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

from .path_finding_utils import cost

def dijkstra(
		data,
		source,
		target,
		weights,
		verbose=False
	):
	vertices = []
	dist = [np.inf] * len(data)
	prev = [None] * len(data)
	
	source_index = 0
	for i, fragment_data in enumerate(data):
		if fragment_data == source:
			source_index = i
		vertices.append(fragment_data)
	
	dist[source_index] = 0

	while vertices:
		curr_vertex = min(dist)
		del vertices[dist.index(u)]

		if u == target:
			break

		for v in vertices:
			alt = dist[u] + cost(u, v, weights=weights)
			# if alt < dist[v]:
			# 	dist[v] = alt
			# 	prev[v] = u
		
		break

	return dist, prev

	






