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
		curr_vertex_index = dist.index(min(dist))
		curr_vertex = vertices[curr_vertex_index] # vertex with minimum distance (source at the start). 
		
		del vertices[curr_vertex_index]

		if curr_vertex == target:
			break

		for other_vertex in vertices:
			other_vertex_index = vertices.index(other_vertex)
			alt = dist[curr_vertex_index] + cost(curr_vertex, other_vertex, weights=weights)
			if alt < dist[other_vertex_index]:
				dist[other_vertex_index] = alt
				prev[other_vertex_index] = curr_vertex
	
	return dist, prev

	






