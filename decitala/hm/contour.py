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
import random

from collections import Counter
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

# Morris's Prime Contour Classes (1993, 220-221)
# "Linear Prime Classes" (Schultz 92)
# NOTE: Schultz uses the same linear prime classes to refer to symmetries
# of these classes: e.g. <0 2 1> and <1 0 2> = L.
PRIME_CONTOUR_CLASSES = {
	(0,): "A",
	(0, 0): "B",
	(0, 1): "D",
	(0, 1, 0): "G",
	(0, 2, 1): "L",
	(1, 0, 2, 1): "P",
	(1, 0, 3, 2): "X",
	(1, 3, 0, 2): "Y"
}

class ContourException(Exception):
	pass

def strip_monotonic_pitch_content(pitch_content):
	"""
	The pitch content extracted in the :obj:`decitala.search` module consists of lists of tuples.
	This functions strips monotonic pitch content to a single list. If non-monotonic pitch content
	is provided, the function chooses the lowest pitch.

	:param list pitch_content: pitch content of the format returned in
							:obj:`decitala.search.rolling_hash_search`.
	:return: a list of MIDI tones.
	:rtype: list

	>>> pitch_content = [(60,), (61,), (65,)]
	>>> strip_monotonic_pitch_content(pitch_content)
	[60, 61, 65]
	"""
	return [x[0] for x in pitch_content]

def normalize_pitch_content(data, midi_start=60):
	"""
	Normalizes a list of MIDI tones to a a starting value.

	:param list data: a list of MIDI tones.
	:param int midi_start: the MIDI starting point to which the data are normalized.
	:return: a numpy array of the pitch content, normalized to the starting value.
	:rtype: numpy.array

	>>> normalize_pitch_content(data=[58, 60, 62], midi_start=60)
	array([60, 62, 64])
	"""
	diff = data[0] - midi_start
	return np.array([x - diff for x in data])

