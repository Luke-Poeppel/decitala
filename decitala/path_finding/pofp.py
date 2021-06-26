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
	"""
	check = []
	for this_data in data[0:i]:
		range_data = this_data.onset_range
		if data[i].onset_range[0] >= range_data[0] and data[i].onset_range[0] >= range_data[1]:
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
	"""
	break_points = get_break_points(data)
	out = [data[i:j] for i, j in zip([0] + break_points, break_points + [None])]

	return out

####################################################################################################
def _min_successor_to_elem(elem, all_min_successors):
	for data in all_min_successors:
		if data[0].id_ == elem.id_:
			return data[1]

def get_pareto_optimal_longest_paths(data):
	"""
	>>> from decitala.search import Extraction
	>>> from decitala.fragment import GreekFoot, GeneralFragment
	>>> data = [
	... 	Extraction(fragment=GreekFoot("Spondee"), frag_type="greek_foot", onset_range=(0.0, 0.5), retrograde=False, factor=0.125, difference=0.0, mod_hierarchy_val=1, pitch_content=[None], is_spanned_by_slur=False, slur_count=0, slur_start_end_count=0, id_=1), # noqa
	... 	Extraction(fragment=GeneralFragment([0.25, 0.25], name="cs-test1"), frag_type="general_fragment", onset_range=(0.0, 0.5), retrograde=False, factor=2.0, difference=0.0, mod_hierarchy_val=1, pitch_content=[None], is_spanned_by_slur=False, slur_count=0, slur_start_end_count=0, id_=2), # noqa
	... 	Extraction(fragment=GreekFoot("Trochee"), frag_type="greek_foot", onset_range=(0.25, 0.625), retrograde=False, factor=0.125, difference=0.0, mod_hierarchy_val=1, pitch_content=[None], is_spanned_by_slur=False, slur_count=0, slur_start_end_count=0, id_=3), # noqa
	... 	Extraction(fragment=GeneralFragment([0.25, 0.125], name="cs-test2"), frag_type="general_fragment", onset_range=(0.25, 0.625), retrograde=False, factor=0.125, difference=0.0, mod_hierarchy_val=1, pitch_content=[None], is_spanned_by_slur=False, slur_count=0, slur_start_end_count=0, id_=4), # noqa
	... 	Extraction(fragment=GreekFoot("Dactyl"), frag_type="greek_foot", onset_range=(0.5, 1.0), retrograde=False, factor=0.125, difference=0.0, mod_hierarchy_val=1, pitch_content=[None], is_spanned_by_slur=False, slur_count=0, slur_start_end_count=0, id_=5) # noqa
	... ]
	>>> for path in get_pareto_optimal_longest_paths(data):
	... 	for fragment in path:
	... 		print(fragment.fragment, fragment.onset_range)
	... 	print("-----")
	<fragment.GreekFoot Spondee> (0.0, 0.5)
	<fragment.GreekFoot Dactyl> (0.5, 1.0)
	-----
	<fragment.GeneralFragment cs-test1: [0.25 0.25]> (0.0, 0.5)
	<fragment.GreekFoot Dactyl> (0.5, 1.0)
	-----
	<fragment.GreekFoot Trochee> (0.25, 0.625)
	-----
	<fragment.GeneralFragment cs-test2: [0.25  0.125]> (0.25, 0.625)
	-----
	"""
	sources = [x for x in data if not any(y.onset_range[1] <= x.onset_range[0] for y in data)]
	sinks = [x for x in data if not any(x.onset_range[1] <= y.onset_range[0] for y in data)]

	all_ids = [x.id_ for x in data]
	sink_ids = [x.id_ for x in sinks]
	remaining = set(all_ids) - set(sink_ids)
	filtered_data = [x for x in data if x.id_ in remaining]

	min_successors = []
	for x in filtered_data:
		candidates = [y for y in data if y.onset_range[0] >= x.onset_range[1]] # noqa and y["onset_range"] != x["onset_range"]]  
		min_successor = min(candidates, key=lambda x: x.onset_range[0])
		min_successors.append([x, min_successor])

	successors = []
	for x in data:
		successor = [y for y in data if x.onset_range[1] <= y.onset_range[0] <= y.onset_range[1] and y.onset_range[0] < _min_successor_to_elem(x, min_successors).onset_range[1]] # noqa
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
				if this_range == this_data.onset_range:
					new_path.append([this_data, this_range])
					continue
		stupid_out.append(new_path)

	return stupid_out