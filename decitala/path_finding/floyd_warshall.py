# -*- coding: utf-8 -*-
####################################################################################################
# File:     floyd_warshall.py
# Purpose:  Implementation of the Floyd-Warshall Algorithm for path-finding. 
# 
# Author:   Luke Poeppel
#
# Location: NYC, 2021
####################################################################################################
"""
Implementation of the Floyd-Warshall Algorithm (path of minimal cost). 
"""
import numpy as np

from progress.bar import Bar

def cost(
		vertex_1, 
		vertex_2, 
		weights
	):
	"""
	Cost function used in the Floyd-Warshall Algorithm. 

	:param :obj:`~decitala.fragment.GeneralFragment` vertex_1: an object inheriting 
		from :obj:`~decitala.fragment.GeneralFragment`
	:param :obj:`~decitala.fragment.GeneralFragment` vertex_2: an object inheriting 
		from :obj:`~decitala.fragment.GeneralFragment`
	:param dict weights: weights used in the model. Must sum to 1. Requires "gap" and "onsets" values. 
	:return: cost of moving from ``vertex_1`` to ``vertex_2``.
	:rtype: float
	"""
	gap = vertex_2["onset_range"][0] - vertex_1["onset_range"][1]
	onsets = 1 / (vertex_1["fragment"].num_onsets + vertex_2["fragment"].num_onsets)
	cost = (weights["gap"] * gap) + (weights["onsets"] * onsets)
	return cost

def floyd_warshall(
		data, 
		weights
	):
	"""
	Calculates the distance and next matrices of the Floyd-Warshall path-finding algorithm.

	:param list data: data from :obj:`~decitala.search.rolling_search``.
	:param dict weights: weights to be used in the cost function. Must sum to 1. Requires "gap" and "onsets" values.
	:return: two matrices of size len(data) x len(data): first is the weighted adjacency matrix, the 
			second is the matrix used for path reconstruction. 
	:rtype: tuple
	"""
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
		elif iterator.multi_index[1] < iterator.multi_index[0]:
			dist_matrix[iterator.multi_index] = np.inf
		else:
			index_1 = iterator.multi_index[0]
			index_2 = iterator.multi_index[1]
			cost_ = cost(data[index_1], data[index_2], weights)
			if cost_ < 0:
				dist_matrix[iterator.multi_index] = np.inf
				next_matrix[iterator.multi_index] = None
			else:
				dist_matrix[iterator.multi_index] = cost_
				next_matrix[iterator.multi_index] = data[iterator.multi_index[1]]
		iterator.iternext()
	
	#with Bar("Building matrices...", max=len(data), check_tty=False, hide_cursor=False) as bar:
	for k in range(0, len(data)):
		for i in range(0, len(data)):
			for j in range(0, len(data)):
				if dist_matrix[i][j] > dist_matrix[i][k] + dist_matrix[k][j]:
					dist_matrix[i][j] = dist_matrix[i][k] + dist_matrix[k][j]
					next_matrix[i][j] = next_matrix[i][k]
		#bar.next()
	
	return dist_matrix, next_matrix

def get_path(start, end, next_matrix, data):
	"""
	Function for retriving the best path extracted from :obj:`~decitala.path_finding.floyd_warshall.floyd_warshall`.

	:param :obj:`~decitala.fragment.GeneralFragment` start: starting fragment in the path.
	:param :obj:`~decitala.fragment.GeneralFragment` end: ending fragment in the path.
	:param numpy.array next_matrix: second matrix from :obj:`~decitala.path_finding.floyd_warshall.floyd_warshall`.
	:param list data: data from :obj:`~decitala.search.rolling_search``.
	:return: best path extracted using the Floyd-Warshall algorithm.
	:rtype: list
	"""
	path = [start]
	while start != end:
		start_index = next((index for (index, d) in enumerate(data) if d["id"] == start["id"]), None)
		end_index = next((index for (index, d) in enumerate(data) if d["id"] == end["id"]), None)
		start = next_matrix[start_index][end_index]
		path.append(start)
	return path