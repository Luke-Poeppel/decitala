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