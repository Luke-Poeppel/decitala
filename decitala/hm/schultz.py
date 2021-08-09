####################################################################################################
# File:     schultz.py
# Purpose:  Tools for Schultz Prime Contour (SPC) calculation.
#
# Author:   Luke Poeppel
#
# Location: NYC, 2021
####################################################################################################
"""
Implementation of Schultz's contour reduction algorithm (final version). See Schultz 2008: 108 in
Spectrum. This was originally in the contour module, but the implementation was complex enough to
warrent its own module...
"""
from itertools import groupby

from .contour_utils import (
	_get_initial_extrema,
	_recheck_extrema,
	_pitch_contour
)
from ..utils import roll_window

class SchultzException(Exception):
	pass

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
			# import pdb; pdb.set_trace()
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

def _schultz_extrema_check(contour):
	"""
	Steps 6-9.
	"""
	# Reiterate over maxima/minima
	# Look at docs in contour_utils if confused! No more than a safety rail.
	# import pdb; pdb.set_trace()
	_recheck_extrema(contour=contour, mode="max")
	_recheck_extrema(contour=contour, mode="min")

	def adjacency_and_intervening_checks(contour, mode):
		if mode == "max":
			extrema_elem = 1
		else:
			extrema_elem = -1

		# Step 6/7. For each cluster of maxima/minima, flag all unless:
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
				for elem in max_grouping:
					grouped_elem = contour[elem[0]]
					grouped_elem[1].add(extrema_elem)

		# import pdb; pdb.set_trace()
		# Step 8/9. Iterate again over maxima/minima. If cluster has no intervening extremum, remove
		# the flag from all but one. (Say 1st).
		for grouping in extrema_groups:
			if not(_window_has_intervening_extrema(grouping, contour=contour, mode=mode)):
				for elem in grouping[1:]:  # Remove flag from all but one.
					elem[1][1].remove(extrema_elem)

	# import pdb; pdb.set_trace()
	adjacency_and_intervening_checks(contour, mode="max")
	adjacency_and_intervening_checks(contour, mode="min")

def _schultz_get_closest_extrema(contour):
	"""
	Part of Step 11.
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
	>>> (c_start, c_end) = _schultz_get_closest_extrema(contour)
	>>> c_start
	('max', (1, [3, {1}]))
	>>> c_end
	('max', (7, [3, {1}]))
	"""
	# Find the closest elements. Unflag (and store) all repetions that are not those from above.
	closest_start_extrema = next((i + 1, x) for (i, x) in enumerate(contour[1:-1]) if 1 in x[1] or -1 in x[1])  # noqa
	closest_end_extrema = next((len(contour) - i - 2, x) for (i, x) in enumerate(contour[1:-1][::-1]) if 1 in x[1] or -1 in x[1])  # noqa

	if -1 in closest_start_extrema[1][1]:
		closest_start_out = ("min", closest_start_extrema)
	else:
		closest_start_out = ("max", closest_start_extrema)

	if -1 in closest_end_extrema[1][1]:
		closest_end_out = ("min", closest_end_extrema)
	else:
		closest_end_out = ("max", closest_end_extrema)

	return (
		closest_start_out,
		closest_end_out,
	)

def _schultz_remove_flag_repetitions_except_closest(contour):
	"""
	Step 11. Check if repetitions; if so, remove all except those closest to the start and end of
	the contour.
	"""
	(
		closest_start_extrema,
		closest_end_extrema,
	) = _schultz_get_closest_extrema(contour)

	# Unflag all repeated maxes/mins that are not closest to first and last.
	unflagged_maxima = []
	unflagged_minima = []
	closest_indices = {closest_start_extrema[1][0], closest_end_extrema[1][0]}
	for i, contour_elem in enumerate(contour):
		if i in closest_indices or i in {0, len(contour) - 1}:
			continue

		if -1 in contour_elem[1]:
			unflagged_minima.append((i, contour_elem))
			contour_elem[1].clear()
		elif 1 in contour_elem[1]:
			unflagged_maxima.append((i, contour_elem))
			contour_elem[1].clear()

	return (contour, closest_start_extrema, closest_end_extrema, unflagged_minima, unflagged_maxima)

def _schultz_reduce(contour, depth):
	"""
	# Steps 11, 12, 13, 14, 15
	"""
	if not(_no_schultz_repetition(contour, allow_unflagged=True)):
		(
			contour,
			closest_start_extrema,
			closest_end_extrema,
			unflagged_minima,
			unflagged_maxima
		) = _schultz_remove_flag_repetitions_except_closest(contour) # noqa

		# Step 12
		# If both are maxes or both are mins, reflag one of the opposite removed values.
		# Not totally sure about the exception (would like to ask contour expert).
		# Basically, what if there are no extrema flags of a certain type to flag/unflag?
		if closest_start_extrema[0] == closest_end_extrema[0]:  # "max" == "max" or "min" == "min"
			if closest_start_extrema[0] == "max":
				try:
					reflag = unflagged_minima[0]
					contour[reflag[0]][1].add(-1)
				except IndexError:
					pass
			else:
				try:
					reflag = unflagged_maxima[0]
					contour[reflag[0]][1].add(1)
				except IndexError:
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
	else:  # Used in steps 11/12.
		# Still only interested in the flagged values, though ;-)
		contour_elems = [x[0] for x in contour if x[1]][1:-1]
		return len(contour_elems) <= len(set(contour_elems)) + 1

def spc(contour):
	depth = 0

	# If the contour is of length <= 2, it is prime by definition.
	if len(contour) <= 2:
		return (_pitch_contour(contour), depth)

	prime_contour = _get_initial_extrema(contour)
	if all(x[1] for x in prime_contour):
		pass  # Proceed directly to Step 6. Morris (1993) stops at this stage.
	else:
		# Steps 4 & 5 (delete unflagged values and increment depth).
		prime_contour = [x for x in prime_contour if x[1]]
		depth += 1

	still_unflagged_values = True
	while still_unflagged_values:
		_schultz_extrema_check(prime_contour)  # Steps 6-9.
		if _no_schultz_repetition(prime_contour, allow_unflagged=False):  # Step 10.
			still_unflagged_values = False
		else:
			# You need to redefine these or it gets stuck.
			prime_contour, depth = _schultz_reduce(prime_contour, depth=depth)  # Steps 11-15.

	# Get the contour elements.
	prime_contour = [x[0] for x in prime_contour]
	return (_pitch_contour(prime_contour), depth)