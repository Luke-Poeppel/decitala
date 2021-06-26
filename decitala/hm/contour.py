# -*- coding: utf-8 -*-
####################################################################################################
# File:     contour.py
# Purpose:  Pitch contour tools for the birdsong transcriptions.
#
# Author:   Luke Poeppel
#
# Location: Kent, 2021
####################################################################################################
import copy
import numpy as np

from itertools import groupby

from ..utils import roll_window

NEUMES = {
	(1, 0): "Clivis",
	(0, 1): "Podatus",
	(0, 1, 2): "Scandicus",
	(2, 1, 0): "Climacus",
	(0, 1, 0): "Torculus",
	(1, 0, 1): "Porrectus"
}

class ContourException(Exception):
	pass

def strip_monotonic_pitch_content(pitch_content):
	"""
	Given monotonic pitch content output from the decitala search modules (which stores singleton
	pitch content as tuples), strips to individual elements.
	"""
	return [x[0] for x in pitch_content]

def normalize_pitch_content(data, midi_start=60):
	"""
	Normalize pitch content to starting value `midi_start`.
	"""
	diff = data[0] - midi_start
	return np.array([x - diff for x in data])

def uds_contour(data):
	"""
	Stands for "up-down-stay" as a measure of pitch contour. Normalized to start at 0.

	>>> frag = np.array([47, 42, 45, 51, 51, 61, 58])
	>>> uds_contour(frag)
	array([ 0, -1,  1,  1,  0,  1, -1])
	"""
	out = [0]
	i = 1
	while i < len(data):
		prev = data[i - 1]
		curr = data[i]

		if curr > prev:
			out.append(1)
		if curr < prev:
			out.append(-1)
		if curr == prev:
			out.append(0)

		i += 1

	return np.array(out)

def pitch_content_to_contour(pitch_content, as_str=False):
	"""
	This function calculates the pitch contour information from data out of rolling_search.
	This function assumes the data is monophonic.

	:param list pitch_content: pitch content from the output of rolling_search."

	>>> pc = [(80,), (91,), (78,), (85,)]
	>>> pitch_content_to_contour(pc)
	array([1, 3, 0, 2])
	>>> pc2 = [(80,), (84,), (84,)]
	>>> pitch_content_to_contour(pc2)
	array([0, 1, 1])
	"""
	if type(pitch_content[0]) == tuple:
		to_mono = [x[0] for x in pitch_content]
	else:
		to_mono = pitch_content
	seg_vals = copy.copy(to_mono)
	value_dict = dict()

	for i, this_val in zip(range(0, len(sorted(set(seg_vals)))), sorted(set(seg_vals))):
		value_dict[this_val] = str(i)

	for i, this_val in enumerate(seg_vals):
		for this_key in value_dict:
			if this_val == this_key:
				seg_vals[i] = value_dict[this_key]

	if not(as_str):
		return np.array([int(val) for val in seg_vals])
	else:
		return "<" + " ".join([str(int(val)) for val in seg_vals]) + ">"

def contour_to_neume(contour):
	"""
	Function for checking the associated neume for a given contour. Only two and three onset
	contour are supported.

	:param contour: A pitch contour (iterable).
	:return: The associated neume or ``None``.
	:rtype: str or None
	"""
	assert len(contour) <= 3, ContourException("Contour input must be of length three!")
	try:
		return NEUMES[tuple(contour)]
	except KeyError:
		return None

def _has_extremum(window, mode):
	"""
	>>> min_check = ([0, {1, -1}], [2, {-1}], [1, {1, -1}])
	>>> _has_extremum(min_check, "min")
	False
	>>> _has_extremum(min_check, "max")
	True
	"""
	assert len(window) == 3
	middle_val = window[1][0]
	if mode == "max":
		if middle_val >= window[0][0] and middle_val >= window[2][0]:
			return True
		else:
			return False
	elif mode == "min":
		if middle_val <= window[0][0] and middle_val <= window[2][0]:
			return True
		else:
			return False

