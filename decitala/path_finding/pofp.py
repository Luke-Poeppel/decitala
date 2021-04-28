# -*- coding: utf-8 -*-
####################################################################################################
# File:     po_non_overlapping_onsets.py
# Purpose:  M. Raynards technique for solving the non-overlapping onset ranges problem using
#           Pareto optimal frontiers of sequences.
#
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
**NOTE**: M. Raynard helpfully provided a technique for solving the given problem (an iterative
approach to the end-overlapping indices problem) in a StackOverflow post from Summer, 2020. The link
to the original post is:
https://stackoverflow.com/questions/62734114/iterative-solution-to-end-overlapping-indices.

Once we have retrieved :math:`n` talas in a part, we want to check whether or not they align.
If a tala :math:`T_1` ranges from onsets :math:`X_i` to :math:`Y_i` and a tala :math:`T_2` ranges
from onsets :math:`X_j` to :math:`Y_j`, if :math:`X_j < Y_i`, we can't satisfactorily align
:math:`T_1` and :math:`T_2`; this means that one (or both) of these talas was not intentionally
included, and simply exists as a sub-tala or cyclic rotation. Multiple possible alignments exist,
so we calculate them all using an iterative solution to the end-overlapping indices problem using
a Pareto frontier of paths.

The output to the alignment function, :obj:`decitala.pofp.get_pareto_optimal_longest_paths`, may be
exponential in size with respect to the input. As such, we use the observation that there often
exist "break points" in the data collected from rolling search: points at which there exists no
overlap. We divide the data by each of these regions (if they exist) and generate the longest
paths separately.

