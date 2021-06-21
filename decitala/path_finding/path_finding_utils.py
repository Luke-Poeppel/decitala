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
import numpy as np

from tqdm import tqdm

from ..fragment import GreekFoot

class CostFunction:
	"""
	Arbitrary cost function to use in the cost functions. The user should set weights as class
	attributes that are referenced in the cost function (which the user must override), if needed.
	If set, the weights should (probably) sum to 1.

	The following is a cost function that doesn't rely on any weights.

	>>> class MyFirstCostFunction(CostFunction):
	... 	def cost(self, vertex_a, vertex_b):
	... 		'''Cost function determined by the sum of the two extractions standard deviations.'''
	... 		return vertex_a.std() + vertex_b.std()

	The following is a cost function that relies on three weights summing to 1.

	>>> class MySecondCostFunction(CostFunction):
	... 	weight_a = 0.4213
	... 	weight_b = 0.2599
	... 	def cost(self, vertex_a, vertex_b):
	... 		'''Cost function determined by the sum of the two extractions standard deviations.'''
	... 		first_term = ((weight_a * vertex_a.num_onsets) + weight_b)
	... 		second_term = ((weight_a * vertex_b.num_onsets) + weight_b)
	... 		return first_term + second_term
	"""
	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)

	def cost(self, vertex_a, vertex_b):
		"""
		This function must be overrided by child classes. Cost function between two
		:obj:`decitala.search.Extraction` objects.

		:param `decitala.search.Extraction` vertex_1: An extraction object from a composition.
		:param `decitala.search.Extraction` vertex_2: A second extraction object from a composition.
		:return: The cost of moving from ``vertex_1`` to ``vertex_2``.
		:rtype: float
		"""
		raise NotImplementedError

class DefaultCostFunction(CostFunction):
	"""
	Default cost function used in the path-finding algorithms. Weights optimized by
	hyperparameter search.
	"""
	def __init__(self, gap_weight=0.75, onset_weight=0.25):
		self.gap_weight = gap_weight
		self.onset_weight = onset_weight

	def cost(self, vertex_a, vertex_b):
		gap = vertex_b.onset_range[0] - vertex_a.onset_range[1]
		onsets = 1 / (vertex_a.fragment.num_onsets + vertex_b.fragment.num_onsets)
		cost = (self.gap_weight * gap) + (self.onset_weight * onsets)
		return cost

class CostFunction3D(CostFunction):
	def __init__(
			self,
			gap_weight,
			onset_weight,
			articulation_weight,
		):
		self.gap_weight = gap_weight
		self.onset_weight = onset_weight
		self.articulation_weight = articulation_weight

	def cost(self, vertex_a, vertex_b):
		gap = vertex_b.onset_range[0] - vertex_a.onset_range[1]
		onsets = 1 / (vertex_a.fragment.num_onsets + vertex_b.fragment.num_onsets)
		total_slurs = vertex_a.slur_count + vertex_b.slur_count
		if total_slurs == 0:
			slur_val = 1 / 0.5  # force non-zero
		else:
			slur_val = 1 / total_slurs

		values = [gap, onsets, slur_val]
		cost = 0
		for weight, val in zip([self.gap_weight, self.onset_weight, self.articulation_weight], values): # noqa
			cost += weight * val

		return cost

def build_graph(
		data,
		cost_function_class=DefaultCostFunction(),
		verbose=False
	):
	"""
	Function for building a "graph" of nodes and edges from a given set of data (each
	vertex of the form as those required in the cost function) extracted from one of the
	search algorithms. Requires ``id`` keys in each dictionary input.

	:param list data: a list of :obj:`decitala.search.Extraction` objects.
	:param `decitala.path_finding.path_finding_utils.CostFunction` cost_function_class: a cost
		function that will be used in calculating the weights between vertices.
	:return: A "graph" holding vertices and the associated cost between all other non-negative edges.
	:rtype: dict
	"""
	G = {}
	i = 0
	with tqdm(total=len(data), disable=not(verbose)) as bar:
		while i < len(data):
			curr = data[i]
			curr_edges = []
			for other in data:
				if other == curr:
					continue

				# Check here, not in cost function, as then we don't need to instantiate a fragment object.
				elif curr.onset_range[1] > other.onset_range[0]:
					continue

				edge = cost_function_class.cost(vertex_a=curr, vertex_b=other)
				if edge < 0:  # Just in case. Dijkstra edges must be negative.
					continue

				curr_edges.append((other.id_, edge))

			G[curr.id_] = curr_edges
			bar.update(1)
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
	TODO: this is bad. I should be using the agnostic approach of Dijkstra here.

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

