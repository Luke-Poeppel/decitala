# -*- coding: utf-8 -*-
####################################################################################################
# File:     floyd_warshall.py
# Purpose:  Implementation of the Floyd-Warshall Algorithm for path-finding. 
# 
# Author:   Luke Poeppel
#
# Location: NYC, 2021
####################################################################################################
def cost(
        vertex_1, 
        vertex_2, 
        weights={
            "gap": 0.7,
            "onsets": 0.3
        }
    ):
    gap = vertex_2["onset_range"][0] - vertex_1["onset_range"][1]
    onsets = 1 / (vertex_1["fragment"].num_onsets + vertex_2["fragment"].num_onsets)
    cost = (weights["gap"] * gap) + (weights["onsets"] * onsets)
    return cost

def floyd_warshall(data):
    dist_matrix = np.full(shape=(len(data), len(data)), fill_value=np.inf)
    next_matrix = np.full(shape=(len(data), len(data)), fill_value=None)
    iterator = np.nditer(
        [dist_matrix, next_matrix], 
        flags=['multi_index', 'refs_ok'], 
        op_flags=['readwrite'],
    )
    while not iterator.finished:
        if iterator.multi_index[0] == iterator.multi_index[1]:
            dist_matrix[iterator.multi_index] = 0
            next_matrix[iterator.multi_index] = data[iterator.multi_index[0]]
        else:
            index_1 = iterator.multi_index[0]
            index_2 = iterator.multi_index[1]
            cost_ = cost(data[index_1], data[index_2])
            dist_matrix[iterator.multi_index] = cost_
            next_matrix[iterator.multi_index] = data[iterator.multi_index[1]]
        iterator.iternext()
    
    for k in range(0, len(data)):
        for i in range(0, len(data)):
            for j in range(0, len(data)):
                if dist_matrix[i][j] > dist_matrix[i][k] + dist_matrix[k][j]:
                    dist_matrix[i][j] = dist_matrix[i][k] + dist_matrix[k][j]
                    next_matrix[i][j] = next_matrix[i][k]

	return dist_matrix, next_matrix