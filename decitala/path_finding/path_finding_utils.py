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
class CostFunction:
	"""
	Arbitrary cost function to use in the cost functions. The user should set weights as class
	attributes that are referenced in the cost function (which the user must override), if needed.
	If set, the weights should (probably) sum to 1.

	The following is a cost function that doesn't rely on any weights.
	>>> class MyFirstCostFunction(CostFunction):
	>>> 	def cost(self, vertex_a, vertex_b):
	>>> 		'''Cost function determined by the sum of the two extractions standard deviations.'''
	>>> 		return vertex_a.std() + vertex_b.std()

	The following is a cost function that relies on three weights summing to 1.
	>>> class MySecondCostFunction(CostFunction):
	>>> 	weight_a = 0.4213
	>>> 	weight_b = 0.2599
	>>> 	weight_c = 0.3188
	>>> 	def cost(self, vertex_a, vertex_b):
	>>> 		'''Cost function determined by the sum of the two extractions standard deviations.'''
	>>> 		first_term = ((weight_a * vertex_a.num_onsets) + weight_b)
	>>> 		second_term = ((weight_a * vertex_b.num_onsets) + weight_b)
	>>> 		return first_term + second_term
	"""
	def cost(self, vertex_a, vertex_b):
		"""
		This function must be overrided by child classes. Cost function between two
		:obj:`decitala.search.Extraction`: objects.

		:param :obj:`decitala.search.Extraction` vertex_1: An extraction object from a composition.
		:param :obj:`decitala.search.Extraction` vertex_2: A second extraction object from a composition.
		:return: The cost of moving from ``vertex_1`` to ``vertex_2``.
		:rtype: float
		"""
		raise NotImplementedError

class DefaultCostFunction(CostFunction):
	"""
	Default cost function used in the path-finding algorithms. Weights optimized by
	hyperparameter search.
	"""
	gap_weight = 0.75
	onset_weight = 0.25

	def cost(self, vertex_1, vertex_2):
		gap = vertex_2.onset_range[0] - vertex_1.onset_range[1]
		onsets = 1 / (vertex_1.fragment.num_onsets + vertex_2.fragment.num_onsets)
		cost = (self.gap_weight * gap) + (self.onset_weight * onsets)
		return cost

def cost(
		vertex_1,
		vertex_2,
		weights
	):
	"""
	Cost function used in the path finding algorithms.


	"""
	gap = vertex_2.onset_range[0] - vertex_1.onset_range[1]
	onsets = 1 / (vertex_1.fragment.num_onsets + vertex_2.fragment.num_onsets)
	cost = (weights["gap"] * gap) + (weights["onsets"] * onsets)
	return cost

def build_graph(data, weights):
	"""
	Function for building a "graph" of nodes and edges from a given set of data (each
	vertex of the form as those required in the cost function) extracted from one of the
	search algorithms. Requires ``id`` keys in each dictionary input.

	:param dict weights: weights used in the model. Must sum to 1. Requires "gap" and "onsets" values.
	:return: A "graph" holding vertices and the associated cost between all other non-negative edges.
	:rtype: dict
	"""
	G = {}
	i = 0
	while i < len(data):
		curr = data[i]
		curr_edges = []
		for other in data:
			if other == curr:
				continue

			# Check here, not `cost()`, as then we don't need to instantiate a fragment object.
			elif curr.onset_range[1] > other.onset_range[0]:
				continue

			edge = cost(curr, other, weights)
			if edge < 0:  # Just in case.
				continue

			curr_edges.append((other.id_, edge))

		G[curr.id_] = curr_edges
		i += 1

	return G

def sources_and_sinks(data):
	"""
	Calculates all sources and sinks in a given dataset.
	"""
	sources = [x for x in data if not any(y.onset_range[1] <= x.onset_range[0] for y in data)]
	sinks = [x for x in data if not any(x.onset_range[1] <= y.onset_range[0] for y in data)]

	return sources, sinks

def best_source_and_sink(data):
	"""
	Calculates the "best" source and sink from a dataset based on two simple heuristics: (1) the
	fragment with the earliest (or latest, for sink) starting point, (2) the fragment with the
	greatest number of onsets.
	"""
	sources, sinks = sources_and_sinks(data)
	curr_best_source = sources[0]
	curr_best_sink = sinks[0]

	if len(sources) == 1:
		pass
	else:
		lowest_point = min(sources, key=lambda x: x.onset_range[0]).onset_range[0]
		for source in sources:
			if source.onset_range[0] == lowest_point:
				if source.fragment.num_onsets > curr_best_source.fragment.num_onsets:
					curr_best_source = source
			else:
				continue

	if len(sinks) == 1:
		pass
	else:
		for sink in sinks:
			if sink.fragment.num_onsets > curr_best_sink.fragment.num_onsets:
				curr_best_sink = sink
			else:
				continue

	return curr_best_source, curr_best_sink