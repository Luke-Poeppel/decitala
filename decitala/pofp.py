# -*- coding: utf-8 -*-
####################################################################################################
# File:     po_non_overlapping_onsets.py
# Purpose:  M. Raynards technique for solving the non-overlapping onset ranges problem using 
#           Pareto optimal frontiers of sequences.
# 
# Author:   Luke Poeppel, M. Raynard.
#
# Location: Kent, CT 2020
####################################################################################################
"""
**NOTE**: M. Raynard helpfully provided a technique for solving the given problem (an iterative approach
to the end-overlapping indices problem) in a StackOverflow post from Summer, 2020. The link to the 
original post is: https://stackoverflow.com/questions/62734114/iterative-solution-to-end-overlapping-indices.

Once we have retrieved :math:`n` talas in a part, we want to check whether or not they align. 
If a tala :math:`T_1` ranges from onsets :math:`X_i` to :math:`Y_i` and a tala :math:`T_2` ranges from 
onsets :math:`X_j` to :math:`Y_j`, if :math:`X_j < Y_i`, we can't satisfactorily align :math:`T_1` and
:math:`T_2`; this means that one (or both) of these talas was not intentionally included, and simply 
exists as a sub-tala or cyclic rotation. Multiple possible alignments exist, so we calculate them all
using an iterative solution to the end-overlapping indices problem using a Pareto frontier of paths. 

The output to the alignment function, :obj:`decitala.pofp.get_pareto_optimal_longest_paths`, may be exponential 
in size with respect to the input. As such, we use the observation that there often exist "break points" in the
data collected from rolling search: points at which there exists no overlap. We divide the data by each of 
these regions (if they exist) and generate the longest paths separately. 

Several of the functions below have the parameter ``data``. This parameter is of the form returned 
by :obj:`~decitala.trees.rolling_search` and corresponds to a list of dictionaries, each holding information
about the fragment, modification, onset-range, and spanning data. 
"""
import copy
import itertools
import pytest

import logging
logging.basicConfig(level=logging.INFO)

def check_break_point(data, i):
	"""
	Helper function for :obj:`~decitala.pofp.get_break_points`. Checks index i of the onset_list that all values 
	prior to it are less than or equal to :math:`b_i` and :math:`s_i`. If True, this means that 
	the data at index i is >= all previous.

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
	[{'fragment': 'info1', 'mod': ('r', 1.0), 'onset_range': (0.0, 2.0)}, {'fragment': 'info2', 'mod': ('r', 2.0), 'onset_range': (0.0, 4.0)}, {'fragment': 'info3', 'mod': ('d', 0.25), 'onset_range': (2.0, 4.0)}, {'fragment': 'info4', 'mod': ('rd', 0.25), 'onset_range': (2.0, 5.75)}, {'fragment': 'info5', 'mod': ('r', 3.0), 'onset_range': (2.5, 4.5)}, {'fragment': 'info6', 'mod': ('r', 1.0), 'onset_range': (4.0, 5.5)}]
	[{'fragment': 'info7', 'mod': ('rd', 0.25), 'onset_range': (6.0, 7.25)}]
	"""
	break_points = get_break_points(data)
	out = [data[i:j] for i, j in zip([0] + break_points, break_points + [None])]

	return out

####################################################################################################
def get_pareto_optimal_longest_paths(data, verbose=False):
	"""
	Algorithm courtesy of M. Raynard. 

	:param list data: data from :obj:`~decitala.trees.rolling_search`.
	:return: list of lists, each holding a pareto-optimal longest path constructed from the data.
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
	>>> # With only 7 windows, we can extract four possible paths!
	>>> for this_path in get_pareto_optimal_longest_paths(data):
	...    path = [x[1] for x in this_path]
	...    print(path)
	[(0.0, 2.0), (2.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
	[(0.0, 2.0), (2.0, 5.75), (6.0, 7.25)]
	[(0.0, 2.0), (2.5, 4.5), (6.0, 7.25)]
	[(0.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
	"""
	tup_lst = [x["onset_range"] for x in data]
	sources = {
		(a, b)
		for (a, b) in tup_lst
		if not any(d <= a for (c, d) in tup_lst)
	} 

	sinks = {
		(a, b)
		for (a, b) in tup_lst
		if not any(b <= c for (c, d) in tup_lst)
	}

	min_successor = {
		(a, b): min(d for c, d in tup_lst if c >= b)
		for (a, b) in set(tup_lst) - sinks
	}

	successors = {
		(a, b): [
			(c, d)
			for (c, d) in tup_lst
			if b <= c <= d and c < min_successor[(a, b)]
		] for (a, b) in tup_lst
	}

	solutions = []
	def print_path_rec(node, path):
		if node in sinks:
			solutions.append([path + [node]])
		else:
			for successor in successors[node]:
				print_path_rec(successor, path + [node])

	for source in sources:
		print_path_rec(source, [])

	flatten = lambda l: [item for sublist in l for item in sublist]
	flattened = flatten(solutions)

	flattened.sort()
	pareto_optimal_paths = list(flattened for flattened, _ in itertools.groupby(flattened))

	#temporary (stupid) solution
	stupid_out = []
	for this_path in pareto_optimal_paths:
		new_path = []
		for this_range in this_path:
			for this_data in data:
				if this_range == this_data["onset_range"]:
					new_path.append([this_data["fragment"], this_range])
					continue
		stupid_out.append(new_path)

	return stupid_out