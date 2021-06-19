# from moiseaux.db import (
# 	Transcription
# )

# from decitala import (
# 	search,
# 	hash_table,
# 	fragment
# )
# from decitala.path_finding import (
# 	path_finding_utils,
# 	dijkstra
# )

# class ScratchCost(path_finding_utils.CostFunction):
# 	def __init__(
# 			self,
# 			reuse_weight,
# 			onset_weight,
# 			gap_weight
# 		):
# 		self.reuse_weight = reuse_weight
# 		self.onset_weight = onset_weight
# 		self.gap_weight = gap_weight

# 	def cost(self, vertex_a, vertex_b):
# 		reuse = 0
# 		if vertex_a.fragment != vertex_b.fragment:
# 			reuse = vertex_a.fragment.num_onsets

# 		onsets = 1 / (vertex_a.fragment.num_onsets + vertex_b.fragment.num_onsets)
# 		gap = vertex_b.onset_range[0] - vertex_a.onset_range[1]

# 		cost = (self.reuse_weight * reuse) + (self.onset_weight * onsets) + (self.gap_weight * gap)
# 		return cost

# class ScratchCost4D(path_finding_utils.CostFunction):
# 	def __init__(
# 			self,
# 			reuse_weight,
# 			#onset_weight,
# 			gap_weight,
# 			articulation_weight
# 		):
# 		self.reuse_weight = reuse_weight
# 		#self.onset_weight = onset_weight
# 		self.gap_weight = gap_weight
# 		self.articulation_weight = articulation_weight

# 	def cost(self, vertex_a, vertex_b):
# 		reuse = 0
# 		if vertex_a.fragment != vertex_b.fragment:
# 			reuse = vertex_a.fragment.num_onsets

# 		#onsets = 1 / (vertex_a.fragment.num_onsets + vertex_b.fragment.num_onsets)
# 		gap = vertex_b.onset_range[0] - vertex_a.onset_range[1]

# 		articulated_sum = int(vertex_a.is_spanned_by_slur) + int(vertex_b.is_spanned_by_slur)
# 		if articulated_sum == 0:
# 			articulation = vertex_a.fragment.num_onsets + vertex_b.fragment.num_onsets
# 		else:
# 			articulation = 1 / articulated_sum

# 		cost = (self.reuse_weight * reuse) + (self.gap_weight * gap) +
# (self.articulation_weight * articulation)
# # (self.onset_weight * onsets) +
# 		return cost

# def test_4D_cost_function(transcription):
# 	print(f'testing {transcription}')
# 	all_results = search.rolling_hash_search(
# 		filepath=transcription.filepath,
# 		part_num=0,
# 		table=hash_table.GreekFootHashTable(),
# 		allow_subdivision=True
# 	)
# 	count = 0
# 	good = 0
# 	for point in path_finding_utils.make_3D_grid(resolution=0.1):
# 		count += 1

# 		print()
# 		print(point)
# 		cost = ScratchCost4D(
# 			reuse_weight=point[0],
# 			#onset_weight=point[1],
# 			gap_weight=point[1],
# 			articulation_weight=point[2]
# 		)
# 		source, sink, mat = dijkstra.dijkstra_best_source_and_sink(
# 			data=all_results,
# 			cost_function_class=cost
# 		)

# 		if source.fragment.name == "Peon_IV" and sink.fragment.name == "Iamb":
# 			good += 1

# 		print('paff')
# 		path = search.path_finder(
# 			filepath=transcription.filepath,
# 			part_num=0,
# 			table=hash_table.GreekFootHashTable(),
# 			allow_subdivision=True,
# 			cost_function_class=cost
# 		)
# 		for x in path:
# 			print(x.fragment, x.onset_range)

# 	print(good, count)

# ex1 = Transcription("Ex1")
# test_4D_cost_function(ex1)

# all_results = search.rolling_hash_search(
# 	filepath=ex1.filepath,
# 	part_num=0,
# 	table=hash_table.GreekFootHashTable(),
# 	allow_subdivision=True
# )
# for point in path_finding_utils.make_3D_grid(resolution=0.1):

# iambs = []
# for x in all_results:
# 	if x.fragment == fragment.GreekFoot("Iamb") and x.is_spanned_by_slur:
# 		iambs.append(x)

# for point in path_finding_utils.make_3D_grid(resolution=0.1):
# 	print(point)
# 	cost = ScratchCost(
# 		reuse_weight=point[0],
# 		onset_weight=point[1],
# 		gap_weight=point[2]
# 	)
# 	print(cost.cost(vertex_a=iambs[0], vertex_b=iambs[1]))