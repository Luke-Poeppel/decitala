# -*- coding: utf-8 -*-
####################################################################################################
# File:     dijkstra.py
# Purpose:  Implementation of the Dijkstra algorithm for path-finding.
#
# Author:   Luke Poeppel
#
# Location: NYC, 2021
####################################################################################################
import numpy as np
import heapq

from . import path_finding_utils

# Useful info here: https://stackoverflow.com/questions/22897209/dijkstras-algorithm-in-python.
# Weights found from hyperparameter search on pre-annotated compositions.
def dijkstra(
		data,
		source,
		cost_function_class=path_finding_utils.DefaultCostFunction(),
		verbose=False
	):
	"""
	Dijkstra path-finding algorithm from dynamic programming. Uses a min-heap
	data structure for efficiency.

	:param list data: Data from one of the search algorithms (each result being a dictionary.)
	:param dict source: Any element from ``data``.
	:param dict weights: Dictionary with two keys and values (must sum to 1.0):
						``"gap"`` and ``"onsets"``.
	"""
	graph = path_finding_utils.build_graph(
		data=data,
		cost_function_class=cost_function_class,
		verbose=verbose
	)
	source = source.id_

	q = []
	dist = {x: np.inf for x in graph.keys()}
	pred = {}

	dist[source] = 0
	heapq.heappush(q, (0, source))

	while q:
		last_w, curr_v = heapq.heappop(q)
		for n, n_w in graph[curr_v]:
			alt = last_w + n_w
			if alt < dist[n]:
				dist[n] = alt
				pred[n] = curr_v
				heapq.heappush(q, (alt, n))

	return dist, pred

def dijkstra_best_source_and_sink(
		data,
		cost_function_class=path_finding_utils.DefaultCostFunction()
	):
	"""
	Function for agnostically choosing the best source and target (and associated predecessor set)
	via Dijkstra. Only requires regular data input.
	"""
	sources, targets = path_finding_utils.sources_and_sinks(data)

	# This checks if there exists a fragment in sources/sinks that spans the whole onset range.
	# Alternatively if all extracted fragments are overlapping (see test_povel_essen_dijkstra).
	def _all_overlap(data):
		"""
		Relies on the fact that the output data is sorted by onset range.
		"""
		return data[0].onset_range[1] > data[-1].onset_range[0]

	min_onset = min(sources, key=lambda x: x.onset_range[0]).onset_range[0]
	max_onset = max(targets, key=lambda x: x.onset_range[1]).onset_range[1]

	if _all_overlap(data):
		for possible_source in sources:
			if possible_source.onset_range == (min_onset, max_onset):
				dist, pred = dijkstra(
					data,
					possible_source,
					cost_function_class
				)
				return possible_source, possible_source, pred

		# otherwise choose the longest source.
		return max(sources, key=lambda x: x.fragment.num_onsets)

	best_path_cost = np.inf
	best_source = None
	best_target = None
	best_predecessor_set = None

	for source in sources:
		dist, pred = dijkstra(
			data,
			source,
			cost_function_class
		)
		for target in targets:
			if (dist[target.id_] < best_path_cost):
				if source.onset_range[1] <= target.onset_range[0]:
					best_path_cost = dist[target.id_]
					best_source = source
					best_target = target
					best_predecessor_set = pred

	return best_source, best_target, best_predecessor_set

def generate_path(pred, source, target):
	"""
	Returns the optimal path extracted from Dijkstra.

	:param dict pred: The ``pred`` dictionary returned from
						:obj:`decitala.path_finding.dijkstra.dijkstra`.
	:param dict source: An element from the ``data`` input to
						:obj:`decitala.path_finding.dijkstra.dijkstra`
	:param dict target: An element from the ``data`` input to
						:obj:`decitala.path_finding.dijkstra.dijkstra`
	"""
	source_fragment_id = source.id_
	target_fragment_id = target.id_

	if not pred and source_fragment_id == target_fragment_id:  # Second condition is just a guardrail.
		return [source_fragment_id]

	path = [target_fragment_id]
	while True:
		key = pred[path[0]]
		path.insert(0, key)
		if key == source_fragment_id:
			break
	return path