def make_2D_grid(resolution):
	"""
	Function for generating a grid of two numbers that sum to 1, iterated over the given resolution.

	:param float resolution: resolution of the grid, :math:`0 < x <= 1`.
	"""
	spaces = []
	for i in range(2):
		parameter_space = np.array([round(x, 3) for x in np.linspace(0, 1, int(1 / resolution) + 1)])
		spaces.append(parameter_space)

	combos = []
	for param_a in spaces[0]:
		for param_b in spaces[1]:
			collection = [param_a, param_b]
			if sum(collection) == 1.0:
				combos.append(collection)

	return combos

def make_3D_grid(resolution):
	"""
	Function for generating a grid of three numbers that sum to 1, iterated over the given resolution.

	:param float resolution: resolution of the grid, :math:`0 < x <= 1`.
	"""
	spaces = []
	for i in range(3):
		parameter_space = np.array([round(x, 3) for x in np.linspace(0, 1, int(1 / resolution) + 1)])
		spaces.append(parameter_space)

	combos = []
	for param_a in spaces[0]:
		for param_b in spaces[1]:
			for param_c in spaces[2]:
				collection = [param_a, param_b, param_c]
				if sum(collection) == 1.0:
					combos.append(collection)

	return combos

def make_4D_grid(resolution):
	"""
	Function for generating a grid of four numbers that sum to 1, iterated over the given resolution.

	:param float resolution: resolution of the grid, :math:`0 < x <= 1`.
	"""
	spaces = []
	for i in range(4):
		parameter_space = np.array([round(x, 3) for x in np.linspace(0, 1, int(1 / resolution) + 1)])
		spaces.append(parameter_space)

	combos = []
	for param_a in spaces[0]:
		for param_b in spaces[1]:
			for param_c in spaces[2]:
				for param_d in spaces[3]:
					collection = [param_a, param_b, param_c, param_d]
					if sum(collection) == 1.0:
						combos.append(collection)

	return combos

def split_extractions(data, split_dict, all_res):
	split_extractions = []
	for extraction in data:
		if extraction.fragment in split_dict:
			components = extraction.split(split_dict=split_dict, all_res=all_res)
			split_extractions.extend(components)
		else:
			split_extractions.append(extraction)
	return split_extractions

def default_split_dict():
	return {
		GreekFoot("Diiamb"): [GreekFoot("Iamb"), GreekFoot("Iamb")],
		GreekFoot("Triiamb"): [GreekFoot("Iamb"), GreekFoot("Iamb"), GreekFoot("Iamb")],
		GreekFoot("Dicretic"): [GreekFoot("Amphimacer"), GreekFoot("Amphimacer")],
		GreekFoot("Tritrochee"): [GreekFoot("Trochee"), GreekFoot("Trochee"), GreekFoot("Trochee")],
		GreekFoot("Dianapest"): [GreekFoot("Anapest"), GreekFoot("Anapest")]
	}

def check_accuracy(training_data, calculated_data, mode, return_list):
	"""
	The `training_data` is the analysis as provided by Messiean. The `input_data`
	is the data calculated by path-finding.

	NOTE: the data is stored in two different formats, hence the use of `mode`. This will
	(hopefully) be fixed in the future.
	"""
	accurate = 0
	for this_training_fragment in training_data:
		for this_fragment in calculated_data:
			if mode == "Compositions":
				if (this_training_fragment["fragment"] == this_fragment.fragment) and (tuple(this_training_fragment["onset_range"]) == this_fragment.onset_range): # noqa
					accurate += 1
			elif mode == "Transcriptions":
				if (this_training_fragment[0] == this_fragment.fragment) and (tuple(this_training_fragment[1]) == this_fragment.onset_range): # noqa
					accurate += 1

	if not(return_list):
		return (accurate / len(training_data)) * 100
	else:
		return [accurate, len(training_data)]