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
TODO:
- Write a nice method for visualizing the various possibilities for overlaps. 
- The data I'm dealing with generally consist of a tala *and* its indices. If I move over to 
SQLite, this isn't a problem, but, right now, it is.
'''
import copy
import itertools
import matplotlib.pyplot as plt

###################### Code Courtesy of M. Raynard ######################
def overlap_condition(tup1, tup2):
    if tup1 == tup2:
        return False
    a, b = tup1
    c, d = tup2
    return b <= c

def adj_mat_from_tup_list(tup_lst):
    return [
        [
            1 if overlap_condition(tup_lst[i], tup_lst[j]) else 0
            for j in range(len(tup_lst))
        ] for i in range(len(tup_lst))
    ]

def topological_sort(adj_mat):
    sorted_v = []
    sinks = {
        i for i in range(len(adj_mat))
        if not any(adj_mat[j][i] == 1 for j in range(len(adj_mat)))
    }

    while sinks:
        v = sinks.pop()
        sorted_v += [v]
        for j in range(len(adj_mat)):
            if adj_mat[v][j] == 1:
                adj_mat[v][j] = 0
                if not any(adj_mat[w][j] for w in range(len(adj_mat))):
                    sinks.add(j)
    return sorted_v

def get_longest_path(adj_mat, sorted_v):
    dists = {v: 0 for v in range(len(adj_mat))}
    preds = {v: None for v in range(len(adj_mat))}
    for v in sorted_v:
        for u in range(len(adj_mat)):
            if adj_mat[u][v]:
                dists[v] = max(dists[v], dists[u] + 1)
                preds[v] = u

    current_v = {
        v for v in range(len(adj_mat))
        if dists[v] == max(dists.values())
    }.pop()
    result = [current_v]
    while preds[current_v] is not None:
        current_v = preds[current_v]
        result += [current_v]
    return result[::-1]

def get_all_end_overlap_tups(tup_lst):
    sorted_v = topological_sort(adj_mat_from_tup_list(tup_lst))
    adj_mat = adj_mat_from_tup_list(tup_lst)
    return [tup_lst[i] for i in get_longest_path(adj_mat, sorted_v)]

####################################################################################################
"""
def get_pareto_optimal_longest_paths(tup_lst):
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
    
    return pareto_optimal_paths
"""
####################################################################################################
"""
The last few lines of this are really stupid; I just couldn't figure out the solution today. 
Something is different about hashing the list of tuples such that it works for the code above
but not the code when all the data is included. If you make the switch, sources and sinks 
are fine; the problem begins with min_successor, so it's probably just a coding error. 
"""
def get_pareto_optimal_longest_paths(tup_lst_in):
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

####################################################################################################
'''
There's a lot of unnecessary memory loss because of repeated paths. What we need to do is split
a tup_lst into segments that are, at maximum, end-overlapping and less than, 15 tuples long. Example data:
'''
sept_haikai_data = [(0.0, 4.0), (2.5, 4.75), (4.0, 5.25), (4.0, 5.75), (5.75, 9.75), (5.75, 13.25), (8.25, 11.25), (8.25, 13.25), (9.75, 12.25), (10.25, 13.25), (13.25, 14.5), (13.25, 15.0), (15.0, 19.0), (19.0, 19.875), (19.0, 20.875), (19.375, 20.875), (20.875, 22.125), (20.875, 22.625), (21.625, 23.125), (22.625, 30.625), (23.125, 27.625), (24.625, 29.625), (26.125, 29.625), (26.125, 30.625), (27.625, 30.625), (30.625, 31.5), (30.625, 32.5), (31.0, 32.5), (31.0, 33.5), (31.5, 34.0), (32.5, 34.625), (34.0, 35.0), (34.625, 35.875), (34.625, 36.375), (35.375, 37.125), (35.875, 37.125), (36.375, 37.625), (36.375, 38.125), (38.125, 39.0), (38.125, 40.0), (38.5, 40.0), (40.0, 41.25), (40.0, 41.75), (41.75, 45.75), (45.75, 46.625), (45.75, 47.625), (46.125, 47.625), (47.625, 48.875), (47.625, 49.375), (49.375, 53.375), (49.375, 56.875), (51.875, 54.875), (51.875, 56.875), (53.375, 55.875), (53.875, 56.875), (56.875, 58.125), (56.875, 58.625), (58.625, 62.625), (61.125, 63.375), (62.625, 63.875), (62.625, 64.375)]

def partition_onset_list(onset_list):
    '''
    this needs to be *slightly* changed to support the following data format:
    [(<decitala.Decitala 51_Vijaya>, ('ratio', 0.66667)), (0.0, 4.0)]
    This isn't a problem if we include added values as the onset ranges will always be the last 
    value of the list. 
    '''
    data_length = len(onset_list)
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
        while i < len(copied):
            curr_range = copied[i]
            next_range = copied[i + 1]

            if max_end_overlap(curr_range[-1], next_range[-1]) == True:
                if len(first_partition) > 10 and len(first_partition) <= 20:
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

tup_lst = [
    (0.0, 2.0), (0.0, 4.0), (2.5, 4.5), (2.0, 5.75),
    (2.0, 4.0), (6.0, 7.25), (4.0, 5.5)
]