def _initial_extremas(contour):
	"""
	First iteration, get extrema.

	>>> contour = [0, 4, 3, 2, 5, 5, 1]
	>>> _initial_extremas(contour)
	[[0, {1, -1}], [4, {1}], [3, set()], [2, {-1}], [5, {1}], [5, {1}], [1, {1, -1}]]
	"""
	out = [[contour[0], {-1, 1}]]
	for this_frame in roll_window(contour, 3):
		elem_set = set()
		middle_val = this_frame[1]
		if middle_val >= this_frame[0] and middle_val >= this_frame[2]:
			elem_set.add(1)
		if middle_val <= this_frame[0] and middle_val <= this_frame[2]:
			elem_set.add(-1)

		out.append([middle_val, elem_set])

	out.append([contour[-1], {-1, 1}])

	return out

def _make_level(contour):
	"""
	Runs one iteration of the reduction.

	>>> data = [[1, {1, -1}], [3, {1}], [1, set()], [2, set()], [0, {-1}], [1, set()], [4, {1, -1}]]
	>>> new = _make_level(data)
	>>> new
	[[1, {1, -1}], [3, set()], [1, set()], [2, set()], [0, {-1}], [1, set()], [4, {1, -1}]]
	>>> _make_level(new) == new
	True
	>>> # remove clusters
	>>> initial_extremas = [
	...		[0, {1, -1}],
	... 	[4, {1}],
	... 	[3, set()],
	... 	[2, {-1}],
	... 	[5, {1}],
	... 	[5, {1}],
	... 	[1, {1, -1}]
	...	]
	"""
	fnmax = lambda x: 1 in x[1]
	fnmin = lambda x: -1 in x[1]

	for i, this_window in enumerate(roll_window(contour, 3, fnmax)):
		elem_set = this_window[1][1]
		if len(elem_set) == 0:
			continue
		elif None in this_window:
			continue
		else:
			if _has_extremum(this_window, "max"):
				pass
			else:
				elem_set.remove(1)

	for i, this_window in enumerate(roll_window(contour, 3, fnmin)):
		elem_set = this_window[1][1]
		if len(elem_set) == 0:
			continue
		elif None in this_window:
			continue
		else:
			if _has_extremum(this_window, "min"):
				pass
			else:
				elem_set.remove(-1)

	ranges = []
	for _, this_range in groupby(range(len(contour)), lambda i: (contour[i][0], contour[i][1])):
		ranges.append(list(this_range))
	del_clusters = []

	for this_cluster in ranges:
		if len(this_cluster) > 1:
			del_clusters.extend(this_cluster[1:])

	if len(del_clusters) != 0:
		for index in sorted(del_clusters, reverse=True):
			del contour[index]

	return contour

def contour_to_prime_contour(contour, include_depth=False):
	"""
	Implementation of Morris' 1993 Contour-Reduction algorithm. "The algorithm prunes pitches
	from a contour until it is reduced to a prime." The loop runs until all elements
	are flagged as maxima or minima.

	:param np.array contour: contour input

	>>> contour_a = [0, 1]
	>>> contour_to_prime_contour(contour_a)
	array([0, 1])
	>>> contour_b = [0, 4, 3, 2, 5, 5, 1]
	>>> contour_to_prime_contour(contour_b, include_depth=False)
	array([0, 2, 1])
	>>> contour_c = [1, 3, 1, 2, 0, 1, 4]
	>>> contour_to_prime_contour(contour_c, include_depth=False)
	array([1, 0, 2])
	>>> contour_d = [0, 1, 1]
	>>> contour_to_prime_contour(contour_d, include_depth=False)
	array([0, 1, 1])
	"""
	depth = 0
	if len(contour) <= 2:
		if not(include_depth):
			return pitch_content_to_contour(contour)
		else:
			return (pitch_content_to_contour(contour), depth)

	prime_contour = _initial_extremas(contour)
	if all([len(x[1]) != 0 for x in prime_contour]):
		if not(include_depth):
			return pitch_content_to_contour(contour)
		else:
			return (pitch_content_to_contour(contour), depth)

	still_unflagged_values = True
	while still_unflagged_values is True:
		_make_level(prime_contour)
		depth += 1
		if _make_level(prime_contour[:]) == prime_contour:  # Check next iteration...
			still_unflagged_values = False
		else:
			continue

	prime_contour = [x[0] for x in prime_contour if len(x[1]) != 0]
	depth += 1

	if not(include_depth):
		return pitch_content_to_contour(prime_contour)
	else:
		return (pitch_content_to_contour(prime_contour), depth)