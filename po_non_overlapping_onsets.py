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
'''
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
            print(len(solutions))
            if len(solutions) == 100:
                print('just passed...')
        else:
            for successor in successors[node]:
                print_path_rec(successor, path + [node])

    for source in sources:
        print_path_rec(source, [])

    flatten = lambda l: [item for sublist in l for item in sublist]
    flattened = flatten(solutions)

    return flattened

'''
tup_lst = [
    (0.0, 2.0), (0.0, 4.0), (2.5, 4.5), (2.0, 5.75),
    (2.0, 4.0), (6.0, 7.25), (4.0, 5.5)
]
'''

'''
one thing that would make this faster is to first search through and find any ranges that are non overlapping with *all* of the rest
this could significantly shorten this process.
'''




