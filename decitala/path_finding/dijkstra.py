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

# Got useful info from https://stackoverflow.com/questions/22897209/dijkstras-algorithm-in-python. 
def dijkstra(data, source, target):
	q = []
	d = {k: np.inf for k in data.keys()}
	p = {}

	d[source] = 0 
	heapq.heappush(q, (0, source))

	while q:
		last_w, curr_v = heapq.heappop(q)
		for n, n_w in data[curr_v]:
			cand_w = last_w + n_w
			if cand_w < d[n]:
				d[n] = cand_w
				p[n] = curr_v
				heapq.heappush(q, (cand_w, n))

	return d, p

def generate_path(parents, start, end):
	path = [end]
	while True:
		key = parents[path[0]]
		path.insert(0, key)
		if key == start:
			break
	return path

def dijkstra_first(
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
		
		for other_vertex in vertices:
			other_vertex_index = vertices.index(other_vertex)
			cost = path_finding_utils.cost(curr_vertex, other_vertex, weights=weights)
			if cost <= 0:
				continue

			alt = dist[curr_vertex_index] + cost
			if alt < dist[other_vertex_index]:
				dist[other_vertex_index] = alt
				prev[other_vertex_index] = curr_vertex

		if curr_vertex == target:
			break

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