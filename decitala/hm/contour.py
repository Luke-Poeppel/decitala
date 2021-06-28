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
	assert len(contour) <= 3, ContourException("Contour input must be of length three.")
	try:
		return NEUMES[tuple(contour)]
	except KeyError:
		return None


####################################################################################################
# Contour reduction tools.
"""
Definitions from Schultz (2008):
Definition: Maximum pitch: Given three adjacent pitches in a contour, if the second is higher than
							or equal to the others it is a maximum. A set of maximum pitches is
							called a maxima. **The first and last pitches of a contour are maxima
							by definition**.
Definition: Minimum pitch: Given three adjacent pitches in a contour, if the second is lower than
							or equal to the others it is a minimum. A set of minimum pitches is
							called a minima. **The first and last pitches of a contour are minima
							by definition**.
"""
def _center_of_window_is_extremum(window, mode):
	"""
	>>> _center_of_window_is_extremum(window=[2, 2, 3], mode="min")
	True
	>>> _center_of_window_is_extremum(window=[0, 2, 1], mode="max")
	True
	>>> _center_of_window_is_extremum(window=[1, 2, 3], mode="min")
	False
	>>> _center_of_window_is_extremum(window=[[1, {-1, 1}], [2, {1}], [3, {-1, 1}]], mode="min")
	False
	"""
	assert len(window) == 3

	if all(isinstance(x, list) for x in window):
		window = [x[0] for x in window]

	middle_val = window[1]
	if mode == "max":
		return (middle_val >= window[0]) and (middle_val >= window[2])
	elif mode == "min":
		return (middle_val <= window[0]) and (middle_val <= window[2])

def _get_initial_extrema(contour):
	"""
	Gets the initial extrema of a contour. Returns a list in which each element is a list holding a
	contour element and a set which tells you whether that element defines a local maxima, local
	minima, or neither. If the contour element is 1, it is a local maxima; if it is -1, it is a
	local minima; otherwise the set is left empty.

	>>> contour = [0, 4, 3, 2, 5, 5, 1]
	>>> _get_initial_extrema(contour)
	[[0, {1, -1}], [4, {1}], [3, set()], [2, {-1}], [5, {1}], [5, {1}], [1, {1, -1}]]
	"""
	out = [[contour[0], {-1, 1}]]  # Maxima by definition.
	for this_frame in roll_window(array=contour, window_length=3):
		middle_val = this_frame[1]
		extrema_tracker = set()
		if _center_of_window_is_extremum(window=this_frame, mode="max"):
			extrema_tracker.add(1)
		if _center_of_window_is_extremum(window=this_frame, mode="min"):
			extrema_tracker.add(-1)

		out.append([middle_val, extrema_tracker])

	out.append([contour[-1], {-1, 1}])  # Maxima by definition.
	return out

####################################################################################################
# Implementation of Morris contour reduction algorithm (1993).
def _morris_reduce(contour):
	"""
	Runs one iteration of the Morris contour reduction.

	>>> data = [
	...		[1, {1, -1}],
	... 	[3, {1}],
	... 	[1, set()],
	... 	[2, set()],
	... 	[0, {-1}],
	... 	[1, set()],
	... 	[4, {1, -1}]
	... ]
	>>> morris_reduced = _morris_reduce(data)
	>>> morris_reduced
	[[1, {1, -1}], [3, set()], [1, set()], [2, set()], [0, {-1}], [1, set()], [4, {1, -1}]]
	>>> _morris_reduce(morris_reduced) == morris_reduced
	True
	"""
	max_check = lambda x: 1 in x[1]
	min_check = lambda x: -1 in x[1]

	# Iterate over maxima.
	for i, this_window in enumerate(roll_window(array=contour, window_length=3, fn=max_check)):
		extrema_tracker = this_window[1][1]
		if not(extrema_tracker):
			continue
		elif None in this_window:
			continue
		else:
			# After level of reduction, the extrema might say it's a maxima, but it isn't anymore!
			# So if it's no longer an extrema, remove it.
			if _center_of_window_is_extremum(window=this_window, mode="max"):
				pass
			else:
				extrema_tracker.remove(1)

	# Iterate over minima.
	for i, this_window in enumerate(roll_window(array=contour, window_length=3, fn=min_check)):
		extrema_tracker = this_window[1][1]
		if not(extrema_tracker):
			continue
		elif None in this_window:
			continue
		else:
			# After level of reduction, the extrema might say it's a minima, but it isn't anymore!
			# So if it's no longer an extrema, remove it.
			if _center_of_window_is_extremum(window=this_window, mode="min"):
				pass
			else:
				extrema_tracker.remove(-1)

	cluster_ranges = []
	index_range_of_contour = range(len(contour))
	# Group by both the element and the stored extrema (now correct, after the above check).
	grouped = groupby(index_range_of_contour, lambda i: (contour[i][0], contour[i][1]))
	for _, index_range in grouped:
		cluster_ranges.append(list(index_range))

	for this_cluster in sorted(cluster_ranges):
		if len(this_cluster) > 1:
			# The del_range keeps the first item in the cluster (deleting only the repeated elem).
			# (Option 1 in Schultz: flag only one of them)
			del_range = this_cluster[1:]
			for index in del_range:
				del contour[index]

	return contour