def uds_contour(data):
	"""
	Returns the for "up-down-stay" contour (UDS) of a given list of MIDI tones. Normalized
	to start at 0.

	:param list data: a list of MIDI tones.
	:return: a numpy array of the UDS contour of the given data.
	:rtype: numpy.array

	>>> midis = [47, 42, 45, 51, 51, 61, 58]
	>>> uds_contour(midis)
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

def pitch_contour(pitch_content, as_str=False):
	"""
	This function returns the contour of given pitch content. It accepts either a list of MIDI
	tones, or the data returned in the :obj:`decitala.search` module. Like
	:obj:`decitala.hm.contour.strip_monotonic_pitch_content`, if non-monotonic pitch content is
	provided, it chooses the lowest pitch.

	:param list pitch_content: pitch content from the output of rolling_search."
	:param bool as_str: whether to return the pitch content as a string (standard format),
						like ``"<0 1 1>"``.
	:return: the contour of the given ``pitch_content``.
	:rtype: numpy.array or str

	>>> pitch_content_1 = [(80,), (91,), (78,), (85,)]
	>>> pitch_contour(pitch_content_1)
	array([1, 3, 0, 2])
	>>> pitch_content_2 = [80, 84, 84]
	>>> pitch_contour(pitch_content_2, as_str=True)
	'<0 1 1>'
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
	Oversimplified function for checking the associated neume of a given pitch contour. Only two and
	three onset contours are supported.

	:param contour: A pitch contour (iterable).
	:return: The associated neume or ``None``.
	:rtype: str or None

	>>> contour = [1, 0, 1]
	>>> contour_to_neume(contour)
	'Porrectus'
	"""
	assert len(contour) <= 3, ContourException("Contour input must be of length three.")
	try:
		return NEUMES[tuple(contour)]
	except KeyError:
		raise ContourException(f"The contour {contour} was not found in the given current set.")

def contour_to_contour_class(
		contour,
		allow_symmetries=False
	):
	"""
	Returns the associated pitch contour class (a letter) from Morris (1993, 220-221)
	of a contour.

	:param contour: a pitch contour (iterable).
	:param bool allow_symmetries: whether to allow permutations of the given contour to be found.
									Default is ``False``. Note that ``X`` and ``Y`` are weird cases
									for this symmetry. May currently fail (don't understand it).
	:rtype: str

	>>> contour_to_contour_class((1, 0, 3, 2))
	'X'
	>>> contour_to_contour_class((0, 1, 0), allow_symmetries=False)
	'G'
	>>> contour_to_contour_class((0, 0, 1), allow_symmetries=True)
	'G'
	"""
	try:
		if not(allow_symmetries):
			return PRIME_CONTOUR_CLASSES[contour]
		elif contour in {(1, 0, 3, 2), (1, 3, 0, 2)}:  # IDK about this case.
			return PRIME_CONTOUR_CLASSES[contour]
		else:
			match = None
			for key in PRIME_CONTOUR_CLASSES.keys():
				if len(key) == len(contour) and len(set(key)) == len(set(contour)):
					match = PRIME_CONTOUR_CLASSES[key]
					break
			return match
	except KeyError:
		ContourException(f"The contour {contour} is not prime.")


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
	>>> contour_2 = [1, 3, 0, 3, 0, 3, 0, 3, 2]
	>>> for x in _get_initial_extrema(contour_2):
	... 	print(x)
	[1, {1, -1}]
	[3, {1}]
	[0, {-1}]
	[3, {1}]
	[0, {-1}]
	[3, {1}]
	[0, {-1}]
	[3, {1}]
	[2, {1, -1}]
	"""
	out = [[contour[0], {-1, 1}]]  # Maxima by definition.
	for this_frame in roll_window(array=contour, window_size=3):
		middle_val = this_frame[1]
		extrema_tracker = set()
		if _center_of_window_is_extremum(window=this_frame, mode="max"):
			extrema_tracker.add(1)
		if _center_of_window_is_extremum(window=this_frame, mode="min"):
			extrema_tracker.add(-1)

		out.append([middle_val, extrema_tracker])

	out.append([contour[-1], {-1, 1}])  # Maxima by definition.
	return out

def _track_extrema(contour, mode):
	if mode == "max":
		check = lambda x: 1 in x[1]
	else:
		check = lambda x: -1 in x[1]

	for i, this_window in enumerate(roll_window(array=contour, window_size=3, fn=check)):
		extrema_tracker = this_window[1][1]
		if not(extrema_tracker):
			continue
		elif None in this_window:
			continue
		else:
			# After level of reduction, the extrema might *say* it's an extrema, but it isn't anymore!
			# So if it's no longer an extrema, remove it.
			if _center_of_window_is_extremum(window=this_window, mode=mode):
				pass
			else:
				if mode == "max":
					extrema_tracker.remove(1)
				else:
					extrema_tracker.remove(-1)

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
	# Reiterate over maxima.
	_track_extrema(contour=contour, mode="max")
	# Reiterate over minima
	_track_extrema(contour=contour, mode="min")

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

def contour_to_prime_contour(contour):
	"""
	Implementation of Robert Morris' Contour-Reduction algorithm (Morris, 1993). "The algorithm prunes
	pitches from a contour until it is reduced to a prime." (Schultz)

	:param contour: A pitch contour (iterable).
	:return: the prime contour of the given pitch contour, along with the depth of the reduction.
	:rtype: tuple

	>>> contour_a = [0, 1]
	>>> contour_to_prime_contour(contour_a)
	(array([0, 1]), 0)
	>>> contour_b = [0, 4, 3, 2, 5, 5, 1]
	>>> contour_to_prime_contour(contour_b)[0]
	array([0, 2, 1])
	"""
	depth = 0

	# If the segment is of length <= 2, it is prime by definition.
	if len(contour) <= 2:
		return (pitch_contour(contour), depth)

	# If all the values are extremas, it is already prime.
	prime_contour = _get_initial_extrema(contour)
	initial_flags = [x[1] for x in prime_contour]
	if all(x for x in initial_flags):
		return (pitch_contour(contour), depth)

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

	return (pitch_contour(prime_contour), depth)

####################################################################################################
# Implementation of Schultz contour reduction algorithm (2008). Final version (see p. 108).
def _window_has_intervening_extrema(window, contour, mode):
	"""
	NOTE: Still a component missing: unflag all but one if repetition found...

	Steps 8/9. If there exists a sequence of equal maxima or minima, check if the sequence
	contains an intervening opposite extrema, i.e. if a sequence of two equal maxima contains
	a minima between them.

	>>> maxima_group = [
	... 	(2, [2, {1}]),
	... 	(4, [2, {1}])
	... ]
	>>> contour = [[1, {1, -1}], [0, {-1}], [2, {1}], [0, {-1}], [2, {1}], [1, {1, -1}]]
	>>> _window_has_intervening_extrema(maxima_group, contour=contour, mode="max")
	True
	"""
	for tiny_window in roll_window(window, window_size=2):
		contour_index_range = [tiny_window[0][0], tiny_window[1][0]]
		if contour_index_range[1] == (contour_index_range[0] + 1):
			return False  # Impossible for there to be an intervening interval.
		else:
			# NOTE: I think this is wrong... Could randomly choose an element that just isn't an extrema...
			# Check if there exists a maxima/minima (opposite) between the extrema. Should be if any(...)
			intervening_index = random.randint(contour_index_range[0] + 1, contour_index_range[1] - 1)
			if mode == "max":  # Looking for min.
				if -1 in contour[intervening_index][1]:
					continue
				else:
					return False
			if mode == "min":  # Looking for max.
				if 1 in contour[intervening_index][1]:
					continue
				else:
					return False
	return True

def _schultz_extrema_check(contour):
	"""
	Steps 6-9.
	"""
	# Reiterate over maxima.
	_track_extrema(contour=contour, mode="max")
	# Reiterate over minima
	_track_extrema(contour=contour, mode="min")

	# Get clusters of maxima and minima.
	maxima = [(i, x) for (i, x) in enumerate(contour) if 1 in x[1]]
	minima = [(i, x) for (i, x) in enumerate(contour) if -1 in x[1]]

	maxima_grouped = groupby(maxima, lambda x: x[1][0])
	maxima_indices = []
	for _, index in maxima_grouped:
		maxima_indices.append(list(index))
	maxima_indices = list(filter(lambda x: len(x) > 1, maxima_indices))

	minima_grouped = groupby(minima, lambda x: x[1][0])
	minima_indices = []
	for _, index in minima_grouped:
		minima_indices.append(list(index))
	minima_indices = list(filter(lambda x: len(x) > 1, minima_indices))

	# Step 6/7 "unless": check if any of the clusters start or end with the actual contour elems.
	# in those cases, remove flags from all except those starts or ends.
	for max_grouping in maxima_indices:
		# Check if both first; if so, continues to next iteration.
		if max_grouping[0][0] == 0 and max_grouping[-1][0] == len(contour):
			for elem in max_grouping:
				grouped_elem = contour[elem[0]]
				if elem[0] != 0 and elem[0] != len(contour) - 1:
					grouped_elem[1].remove(1)
			continue
		elif max_grouping[0][0] == 0:
			for elem in max_grouping:
				grouped_elem = contour[elem[0]]
				if elem[0] != 0:
					grouped_elem[1].remove(1)
		elif max_grouping[-1][0] == len(contour) - 1:  # 0-indexed.
			for elem in max_grouping:
				grouped_elem = contour[elem[0]]
				if elem[0] != len(contour) - 1:
					grouped_elem[1].remove(1)

	for min_grouping in minima_indices:
		# Check if both first; if so, continues to next iteration.
		if min_grouping[0][0] == 0 and min_grouping[-1][0] == len(contour):
			for elem in min_grouping:
				grouped_elem = contour[elem[0]]
				if elem[0] != 0 and elem[0] != len(contour) - 1:
					grouped_elem[1].remove(-1)
			continue
		elif min_grouping[0][0] == 0:
			for elem in min_grouping:
				grouped_elem = contour[elem[0]]
				if elem[0] != 0:
					grouped_elem[1].remove(-1)
		elif min_grouping[-1][0] == len(contour) - 1:  # 0-indexed.
			for elem in min_grouping:
				grouped_elem = contour[elem[0]]
				if elem[0] != len(contour) - 1:
					grouped_elem[1].remove(-1)

	# Filter again...
	maxima_indices = list(filter(lambda x: len(x) > 1, maxima_indices))
	minima_indices = list(filter(lambda x: len(x) > 1, minima_indices))

	# Step 8 and 9: find strings of equal and adjacent extrema; delete all but one of them.
	# UNLESS: they have an intervening extrema, i.e. between any two.
	# Group by both the element and the stored extrema (now correct, after the above check).
	for max_grouping in maxima_indices:
		if not(_window_has_intervening_extrema(max_grouping, contour=contour, mode="max")):
			for elem in max_grouping[1:]:  # Remove flag from all but one.
				# Unsure about this try-except...
				try:
					elem[1][1].remove(1)
				except KeyError:
					continue

	for min_grouping in minima_indices:
		if not(_window_has_intervening_extrema(min_grouping, contour=contour, mode="min")):
			for elem in min_grouping[1:]:  # Remove flag from all but one.
				# Unsure about this try-except...
				try:
					elem[1][1].remove(-1)
				except KeyError:
					continue

	# I don't love this, but it does ensure the start and end are flagged as maxima and minima...
	contour[0][1].update({-1, 1})
	contour[-1][1].update({-1, 1})

def _schultz_get_closest_extrema(
		contour,
		maxima,
		minima
	):
	"""
	Returns the closest repeating extrema to the start and end of the contour.

	From Ex15B:
	>>> contour = [
	...		[1, {1, -1}],
	... 	[3, {1}],
	... 	[0, {-1}],
	... 	[3, {1}],
	... 	[0, {-1}],
	... 	[3, {1}],
	... 	[0, {-1}],
	... 	[3, {1}],
	... 	[2, {1, -1}]
	... ]
	>>> maxima = [(1, [3, {1}]), (3, [3, {1}]), (5, [3, {1}]), (7, [3, {1}])]
	>>> minima = [(2, [0, {-1}]), (4, [0, {-1}]), (6, [0, {-1}])]
	>>> (c_start, c_end, rep_max, rep_min) = _schultz_get_closest_extrema(
	... 	contour,
	... 	maxima,
	... 	minima
	... )
	>>> c_start
	('max', (1, [3, {1}]))
	>>> c_end
	('max', (7, [3, {1}]))
	"""
	# For minima/maxima that repeat themselves, stores the closest to start and end.
	maxima_contour_elems = Counter([x[1][0] for x in maxima])
	repeated_max_keys = set([key for key, val in maxima_contour_elems.items()])

	minima_contour_elems = Counter([x[1][0] for x in minima])
	repeated_min_keys = set([key for key, val in minima_contour_elems.items()])

	closest_max_start = None  # Correct by Ex. 15A
	closest_max_start_distance = 100
	closest_max_end = None  # Correct by Ex. 15A
	closest_max_end_distance = 100

	closest_min_start = None  # Correct by Ex. 15A
	closest_min_start_distance = 100
	closest_min_end = None  # Correct by Ex. 15A
	closest_min_end_distance = 100

	for repeated_max_key in repeated_max_keys:
		# Already sorted, so we just look at [0] and [-1].
		relevant_maxima = [x for x in maxima if x[1][0] == repeated_max_key]
		start_dist = len(contour) - relevant_maxima[0][0]
		end_dist = len(contour) - relevant_maxima[-1][0]
		if start_dist < closest_max_start_distance:
			closest_max_start_distance = start_dist
			closest_max_start = relevant_maxima[0]
		if end_dist < closest_max_end_distance:
			closest_max_end_distance = end_dist
			closest_max_end = relevant_maxima[-1]

	for repeated_min_key in repeated_min_keys:
		# Already sorted, so we just look at [0] and [-1].
		relevant_minima = [x for x in minima if x[1][0] == repeated_min_key]
		start_dist = len(contour) - relevant_minima[0][0]
		end_dist = len(contour) - relevant_minima[-1][0]
		if start_dist < closest_min_start_distance:
			closest_min_start_distance = start_dist
			closest_min_start = relevant_minima[0]
		if end_dist < closest_min_end_distance:
			closest_min_end_distance = end_dist
			closest_min_end = relevant_minima[-1]

	# The starts and ends shouldn't be touched!
	assert contour[0][1] == {1, -1}, ContourException("Something is wrong (start flags).")
	assert contour[-1][1] == {1, -1}, ContourException("Something is wrong (end flags).")

	# This list holds the closts repeating min and max to the start (in that order).
	# Also tracks whether the chosen element is a minima or maxima.
	start_elems = [("min", closest_min_start), ("max", closest_max_start)] # noqa
	# This list holds the closts repeating min and max to the end (in that order).
	end_elems = [("min", closest_min_end), ("max", closest_max_end)] # noqa

	if any(x is None for x in [closest_min_start, closest_max_start, closest_min_end, closest_max_end]): # noqa
		raise ContourException("Something is wrong.")

	closest_start_extrema = min(start_elems, key=lambda x: x[1][0])  # noqa Correct by Ex. 15A
	closest_end_extrema = max(end_elems, key=lambda x: x[1][0])  # noqa Correct by Ex. 15A

	return (
		closest_start_extrema,
		closest_end_extrema,
		repeated_max_keys,
		repeated_min_keys
	)

def _schultz_remove_flag_repetitions_except_closest(contour):
	"""
	Step 11. Check if repetitions; if so, remove all except those closest to the start and end of
	the contour.

	From Ex15B:
	>>> contour = [
	...		[1, {1, -1}],
	... 	[3, {1}],
	... 	[0, {-1}],
	... 	[3, {1}],
	... 	[0, {-1}],
	... 	[3, {1}],
	... 	[0, {-1}],
	... 	[3, {1}],
	... 	[2, {1, -1}]
	... ]
	>>> for x in _schultz_remove_flag_repetitions_except_closest(contour)[0]:
	... 	print(x)
	[1, {1, -1}]
	[3, {1}]
	[0, set()]
	[3, set()]
	[0, set()]
	[3, set()]
	[0, set()]
	[3, {1}]
	[2, {1, -1}]
	"""
	# These exclude the first and last (by design).
	maxima = [(i, x) for (i, x) in enumerate(contour) if 1 in x[1]][1:-1]
	minima = [(i, x) for (i, x) in enumerate(contour) if -1 in x[1]][1:-1]
	(
		closest_start_extrema,
		closest_end_extrema,
		repeated_max_keys,
		repeated_min_keys
	) = _schultz_get_closest_extrema(contour, maxima, minima)

	# Unflag all repeated maxes/mins that are not closest to first and last.
	unflagged_maxima = []
	unflagged_minima = []
	for i, contour_elem in enumerate(contour):
		# Really weird bug, won't accept contour_elem[0] in (repeated_max_keys or repeated_min_keys)...
		if (contour_elem[0] in repeated_max_keys) or (contour_elem[0] in repeated_min_keys):
			# Make sure we're not unflagging the closest flagged extrema.
			# Unflag everything except the closest stuff.
			if i not in {closest_start_extrema[1][0], closest_end_extrema[1][0]}:
				if contour_elem[0] in repeated_max_keys:
					try:  # It may be empty already.
						contour_elem[1].remove(1)
						unflagged_maxima.append((i, contour_elem))
					except KeyError:
						continue
				elif contour_elem[0] in repeated_min_keys:
					try:
						contour_elem[1].remove(-1)
						unflagged_minima.append((i, contour_elem))
					except KeyError:
						continue
			else:
				continue

	return (contour, closest_start_extrema, closest_end_extrema, unflagged_minima, unflagged_maxima)

def _schultz_reduce(contour, depth):
	"""
	# Steps 11, 12, 13, 14, 15
	"""
	# Step 11
	if _no_schultz_repetition(contour, allow_unflagged=True) is False:
		(
			contour,
			closest_start_extrema,
			closest_end_extrema,
			unflagged_minima,
			unflagged_maxima
		) = _schultz_remove_flag_repetitions_except_closest(contour) # noqa

		# Step 12
		# If both are maxes or both are mins, reflag one of the opposite removed values.
		if closest_start_extrema[0] == closest_end_extrema[0]:
			if closest_start_extrema[0] == "max":
				# re-add single flag to minlist.
				try:
					reflag = random.choice(unflagged_minima)
					contour[reflag[0]][1].add(-1)
				except IndexError:  # No minima were removed. Not totally sure this is right.
					pass
			else:
				try:
					reflag = random.choice(unflagged_maxima)
					contour[reflag[0]][1].add(1)
				except IndexError:  # No minima were removed. Not totally sure this is right.
					pass

	# Steps 13-15
	contour = [x for x in contour if x[1]]
	if depth:
		depth += 1
	else:
		depth += 2

	return contour, depth

def _no_schultz_repetition(contour, allow_unflagged=False):
	"""
	Step 10. If all values are flagged and no more than one repetition of values exists, excluding
	the first and last values, returns True.
	Step 11 first checks if this repetition exists, but it doesn't care about unflagged values flags.

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
	if not(allow_unflagged):  # Step 10
		if all(x[1] for x in contour):
			contour_elems = [x[0] for x in contour][1:-1]  # Exclude first and last.
			return len(contour_elems) <= len(set(contour_elems)) + 1  # Only allow for one repetition.
		else:
			return False
	else:
		# Only interested in the flagged values, of course ;-)
		contour_elems = [x[0] for x in contour if x[1]][1:-1]
		return len(contour_elems) <= len(set(contour_elems)) + 1

def contour_to_schultz_prime_contour(contour):
	"""
	Implementation of Schultz's (2008) modification of Morris' contour-reduction algorithm. Catered
	to further prune "unnecessary" repetitions of contour elements.

	:param contour: A pitch contour (iterable).
	:return: the Schultz prime contour of the given pitch contour, along with the depth of the
			reduction.
	:rtype: tuple

	>>> alouette_5 = [2, 5, 3, 1, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	>>> contour_to_schultz_prime_contour(alouette_5)
	(array([1, 2, 0]), 3)
	"""
	depth = 0

	# If the segment is of length <= 2, it is prime by definition.
	if len(contour) <= 2:
		return (pitch_contour(contour), depth)

	prime_contour = _get_initial_extrema(contour)

	if all(x[1] for x in prime_contour):
		pass  # Proceed directly to Step 6.
	else:
		# Steps 4 & 5 (delete unflagged values and increment).
		prime_contour = [x for x in prime_contour if x[1]]
		depth += 1

	still_unflagged_values = True
	while still_unflagged_values:
		_schultz_extrema_check(prime_contour)  # Steps 6-9.
		if _no_schultz_repetition(prime_contour, allow_unflagged=False):  # Step 10.
			still_unflagged_values = False
		else:
			prime_contour, depth = _schultz_reduce(prime_contour, depth=depth)  # Steps 11-15.

	# Get the contour elements.
	prime_contour = [x[0] for x in prime_contour]
	return (pitch_contour(prime_contour), depth)