Several of the functions below have the parameter ``data``. This parameter is of the form returned
by :obj:`~decitala.trees.rolling_search` and corresponds to a list of dictionaries, each holding
information about the fragment, modification, onset-range, and spanning data.
"""
import itertools

def check_break_point(data, i):
	"""
	Helper function for :obj:`~decitala.pofp.get_break_points`. Checks index i of the onset_list that
	all values prior to it are less than or equal to :math:`b_i` and :math:`s_i`. If True, this means
	that the data at index i is >= all previous.

	:param list data: data from :obj:`~decitala.trees.rolling_search`.
	:param int i: index of the data to check.
	:return: whether or not the queried index is a break point.
	:rtype: bool

	>>> data = [
	...		{"fragment": "info1", "mod": ("r", 1.0), "onset_range": (0.0, 2.0)},
	... 	{"fragment": "info2", "mod": ("r", 2.0), "onset_range": (0.0, 4.0)},
	... 	{"fragment": "info3", "mod": ("d", 0.25), "onset_range": (2.0, 4.0)},
	... 	{"fragment": "info4", "mod": ("rd", 0.25), "onset_range": (2.0, 5.75)},
	... 	{"fragment": "info5", "mod": ("r", 3.0), "onset_range": (2.5, 4.5)},
	... 	{"fragment": "info6", "mod": ("r", 1.0), "onset_range": (4.0, 5.5)},
	... 	{"fragment": "info7", "mod": ("rd", 0.25), "onset_range": (6.0, 7.25)}
	... ]
	>>> print(check_break_point(data, 2))
	False
	>>> print(check_break_point(data, 6))
	True
	"""
	check = []
	for this_data in data[0:i]:
		range_data = this_data["onset_range"]
		if data[i]["onset_range"][0] >= range_data[0] and data[i]["onset_range"][0] >= range_data[1]:
			check.append(1)
		else:
			check.append(0)

	if set(check) == {1}:
		return True
	else:
		return False

def get_break_points(data):
	"""
	:param list data: data from :obj:`~decitala.trees.rolling_search`.
	:return: every index in the input at which the data is at most end-overlapping.
	:rtype: list

	>>> data = [
	...		{"fragment": "info1", "mod": ("r", 1.0), "onset_range": (0.0, 2.0)},
	... 	{"fragment": "info2", "mod": ("r", 2.0), "onset_range": (0.0, 4.0)},
	... 	{"fragment": "info3", "mod": ("d", 0.25), "onset_range": (2.0, 4.0)},
	... 	{"fragment": "info4", "mod": ("rd", 0.25), "onset_range": (2.0, 5.75)},
	... 	{"fragment": "info5", "mod": ("r", 3.0), "onset_range": (2.5, 4.5)},
	... 	{"fragment": "info6", "mod": ("r", 1.0), "onset_range": (4.0, 5.5)},
	... 	{"fragment": "info7", "mod": ("rd", 0.25), "onset_range": (6.0, 7.25)}
	... ]
	>>> get_break_points(data)
	[6]
	"""
	i = 0
	break_points = []
	while i < len(data):
		if check_break_point(data, i):
			break_points.append(i)

		i += 1

	return break_points

def partition_data_by_break_points(data):
	"""
	Partitions the input data according to all calculated breakpoints.

	>>> data = [
	...		{"fragment": "info1", "mod": ("r", 1.0), "onset_range": (0.0, 2.0)},
	... 	{"fragment": "info2", "mod": ("r", 2.0), "onset_range": (0.0, 4.0)},
	... 	{"fragment": "info3", "mod": ("d", 0.25), "onset_range": (2.0, 4.0)},
	... 	{"fragment": "info4", "mod": ("rd", 0.25), "onset_range": (2.0, 5.75)},
	... 	{"fragment": "info5", "mod": ("r", 3.0), "onset_range": (2.5, 4.5)},
	... 	{"fragment": "info6", "mod": ("r", 1.0), "onset_range": (4.0, 5.5)},
	... 	{"fragment": "info7", "mod": ("rd", 0.25), "onset_range": (6.0, 7.25)}
	... ]
	>>> for this_partition in partition_data_by_break_points(data):
	...    print(this_partition)
	[{'fragment': 'info1', 'mod': ('r', 1.0), 'onset_range': (0.0, 2.0)}, {'fragment': 'info2', 'mod': ('r', 2.0), 'onset_range': (0.0, 4.0)}, {'fragment': 'info3', 'mod': ('d', 0.25), 'onset_range': (2.0, 4.0)}, {'fragment': 'info4', 'mod': ('rd', 0.25), 'onset_range': (2.0, 5.75)}, {'fragment': 'info5', 'mod': ('r', 3.0), 'onset_range': (2.5, 4.5)}, {'fragment': 'info6', 'mod': ('r', 1.0), 'onset_range': (4.0, 5.5)}] # noqa
	[{'fragment': 'info7', 'mod': ('rd', 0.25), 'onset_range': (6.0, 7.25)}]
	"""
	break_points = get_break_points(data)
	out = [data[i:j] for i, j in zip([0] + break_points, break_points + [None])]

	return out

####################################################################################################
def _min_successor_to_elem(elem, all_min_successors):
	"""
	>>> all_min_successors = [
	...		[{'fragment': 'info1', 'mod': ('r', 1.0), 'onset_range': (0.0, 2.0), 'id': 1}, {'fragment': 'info3', 'mod': ('d', 0.25), 'onset_range': (2.0, 4.0), 'id': 3}], # noqa
	... 	[{'fragment': 'info2', 'mod': ('r', 2.0), 'onset_range': (0.0, 4.0), 'id': 2}, {'fragment': 'info6', 'mod': ('r', 1.0), 'onset_range': (4.0, 5.5), 'id': 6}], # noqa
	... 	[{'fragment': 'info3', 'mod': ('d', 0.25), 'onset_range': (2.0, 4.0), 'id': 3}, {'fragment': 'info6', 'mod': ('r', 1.0), 'onset_range': (4.0, 5.5), 'id': 6}], # noqa
	... 	[{'fragment': 'info4', 'mod': ('rd', 0.25), 'onset_range': (2.0, 5.75), 'id': 4}, {'fragment': 'info7', 'mod': ('rd', 0.25), 'onset_range': (6.0, 7.25), 'id': 7}], # noqa
	... 	[{'fragment': 'info5', 'mod': ('r', 3.0), 'onset_range': (2.5, 4.5), 'id': 5}, {'fragment': 'info7', 'mod': ('rd', 0.25), 'onset_range': (6.0, 7.25), 'id': 7}], # noqa
	... 	[{'fragment': 'info6', 'mod': ('r', 1.0), 'onset_range': (4.0, 5.5), 'id': 6}, {'fragment': 'info7', 'mod': ('rd', 0.25), 'onset_range': (6.0, 7.25), 'id': 7}] # noqa
	... ]
	>>> elem = all_min_successors[2][0]
	>>> elem
	{'fragment': 'info3', 'mod': ('d', 0.25), 'onset_range': (2.0, 4.0), 'id': 3}
	>>> _min_successor_to_elem(elem, all_min_successors)
	{'fragment': 'info6', 'mod': ('r', 1.0), 'onset_range': (4.0, 5.5), 'id': 6}
	"""
	for data in all_min_successors:
		if data[0]["id"] == elem["id"]:
			return data[1]

def get_pareto_optimal_longest_paths(data):
	"""
	>>> data_1 = [
	... 	{"fragment": "info1", "mod": ("r", 1.0), "onset_range": (0.0, 2.0), "id":1},
	... 	{"fragment": "info2", "mod": ("r", 2.0), "onset_range": (0.0, 4.0), "id":2},
	... 	{"fragment": "info3", "mod": ("d", 0.25), "onset_range": (2.0, 4.0), "id":3},
	... 	{"fragment": "info4", "mod": ("rd", 0.25), "onset_range": (2.0, 5.75), "id":4},
	... 	{"fragment": "info5", "mod": ("r", 3.0), "onset_range": (2.5, 4.5), "id":5},
	... 	{"fragment": "info6", "mod": ("r", 1.0), "onset_range": (4.0, 5.5), "id":6},
	... 	{"fragment": "info7", "mod": ("rd", 0.25), "onset_range": (6.0, 7.25), "id":7}
	... ]
	>>> for path in get_pareto_optimal_longest_paths(data_1):
	... 	onset_ranges = [x["onset_range"] for x in path]
	... 	print(onset_ranges)
	[(0.0, 2.0), (2.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
	[(0.0, 2.0), (2.0, 5.75), (6.0, 7.25)]
	[(0.0, 2.0), (2.5, 4.5), (6.0, 7.25)]
	[(0.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
	>>> data_2 = [
	... 	{'fragment': GreekFoot("Spondee"), 'mod': ('r', 0.125), 'onset_range': (0.0, 0.5), 'is_spanned_by_slur': False, 'pitch_content': [(80,), (91,)], "id":1}, # noqa
	... 	{'fragment': GeneralFragment([0.25, 0.25], name="cs-test1"), 'mod': ('cs', 2.0), 'onset_range': (0.0, 0.5), 'is_spanned_by_slur': False, 'pitch_content': [(80,), (91,)], "id":2}, # noqa
	... 	{'fragment': GreekFoot("Trochee"), 'mod': ('r', 0.125), 'onset_range': (0.25, 0.625), 'is_spanned_by_slur': False, 'pitch_content': [(91,), (78,)], "id":3}, # noqa
	... 	{'fragment': GeneralFragment([0.25, 0.125], name="cs-test2"), 'mod': ('cs', 2.0), 'onset_range': (0.25, 0.625), 'is_spanned_by_slur': False, 'pitch_content': [(80,), (91,)], "id":4}, # noqa
	... 	{'fragment': GreekFoot("Dactyl"), 'mod': ('r', 0.125), 'onset_range': (0.5, 1.0), 'is_spanned_by_slur': False, 'pitch_content': [(91,), (78,), (85,)], "id":5} # noqa
	... ]
	>>> for path in get_pareto_optimal_longest_paths(data_2):
	... 	for fragment in path:
	... 		print(fragment)
	... 	print("-----")
	{'fragment': <fragment.GreekFoot Spondee>, 'mod': ('r', 0.125), 'onset_range': (0.0, 0.5), 'is_spanned_by_slur': False, 'pitch_content': [(80,), (91,)], 'id': 1}
	{'fragment': <fragment.GreekFoot Dactyl>, 'mod': ('r', 0.125), 'onset_range': (0.5, 1.0), 'is_spanned_by_slur': False, 'pitch_content': [(91,), (78,), (85,)], 'id': 5}
	-----
	{'fragment': <fragment.GeneralFragment cs-test1: [0.25 0.25]>, 'mod': ('cs', 2.0), 'onset_range': (0.0, 0.5), 'is_spanned_by_slur': False, 'pitch_content': [(80,), (91,)], 'id': 2}
	{'fragment': <fragment.GreekFoot Dactyl>, 'mod': ('r', 0.125), 'onset_range': (0.5, 1.0), 'is_spanned_by_slur': False, 'pitch_content': [(91,), (78,), (85,)], 'id': 5}
	-----
	{'fragment': <fragment.GreekFoot Trochee>, 'mod': ('r', 0.125), 'onset_range': (0.25, 0.625), 'is_spanned_by_slur': False, 'pitch_content': [(91,), (78,)], 'id': 3}
	-----
	{'fragment': <fragment.GeneralFragment cs-test2: [0.25  0.125]>, 'mod': ('cs', 2.0), 'onset_range': (0.25, 0.625), 'is_spanned_by_slur': False, 'pitch_content': [(80,), (91,)], 'id': 4}
	-----
	"""
	sources = [x for x in data if not any(y["onset_range"][1] <= x["onset_range"][0] for y in data)]
	sinks = [x for x in data if not any(x["onset_range"][1] <= y["onset_range"][0] for y in data)]

	all_ids = [x["id"] for x in data]
	sink_ids = [x["id"] for x in sinks]
	remaining = set(all_ids) - set(sink_ids)
	filtered_data = [x for x in data if x["id"] in remaining]

	min_successors = []
	for x in filtered_data:
		candidates = [y for y in data if y["onset_range"][0] >= x["onset_range"][1]] # noqa and y["onset_range"] != x["onset_range"]]  
		min_successor = min(candidates, key=lambda x: x["onset_range"][0])
		min_successors.append([x, min_successor])

	successors = []
	for x in data:
		successor = [y for y in data if x["onset_range"][1] <= y["onset_range"][0] <= y["onset_range"][1] and y["onset_range"][0] < _min_successor_to_elem(x, min_successors)["onset_range"][1]] # noqa
		successors.append([x, successor])

	def print_path_rec(node, path):
		if node in sinks:
			solutions.append([path + [node]])
		else:
			for successor in _min_successor_to_elem(node, successors):
				print_path_rec(successor, path + [node])

	solutions = []
	for source in sources:
		print_path_rec(source, [])

	flatten = lambda l: [item for sublist in l for item in sublist]
	flattened = flatten(solutions)

	return flattened

	# flattened.sort()
	pareto_optimal_paths = list(flattened for flattened, _ in itertools.groupby(flattened))

	stupid_out = []
	for this_path in pareto_optimal_paths:
		new_path = []
		for this_range in this_path:
			for this_data in data:
				if this_range == this_data["onset_range"]:
					new_path.append([this_data, this_range])
					continue
		stupid_out.append(new_path)

	return stupid_out