def contour_to_prime_contour(contour, include_depth=False):
	"""
	Implementation of Morris' 1993 Contour-Reduction algorithm. "The algorithm prunes pitches
	from a contour until it is reduced to a prime." The loop runs until all elements
	are flagged as maxima or minima.

	**Assumes the input array is a proper contour, i.e. all elements in range 0-n.**
	**NOTE: Recalculating the contour at the return is not a mistake! Once reduced, the values
			don't match a standard, sequential contour anymore.**

	:param np.array contour: contour input

	>>> contour_a = [0, 1]
	>>> contour_to_prime_contour(contour_a)
	array([0, 1])
	>>> contour_b = [0, 4, 3, 2, 5, 5, 1]
	>>> contour_to_prime_contour(contour_b, include_depth=False)
	array([0, 2, 1])
	"""
	depth = 0

	# If the segment is of length <= 2, it is prime by definition.
	if len(contour) <= 2:
		if not(include_depth):
			return pitch_content_to_contour(contour)
		else:
			return (pitch_content_to_contour(contour), depth)

	# If all the values are extremas, it is already prime.
	prime_contour = _get_initial_extrema(contour)
	initial_flags = [x[1] for x in prime_contour]
	if all(x for x in initial_flags):
		if not(include_depth):
			return pitch_content_to_contour(contour)
		else:
			return (pitch_content_to_contour(contour), depth)

	still_unflagged_values = True
	while still_unflagged_values:
		_morris_reduce(prime_contour)
		depth += 1
		# Check if next iteration is identical.
		contour_copy = copy.deepcopy(prime_contour)
		if _morris_reduce(contour_copy) == prime_contour:
			still_unflagged_values = False

	# Remove elements that are unflagged.
	prime_contour = [x[0] for x in prime_contour if x[1]]
	depth += 1

	if not(include_depth):
		return pitch_content_to_contour(prime_contour)
	else:
		return (pitch_content_to_contour(prime_contour), depth)

####################################################################################################
# Implementation of Schultz contour reduction algorithm (2008). Final version (see p. 108).
def _schultz_reduce(contour):
	pass

def _no_schultz_repetition(contour):
	"""
	Step 10. If all values are flagged and no more than one repetition of values exists, excluding
	the first and last values, returns True.

	>>> contour_with_extrema = [
	... 	[1, {-1, 1}],
	... 	[0, {-1}],
	... 	[2, {1}],
	... 	[0, {-1}],
	... 	[2, {1}],
	... 	[1, {-1, 1}]
	... ]
	>>> _no_schultz_repetition(contour=contour_with_extrema)
	False
	"""
	if all(x[1] for x in contour):
		contour_elems = [x[0] for x in contour][1:-1]  # Exclude first and last.
		return len(contour_elems) == len(set(contour_elems))

def contour_to_schultz_prime_contour(contour, include_depth=False):
	"""
	Implementation of Schultz's (2008) modification of Morris' contour-reduction algorithm.
	"""
	depth = 0

	# If the segment is of length <= 2, it is prime by definition.
	if len(contour) <= 2:
		if not(include_depth):
			return pitch_content_to_contour(contour)
		else:
			return (pitch_content_to_contour(contour), depth)

	prime_contour = _get_initial_extrema(contour)
	initial_flags = [x[1] for x in prime_contour]

	if all(x for x in initial_flags):
		pass  # Proceed directly to Step 6.
	else:
		# Steps 4 & 5 (delete unflagged values and increment).
		prime_contour = [x for x in prime_contour if x[1]]
		depth += 1

	still_unflagged_values = True
	while still_unflagged_values:
		_schultz_reduce(prime_contour)
		if depth != 0:
			depth += 1
		else:
			depth += 2
		# Check Step 10.
		if all(x[1] for x in prime_contour) and _no_schultz_repetition(prime_contour):
			still_unflagged_values = False
		else:
			still_unflagged_values = False

	# Remove elements that are unflagged.
	prime_contour = [x[0] for x in prime_contour if x[1]]
	depth += 1

	if not(include_depth):
		return pitch_content_to_contour(prime_contour)
	else:
		return (pitch_content_to_contour(prime_contour), depth)