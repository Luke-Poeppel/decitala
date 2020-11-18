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

Once we have retrieved :math:`n` talas in an instrument, we want to check whether or not they align. 
If a tala :math:`T_1` ranges from onsets :math:`X_i` to :math:`Y_i` and a tala :math:`T_2` ranges from 
onsets :math:`X_j` to :math:`Y_j`, if :math:`X_j < Y_i`, we can't satisfactorily align :math:`T_1` and
:math:`T_2`; this means that one or both of those talas was not intentionally included, and simply 
exists as a sub-tala/cyclic rotation. Multiple possible alignments exist, so we calculate them all
using an iterative solution to the end-overlapping indices problem using a Pareto frontier of paths. 
"""
import copy
import itertools
import matplotlib.pyplot as plt
import pytest
import unittest
import warnings

"""
>>> sept_haikai_data = [
...         (('info_0',), (0.0, 4.0)), (('info_1',), (2.5, 4.75)), (('info_2',), (4.0, 5.25)), (('info_3',), (4.0, 5.75)), (('info_4',), (5.75, 9.75)), (('info_5',), (5.75, 13.25)), 
...         (('info_6',), (8.25, 11.25)), (('info_7',), (8.25, 13.25)), (('info_8',), (9.75, 12.25)), (('info_9',), (10.25, 13.25)), (('info_10',), (13.25, 14.5)), (('info_11',), (13.25, 15.0)), 
...         (('info_12',), (15.0, 19.0)), (('info_13',), (19.0, 19.875)), (('info_14',), (19.0, 20.875)), (('info_15',), (19.375, 20.875)), (('info_16',), (20.875, 22.125)), (('info_17',), (20.875, 22.625)), 
...         (('info_18',), (21.625, 23.125)), (('info_19',), (22.625, 30.625)), (('info_20',), (23.125, 27.625)), (('info_21',), (24.625, 29.625)), (('info_22',), (26.125, 29.625)), (('info_23',), (26.125, 30.625)), 
...         (('info_24',), (27.625, 30.625)), (('info_25',), (30.625, 31.5)), (('info_26',), (30.625, 32.5)), (('info_27',), (31.0, 32.5)), (('info_28',), (31.0, 33.5)), (('info_29',), (31.5, 34.0)), 
...         (('info_30',), (32.5, 34.625)), (('info_31',), (34.0, 35.0)), (('info_32',), (34.625, 35.875)), (('info_33',), (34.625, 36.375)), (('info_34',), (35.375, 37.125)), (('info_35',), (35.875, 37.125)), 
...         (('info_36',), (36.375, 37.625)), (('info_37',), (36.375, 38.125)), (('info_38',), (38.125, 39.0)), (('info_39',), (38.125, 40.0)), (('info_40',), (38.5, 40.0)), (('info_41',), (40.0, 41.25)), 
...         (('info_42',), (40.0, 41.75)), (('info_43',), (41.75, 45.75)), (('info_44',), (45.75, 46.625)), (('info_45',), (45.75, 47.625)), (('info_46',), (46.125, 47.625)), (('info_47',), (47.625, 48.875)), 
...         (('info_48',), (47.625, 49.375)), (('info_49',), (49.375, 53.375)), (('info_50',), (49.375, 56.875)), (('info_51',), (51.875, 54.875)), (('info_52',), (51.875, 56.875)), (('info_53',), (53.375, 55.875)), 
...         (('info_54',), (53.875, 56.875)), (('info_55',), (56.875, 58.125)), (('info_56',), (56.875, 58.625)), (('info_57',), (58.625, 62.625)), (('info_58',), (61.125, 63.375)), (('info_59',), (62.625, 63.875)), (('info_60',), (62.625, 64.375))
... ]
>>> partitioned = partition_onset_list(sept_haikai_data)

