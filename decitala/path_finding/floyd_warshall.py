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
from .path_finding_utils import cost, best_source_and_sink

logger = get_logger(name=__name__, print_to_console=True)

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

def reconstruct_standard_path(
		data,
		next_matrix,
		start,
		end
	):
	path = [start]
	if end["onset_range"][0] <= start["onset_range"][-1]:
		return path

	while start != end:
		start_index = next((index for (index, d) in enumerate(data) if d["id"] == start["id"]), None)
		end_index = next((index for (index, d) in enumerate(data) if d["id"] == end["id"]), None)
		start = next_matrix[start_index][end_index]
		path.append(start)

	return path

def get_path(
		start,
		end,
		next_matrix,
		data,
		slur_constraint=False
	):
	"""
	Function for retriving the best path extracted from the Floyd-Warshall algorithm.

	:param `~decitala.fragment.GeneralFragment` start: starting fragment in the path.
	:param `~decitala.fragment.GeneralFragment` end: ending fragment in the path.
	:param numpy.array next_matrix: second matrix from
			:obj:`~decitala.path_finding.floyd_warshall.floyd_warshall`.
	:param list data: data from :obj:`~decitala.search.rolling_search``.
	:return: best path extracted using the Floyd-Warshall algorithm.
	:rtype: list
	"""
	if slur_constraint is False:
		path = reconstruct_standard_path(data, next_matrix, start, end)
		return path
	else:
		slurred_fragments_indices = [data.index(x) for x in data if x["is_spanned_by_slur"] is True]
		if len(slurred_fragments_indices) == 0:
			path = reconstruct_standard_path(data, next_matrix, start, end)
			return path

		start_index = next((index for (index, d) in enumerate(data) if d["id"] == start["id"]), None)
		end_index = next((index for (index, d) in enumerate(data) if d["id"] == end["id"]), None)

		if slurred_fragments_indices[0] <= start_index:
			curr_start = data[slurred_fragments_indices[0]]
		elif data[slurred_fragments_indices[0]]["onset_range"][0] < data[start_index]["onset_range"][1]:
			curr_start = data[slurred_fragments_indices[0]]
		else:
			curr_start = data[start_index]

		path = [curr_start]

		if slurred_fragments_indices[-1] >= end_index:
			overall_end = data[slurred_fragments_indices[-1]]
			fragment_slur_is_ending = True
		elif data[slurred_fragments_indices[-1]]["onset_range"][0] < data[end_index]["onset_range"][1]:
			overall_end = data[slurred_fragments_indices[-1]]
			fragment_slur_is_ending = True
		else:
			overall_end = end
			fragment_slur_is_ending = False

		i = 0
		while i < len(slurred_fragments_indices) - 1:
			if i != 0:
				curr_start = slurred_fragments_indices[i]

			curr_end = data[slurred_fragments_indices[i + 1]]
			while curr_start != curr_end:
				curr_start = next_matrix[slurred_fragments_indices[i + 1]][slurred_fragments_indices[i + 1]]
				path.append(curr_start)
			i += 1

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