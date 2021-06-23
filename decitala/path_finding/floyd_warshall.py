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

from decitala.path_finding.path_finding_utils import DefaultCostFunction

def floyd_warshall(
		data,
		cost_function_class=DefaultCostFunction(),
		verbose=False
	):
	"""
	Calculates the distance and next matrices of the Floyd-Warshall path-finding algorithm.

	:param list data: a list of :obj:`decitala.search.Extraction` objects.
	:param `decitala.path_finding.path_finding_utils.CostFunction` cost_function_class: a cost
		function that will be used in calculating the weights between vertices.
	:param bool verbose: Whether to log messages (including showing a progress bar).
	:return: Two matrices of size len(data) x len(data): first is the weighted adjacency matrix, the
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
			cost_ = cost_function_class.cost(vertex_a=data[index_1], vertex_b=data[index_2])
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
	"""
	:param list data: a list of :obj:`decitala.search.Extraction` objects.
	"""
	path = [start]
	if end.onset_range[0] <= start.onset_range[-1]:
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

	:param start: an :obj:`decitala.search.Extraction` object.
	:param end: an :obj:`decitala.search.Extraction` object.
	:param numpy.array next_matrix: second matrix from
			:obj:`~decitala.path_finding.floyd_warshall.floyd_warshall`.
	:param list data: data from :obj:`~decitala.search.rolling_search`.
	:return: best path extracted using the Floyd-Warshall algorithm.
	:rtype: list
	"""
	if slur_constraint is False:
		path = reconstruct_standard_path(data, next_matrix, start, end)
		return path
	else:
		slurred_fragments_indices = [data.index(x) for x in data if x.is_spanned_by_slur]
		if len(slurred_fragments_indices) == 0:
			path = reconstruct_standard_path(data, next_matrix, start, end)
			return path

		start_index = next((index for (index, d) in enumerate(data) if d.id_ == start.id_), None)
		end_index = next((index for (index, d) in enumerate(data) if d.id_ == end.id_), None)

		if slurred_fragments_indices[0] <= start_index:
			curr_start = data[slurred_fragments_indices[0]]
		elif data[slurred_fragments_indices[0]].onset_range[0] < data[start_index].onset_range[1]:
			curr_start = data[slurred_fragments_indices[0]]
		else:
			curr_start = data[start_index]

		path = [curr_start]

		if slurred_fragments_indices[-1] >= end_index:
			overall_end = data[slurred_fragments_indices[-1]]
			fragment_slur_is_ending = True
		elif data[slurred_fragments_indices[-1]].onset_range[0] < data[end_index].onset_range[1]:
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
		elif overall_end.onset_range[0] < path[-1].onset_range[1]:
			pass  # sink input clashes with final slurred fragment.
		else:
			while curr_start != overall_end:
				start_index = slurred_fragments_indices[-1]
				curr_start = next_matrix[start_index][end_index]
				path.append(curr_start)

		return path