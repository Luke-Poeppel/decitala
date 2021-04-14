import numpy as np

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

	for k in range(0, len(data)):
		for i in range(0, len(data)):
			for j in range(0, len(data)):
				if dist_matrix[i][j] > dist_matrix[i][k] + dist_matrix[k][j]:
					dist_matrix[i][j] = dist_matrix[i][k] + dist_matrix[k][j]
					next_matrix[i][j] = next_matrix[i][k]

	return dist_matrix, next_matrix