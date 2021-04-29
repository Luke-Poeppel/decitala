# -*- coding: utf-8 -*-
####################################################################################################
# File:     path_finding_utils.py
# Purpose:  Path finding utility functions used in the various algorithms. Includes the main cost
#           function used as the metric on the graphs. 
#
# Author:   Luke Poeppel
#
# Location: NYC, 2021
####################################################################################################
def cost(
		vertex_1,
		vertex_2,
		weights
	):
	"""
	Cost function used in the path finding algorithms. 

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

def build_graph(data, weights):
	G = {}
	i = 0
	while i < len(data):
		curr = data[i]
		curr_edges = []
		for other in data:
			if other == curr:
				continue
			edge = cost(curr, other, weights)
			if edge < 0:
				continue
			
			curr_edges.append((other["id"], edge))

		G[curr["id"]] = curr_edges
		i += 1

	return G