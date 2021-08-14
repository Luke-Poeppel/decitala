####################################################################################################
# File:     contour_utils.py
# Purpose:  Pitch contour utility functions for the birdsong transcriptions.
#
# Author:   Luke Poeppel
#
# Location: NYC, 2021
####################################################################################################
"""
After refactoring the Schultz calculations, there were some circular import issues. This file may
be removed at some point.
"""
import copy

from itertools import groupby

from ..utils import roll_window

def _pitch_contour(pitch_content, as_str=False):
	if type(pitch_content[0]) == tuple:
		to_mono = [x[0] for x in pitch_content]
	else:
		to_mono = pitch_content
	seg_vals = copy.deepcopy(to_mono)
	value_dict = dict()

	for i, this_val in zip(range(0, len(sorted(set(seg_vals)))), sorted(set(seg_vals))):
		value_dict[this_val] = str(i)

	for i, this_val in enumerate(seg_vals):
		for this_key in value_dict:
			if this_val == this_key:
				seg_vals[i] = value_dict[this_key]

	if not(as_str):
		return [int(val) for val in seg_vals]
	else:
		return "<" + " ".join([str(int(val)) for val in seg_vals]) + ">"


####################################################################################################
# Common Reduction Utils
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

def _track_extrema(contour):
	"""
	Gets the initial extrema of a contour. Returns a list in which each element is a list holding a
	contour element and a set which tells you whether that element defines a local maxima, local
	minima, or neither. If the contour element is 1, it is a local maxima; if it is -1, it is a
	local minima; otherwise the set is left empty.

	>>> contour = [0, 4, 3, 2, 5, 5, 1]
	>>> _track_extrema(contour)
	[[0, {1, -1}], [4, {1}], [3, set()], [2, {-1}], [5, {1}], [5, {1}], [1, {1, -1}]]
	>>> contour_2 = [1, 3, 0, 3, 0, 3, 0, 3, 2]
	>>> for x in _track_extrema(contour_2):
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

def _recheck_extrema(contour, mode):
	"""
	Recall that the data are contour elements (integers) and their extrema trackers (a set
	holding -1, 1, or nothing). After a level of reduction, a contour element may or may not
	still be an extrema. This function re-iterates over the windows and updates the
	extrema data.

	If iterating over maxima to check, use ``mode='max'``, otherwise ``mode='min'``.

	>>> post_reduction = [[2, {-1, 1}], [1, {1}], [3, {1}], [2, {-1, 1}]]
	>>> _recheck_extrema(post_reduction, mode="max")
	>>> post_reduction
	[[2, {1, -1}], [1, set()], [3, {1}], [2, {1, -1}]]
	"""
	if mode == "max":
		extrema_elem = 1
		check = lambda x: 1 in x[1]
	else:
		extrema_elem = -1
		check = lambda x: -1 in x[1]

	for i, this_window in enumerate(roll_window(array=contour, window_size=3, fn=check)):
		if any(x is None for x in this_window):
			continue

		if not(_center_of_window_is_extremum(window=this_window, mode=mode)):
			mid_elem_extrema = this_window[1][1]
			if extrema_elem in mid_elem_extrema:
				mid_elem_extrema.remove(extrema_elem)


"""
The following functions are used in both the Morris and Schultz reduction algorithms.
"""
def _window_has_intervening_extrema(window, contour, mode):
	"""
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
	if mode == "max":
		# Only a single extrema found. Trivial case.
		if len([x for x in window if 1 in x[1][1]]) == 1:
			return True
		else:
			check = lambda x: 1 in x[1][1]
	else:
		# Only a single extrema found.
		if len([x for x in window if -1 in x[1][1]]) == 1:
			return True
		check = lambda x: -1 in x[1][1]

	for tiny_window in roll_window(window, window_size=2, fn=check):
		contour_index_range = [tiny_window[0][0], tiny_window[1][0]]
		if (contour_index_range[0] + 1) == contour_index_range[1]:
			# Check if second element in tiny-window contains opposite flag.
			if mode == "max":
				if not(-1 in contour[contour_index_range[1]][1]):
					return False
			if mode == "min":
				if not(1 in contour[contour_index_range[1]][1]):
					return False
		else:
			# -1 + 1 because looking one element before ending, but list indexing so add 1.
			intervening_range = contour[contour_index_range[0] + 1:contour_index_range[-1] - 1 + 1]
			if mode == "max":  # Looking for min.
				if not(any(-1 in x[1] for x in intervening_range)):
					return False
			if mode == "min":  # Looking for max.
				if not(any(1 in x[1] for x in intervening_range)):
					return False
	return True

def _adjacency_and_intervening_checks(contour, mode, algorithm):
	"""
	See Step 6/7 in Morris & Schultz AND Step 8/9 of Schultz.
	"""
	if mode == "max":
		extrema_elem = 1
	else:
		extrema_elem = -1

	# For each cluster of maxima/minima, flag all/one unless:
	# (1) one of the pitches in the string is the first or last element -> flag only the first/last.
	# (2) both the first and last elements are in the string -> flag only the first and last.
	extrema = [(i, x) for (i, x) in enumerate(contour) if extrema_elem in x[1]]
	extrema_grouped = groupby(extrema, lambda x: x[1][0])
	extrema_groups = [list(val) for _, val in extrema_grouped]
	extrema_groups = [x for x in extrema_groups if len(x) > 1]
	for max_grouping in extrema_groups:
		if max_grouping[0][0] == 0 or max_grouping[-1][0] == len(contour) - 1:
			for elem in max_grouping:
				if elem[0] not in {0, len(contour) - 1}:
					grouped_elem = contour[elem[0]]
					grouped_elem[1].remove(extrema_elem)
		else:
			if algorithm == "morris":
				# Flag only 1.
				for elem in max_grouping[1:]:
					elem[1][1].remove(extrema_elem)
			elif algorithm == "schultz":
				# Flag all FOLLOWED BY STEPS 8 and 9.
				if not(_window_has_intervening_extrema(window=max_grouping, contour=contour, mode=mode)):  # noqa
					for elem in max_grouping[1:]:
						elem[1][1].remove(extrema_elem)