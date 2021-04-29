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
def dijkstra(
		data,
		source,
		target,
		weights={"gap": 0.75, "onsets": 0.25}
	):
	"""
	Dijkstra path-finding algorithm from dynamic programming. Uses a min-heap
	data structure for efficiency.

	:param list data: Data from one of the search algorithms (each result being a dictionary.)
	:param dict source: Any element from ``data``.
	:param dict target: Any element from ``data``.
	"""
	graph = path_finding_utils.build_graph(data, weights)
	source = source["id"]
	target = target["id"]

	q = []
	dist = {x: np.inf for x in graph.keys()}
	pred = {}

	dist[source] = 0
	heapq.heappush(q, (0, source))

	while q:
		last_w, curr_v = heapq.heappop(q)
		for n, n_w in graph[curr_v]:
			cand_w = last_w + n_w
			if cand_w < dist[n]:
				dist[n] = cand_w
				pred[n] = curr_v
				heapq.heappush(q, (cand_w, n))

	return dist, pred

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
	source = source["id"]
	target = target["id"]

	path = [target]
	while True:
		key = pred[path[0]]
		path.insert(0, key)
		if key == source:
			break
	return path