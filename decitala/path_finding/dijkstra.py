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