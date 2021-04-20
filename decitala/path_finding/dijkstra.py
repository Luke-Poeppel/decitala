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

from . import path_finding_utils

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

	# Everything above is right! 
	while vertices:
		curr_vertex_index = dist.index(min(dist))
		curr_vertex = vertices[curr_vertex_index]
		
		del vertices[curr_vertex_index]

		if curr_vertex == target:
			break
		
		for other_vertex in vertices:
			other_vertex_index = vertices.index(other_vertex)
			cost_pre = path_finding_utils.cost(curr_vertex, other_vertex, weights=weights)
			if cost_pre < 0:
				cost = cost_pre + 10000  # Random large number. 
			else:
				cost = cost_pre

			alt = dist[curr_vertex_index] + cost
			if alt < dist[other_vertex_index]:
				dist[other_vertex_index] = alt
				prev[other_vertex_index] = curr_vertex

	return dist, prev

def reconstruct_standard_path(
		data,
		dist,
		prev,
		source,
		target
	):
	path = []
	target_index = prev.index(target)
	if prev[target_index] is not None or target == source:		
		while target is not None:
			path.insert(0, target)
			target = prev[target_index]
	
	return path