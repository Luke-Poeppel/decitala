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
	"""
	Function for building a "graph". 
	"""
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

def sources_and_sinks(data):
	sources = [x for x in data if not any(y["onset_range"][1] <= x["onset_range"][0] for y in data)]
	sinks = [x for x in data if not any(x["onset_range"][1] <= y["onset_range"][0] for y in data)]

	return sources, sinks

def best_source_and_sink(data):
	sources, sinks = sources_and_sinks(data)
	curr_best_source = sources[0]
	curr_best_sink = sinks[0]

	if len(sources) == 1:
		pass
	else:
		lowest_point = min(sources, key=lambda x: x["onset_range"][0])["onset_range"][0]
		for source in sources:
			if source["onset_range"][0] == lowest_point:
				if source["fragment"].num_onsets > curr_best_source["fragment"].num_onsets:
					curr_best_source = source
			else:
				continue

	if len(sinks) == 1:
		pass
	else:
		for sink in sinks:
			if sink["fragment"].num_onsets > curr_best_sink["fragment"].num_onsets:
				curr_best_sink = sink
			else:
				continue

	return curr_best_source, curr_best_sink