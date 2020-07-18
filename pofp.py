# -*- coding: utf-8 -*-
####################################################################################################
# File:     po_non_overlapping_onsets.py
# Purpose:  M. Raynards techniques for solving the non-overlapping onset ranges problem using 
#           Pareto optimal frontiers of sequences.
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
'''
This module holds the functions for generating a pareto optimal frontier of paths given a list of 
onset ranges. The function has some unnecessarily large space complexity as it reprocesses data 
ranges that are fixed. To solve this problem, we use a function to partition the data into completely
non-overlapping, manageable chunks of length between 10 and 20. 

TODO:
- doctests/unittests
- visualization of the various possibilities for overlaps. 
'''
import copy
import doctest
import itertools
import matplotlib.pyplot as plt
import unittest
import warnings

def partition_onset_list(onset_list):
    """
    A function that takes in data of the form [(<decitala>, (<mod>), ...), (<onset_range>)]
    and returns a new list that holds the same data partitioned into chunks of length less than 20.

    TODO: a more dynamic approach would be to *find* all the places where it's non overlapping and figure
    out the partition size calculation after the fact! 
     
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
    data_length = len(onset_list)
    if data_length < 20:
        return onset_list
    else:
        pass

    num_partitions = (data_length // 15)  #somewhat arbitrary, just fast.
    partitions = []

    def max_end_overlap(tup1, tup2):
        if tup1[1] == tup2[0]:
            return True
        elif tup1[1] < tup2[0]:
            return True
        else:
            return False

    copied = copy.copy(onset_list)
    partitions = []
    j = 0

    while j < num_partitions:
        i = 0
        first_partition = []
        while i < len(copied) - 1:
            curr_range = copied[i]
            next_range = copied[i + 1]

            if max_end_overlap(curr_range[-1], next_range[-1]) == True:
                if len(first_partition) >= 10 and len(first_partition) <= 20:
                    first_partition.append(curr_range)
                    break
                else:
                    first_partition.append(curr_range)
            else:
                first_partition.append(curr_range)
            
            i += 1
            
        partitions.append(first_partition)
        end_index = copied.index(first_partition[-1])
        copied = copied[end_index + 1:]

        j += 1

    #append whatever is left over
    partitions.append(copied)

    return partitions

def get_pareto_optimal_longest_paths(tup_lst_in):
    """
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

def show_paths(paths: list, title: str):
    """
    A nice visualization for paths. For now, limited to 2.
    """
    raise NotImplementedError

# Helper function to ignore annoying warnings 
# source: https://www.neuraldump.net/2017/06/how-to-suppress-python-unittest-warnings/
def ignore_warnings(test_func):
    def do_test(self, *args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            test_func(self, *args, **kwargs)
    return do_test

class Test(unittest.TestCase):
    """
    Unittest(s)
    """
    def setUp(self):
        warnings.simplefilter('ignore', category=ImportWarning)
        
    def test_unittest(self):
        test_string = "Is this thing on?"
        assert test_string != "This thing is on!"

    @ignore_warnings
    def test_partition_lengths(self):
        """
        Check that the number of talas in the rolling search is equal to the number of talas
        in the partitions. 
        """
        from decitala import Decitala, FragmentTree
        
        decitala_path = '/Users/lukepoeppel/decitala_v2/Decitalas'
        sept_haikai_path = '/Users/lukepoeppel/Desktop/Messiaen/Sept_Haikai/1_Introduction.xml' 

        tree = FragmentTree(root_path = decitala_path, frag_type = 'decitala', rep_type = 'ratio')

        onset_ranges = []
        for this_tala in tree.rolling_search(path = sept_haikai_path, part_num = 1):
            onset_ranges.append(list(this_tala))

        sorted_onset_ranges = sorted(onset_ranges, key = lambda x: x[1][0])
        partitioned = partition_onset_list(sorted_onset_ranges)
        full_count = 0
        for x in partitioned:
            for this_range in x:
                full_count += 1

        assert len(sorted_onset_ranges) == full_count

if __name__ == '__main__':
    doctest.testmod()
    unittest.main()