We extract the first partition.
>>> for x in partitioned[0]:
...     print(x[-1])
(0.0, 4.0)
(2.5, 4.75)
(4.0, 5.25)
(4.0, 5.75)
(5.75, 9.75)
(5.75, 13.25)
(8.25, 11.25)
(8.25, 13.25)
(9.75, 12.25)
(10.25, 13.25)
(13.25, 14.5)
(13.25, 15.0)
"""

####################################################################################################
"""
The above partition function works great for Sept Haikai but has trouble with other pieces. I think 
a far more elegant solution would be to make it more dynamic. 
"""
def _check_all_prev(onset_list, i):
	"""
	Checks at a particular index if all values prior to it are less than or equal to it.

	>>> tup_lst = [
	...     (("info1",), (0.0, 2.0)), (("info2",), (0.0, 4.0)), (("info3",), (2.5, 4.5)), (("info4",), (2.0, 5.75)),
	...     (("info5",), (2.0, 4.0)), (("info6",), (6.0, 7.25)), (("info7",), (4.0, 5.5))]
	>>> print(_check_all_prev(tup_lst, 2))
	False
	>>> print(_check_all_prev(tup_lst, 5))
	True
	"""
	check = []
	for this_data in onset_list[0:i]:
		range_data = this_data[1]
		if onset_list[i][1][0] >= range_data[0] and onset_list[i][1][0] >= range_data[1]:
			check.append(1)
		else:
			check.append(0)
	
	if set(check) == {1}:
		return True
	else:
		return False

def naive_partition(onset_list):
	"""
	Partitions the onset list without regard for nice breakpoints into chunks of length 18. 
	The remainder is the last partitions. 
	"""
	copied = copy.copy(onset_list)
	length = len(copied)

	partition_indices = list(range(0, length, 18))
	diff = length - partition_indices[-1]

	if diff == 0:
		del partition_indices[0]
	else:
		del partition_indices[0]
		partition_indices.append(partition_indices[-1] + 1)

	partitions = []
	for this_partition_index in partition_indices:
		partitions.append(copied[0:partition_indices[0]])
		copied = copied[partition_indices[0]:]

	return partitions

def check_good(lst):
	"""
	Checks if for every increment of 20, there exists a value. 
	"""
	if len(lst) == 0:
		return False

	vals = []
	i = 0
	while i < len(lst) - 1:
		curr_val = lst[i]
		next_val = lst[i + 1]
		vals.append(next_val - curr_val <= 20)
		i += 1
	
	return all(vals)

def get_break_points(lst):
	i = 0
	break_points = []
	while i < len(lst) - 1:
		if _check_all_prev(lst, i):
			break_points.append(i)
			
		i += 1
	
	return break_points

def get_filtered_break_points(break_points):
	filtered_break_points = copy.copy(break_points)
	i = 0
	partition_start = 0
	while i < len(filtered_break_points):
		if 9 <= filtered_break_points[i] - partition_start <= 19:
			partition_start = filtered_break_points[i]
			i += 1
		else:
			del filtered_break_points[i]

	return filtered_break_points

def dynamically_partition_onset_list(onset_list):
	"""
	1.) Go through and check if we can find breakpoints for end-overlapping paths. To do this, we need to use
	the check_all_prev function.
	2.) If breakpoints can be found, check if there are enough (and are of appropriate size) to form partitions. 
	3.) If no breakpoints can be found (or they are of inappropriate lengths, i.e., > 20), partition the data 
	randomly into chunks of 18 and append the remaining. 
	"""
	data_length = len(onset_list)
	if data_length <= 18:
		return onset_list

	break_points = get_break_points(onset_list)
	if break_points:
		filtered_break_points = get_filtered_break_points(break_points)
		if check_good(filtered_break_points):
			pass
		else:
			raise NotImplementedError
			#return naive_partition(onset_list)

		out = [onset_list[i:j] for i, j in zip([0]+filtered_break_points, filtered_break_points + [None])]

		return out
	else:
		raise NotImplementedError
		#return naive_partition(onset_list)

################################################################

def filter_single_anga_class_talas(onset_list):
	"""
	Given the output tala data from the rolling window search, returns a new list 
	with all single anga class talas removed. 
	"""
	return list(filter(lambda x: x[0][0].num_anga_classes != 1, onset_list))

def filter_subtalas(onset_list):
	"""
	Given the output tala data from the filter above, returns a new list with 
	all subtalas (that is, talas that "sit inside" other talas) removed. 
	"""
	just_talas = list(set([x[0][0] for x in onset_list]))

	def _check_individual_containment(a, b):
		return ', '.join(map(str, a)) in ', '.join(map(str, b))
	
	def _check_all(x):
		check = False
		for this_tala in just_talas:
			if this_tala == x:
				pass
			else:
				if _check_individual_containment(x.successive_ratio_array(), this_tala.successive_ratio_array()):
					check = True
		return check

	#the relevant talas
	filtered = [x for x in just_talas if not(_check_all(x))]
	filtered_ids = [x.id_num for x in filtered]
	
	return [x for x in onset_list if x[0][0].id_num in filtered_ids]

####################################################################################################

def get_pareto_optimal_longest_paths(tup_lst_in):
	"""
	***THIS IS THE FUNCTION USED IN DATABASE
	The last few lines of this are really stupid; I just couldn't figure out the solution today. 
	Something is different about hashing the list of tuples such that it works for the code above
	but not the code when all the data is included. If you make the switch, sources and sinks 
	are fine; the problem begins with min_successor, so it's probably just a coding error. 

	>>> tup_lst = [
	...     (("info1",), (0.0, 2.0)), (("info2",), (0.0, 4.0)), (("info3",), (2.5, 4.5)), (("info4",), (2.0, 5.75)),
	...     (("info5",), (2.0, 4.0)), (("info6",), (6.0, 7.25)), (("info7",), (4.0, 5.5))]
	>>> for onset_range in tup_lst:
	...     print(onset_range)
	...
	(('info1',), (0.0, 2.0))
	(('info2',), (0.0, 4.0))
	(('info3',), (2.5, 4.5))
	(('info4',), (2.0, 5.75))
	(('info5',), (2.0, 4.0))
	(('info6',), (6.0, 7.25))
	(('info7',), (4.0, 5.5))
	>>> for this_path in get_pareto_optimal_longest_paths(tup_lst):
	...     just_paths = [x[1] for x in this_path]
	...     print(just_paths)
	...
	[(0.0, 2.0), (2.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
	[(0.0, 2.0), (2.0, 5.75), (6.0, 7.25)]
	[(0.0, 2.0), (2.5, 4.5), (6.0, 7.25)]
	[(0.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
	"""
	tup_lst = [x[1] for x in tup_lst_in]
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

	#temporary solution
	stupid_out = []
	for this_path in pareto_optimal_paths:
		new_path = []
		for this_range in this_path:
			for this_data in tup_lst_in:
				if this_range == this_data[-1]:
					new_path.append([this_data[0], this_range])
					continue
		stupid_out.append(new_path)

	return stupid_out

#for this in get_pareto_optimal_longest_paths(p0):
	#print(this)

if __name__ == '__main__':
	import doctest
	doctest.testmod()
	#unittest.main()

