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

from ..utils import get_logger

logger = get_logger(name=__name__, print_to_console=True)

def cost(
		vertex_1,
		vertex_2,
		weights
	):
	"""
	Cost function used in the Floyd-Warshall Algorithm.

	:param `~decitala.fragment.GeneralFragment` vertex_1: an object inheriting from
			:obj:`~decitala.fragment.GeneralFragment`.
	:param `~decitala.fragment.GeneralFragment` vertex_2: an object inheriting from
			:obj:`~decitala.fragment.GeneralFragment`.
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
		weights,
		verbose=False
	):
	"""
	Calculates the distance and next matrices of the Floyd-Warshall path-finding algorithm.

	:param list data: data from :obj:`~decitala.search.rolling_search`.
	:param dict weights: weights to be used in the cost function. Must sum to 1. Requires "gap"
			and "onsets" values.
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
	# logger.info("Building initial matrix...")
	while not iterator.finished:
		if iterator.multi_index[0] == iterator.multi_index[1]:  # diagonal
			dist_matrix[iterator.multi_index] = 0
			next_matrix[iterator.multi_index] = data[iterator.multi_index[0]]
		elif iterator.multi_index[1] < iterator.multi_index[0]:
			dist_matrix[iterator.multi_index] = np.inf  # good heuristic
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
	# logger.info("Finished building initial matrix.")
	
	# logger.info("Running Floyd-Warshall Algorithm...")
	if verbose is True:
		with Bar("Processing...", max=len(data), check_tty=False, hide_cursor=False) as bar:
			for k in range(0, len(data)):
				for i in range(0, len(data)):
					for j in range(0, len(data)):
						if dist_matrix[i][j] > dist_matrix[i][k] + dist_matrix[k][j]:
							dist_matrix[i][j] = dist_matrix[i][k] + dist_matrix[k][j]
							next_matrix[i][j] = next_matrix[i][k]
				bar.next()
	else:
		for k in range(0, len(data)):
			for i in range(0, len(data)):
				for j in range(0, len(data)):
					if dist_matrix[i][j] > dist_matrix[i][k] + dist_matrix[k][j]:
						dist_matrix[i][j] = dist_matrix[i][k] + dist_matrix[k][j]
						next_matrix[i][j] = next_matrix[i][k]

	return dist_matrix, next_matrix

def sources_and_sinks(data):
	sources = [x for x in data if not any(y["onset_range"][1] <= x["onset_range"][0] for y in data)]
	sinks = [x for x in data if not any(x["onset_range"][1] <= y["onset_range"][0] for y in data)]
	
	return sources, sinks

def best_source_and_sink(data):
	sources, sinks = sources_and_sinks(data)
	if len(sources) == 1:
		curr_best_source = sources[0]
	elif len(sinks) == 1:
		curr_best_sink = sinks[0]
	else:
		lowest_point = min(sources, key=lambda x: x["onset_range"][0])["onset_range"][0]
		curr_best_source = sources[0]
		for source in sources:
			if source["onset_range"][0] == lowest_point:
				if source["fragment"].num_onsets > curr_best_source["fragment"].num_onsets:
					curr_best_source = source
			else:
				continue
		
		curr_best_sink = sinks[0]
		for sink in sinks:
			if sink["fragment"].num_onsets > curr_best_sink["fragment"].num_onsets:
				curr_best_sink = sink
			else:
				continue
				
	return curr_best_source, curr_best_sink

def get_path(
		start,
		end,
		next_matrix,
		data,
		slur_constraint=False
	):
	"""
	Function for retriving the best path extracted from
		:obj:`~decitala.path_finding.floyd_warshall.floyd_warshall`.

	:param `~decitala.fragment.GeneralFragment` start: starting fragment in the path.
	:param `~decitala.fragment.GeneralFragment` end: ending fragment in the path.
	:param numpy.array next_matrix: second matrix from
			:obj:`~decitala.path_finding.floyd_warshall.floyd_warshall`.
	:param list data: data from :obj:`~decitala.search.rolling_search``.
	:return: best path extracted using the Floyd-Warshall algorithm.
	:rtype: list
	"""
	path = [start]
	if slur_constraint is False:
		while start != end:
			start_index = next((index for (index, d) in enumerate(data) if d["id"] == start["id"]), None)
			end_index = next((index for (index, d) in enumerate(data) if d["id"] == end["id"]), None)
			start = next_matrix[start_index][end_index]
			path.append(start)
	else:
		slurred_fragments_indices = [data.index(x) for x in data if x["is_spanned_by_slur"] is True]
		start_index = next((index for (index, d) in enumerate(data) if d["id"] == start["id"]), None)
		end_index = next((index for (index, d) in enumerate(data) if d["id"] == end["id"]), None)
		
		if slurred_fragments_indices[0] == start_index:
			curr_start = data[slurred_fragments_indices[0]]
		else:
			curr_start = data[start_index]
		
		if slurred_fragments_indices[-1] == end_index:
			overall_end = data[slurred_fragments_indices[-1]]
			fragment_slur_is_ending = True
		else:
			overall_end = end
			fragment_slur_is_ending = False

		i = 0
		while i < len(slurred_fragments_indices) - 1:			
			if i != 0:
				curr_start = slurred_fragments_indices[i]

			curr_end = data[slurred_fragments_indices[i+1]]
			while curr_start != curr_end:
				curr_start = next_matrix[slurred_fragments_indices[i]][slurred_fragments_indices[i+1]]
				path.append(curr_start)
			i += 1
		
		# import pdb; pdb.set_trace()
		if fragment_slur_is_ending is True:
			pass
		elif overall_end["onset_range"][0] < path[-1]["onset_range"][1]:
			pass  # sink input clashes with final slurred fragment. 
		else:
			while curr_start != overall_end:
				start_index = slurred_fragments_indices[-1]
				curr_start = next_matrix[start_index][end_index]				
				path.append(curr_start)

	return path