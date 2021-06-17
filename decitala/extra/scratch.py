from moiseaux.db import (
	Transcription
)

from decitala import (
	search,
	hash_table,
)
from decitala.path_finding import (
	path_finding_utils,
	dijkstra
)

class ScratchCost(path_finding_utils.CostFunction):
	def __init__(
			self,
			reuse_weight,
			onset_weight,
			gap_weight
		):
		self.reuse_weight = reuse_weight
		self.onset_weight = onset_weight
		self.gap_weight = gap_weight

	def cost(self, vertex_a, vertex_b):
		reuse = 0
		if vertex_a.fragment != vertex_b.fragment:
			reuse = vertex_a.fragment.num_onsets

		onsets = 1 / (vertex_a.fragment.num_onsets + vertex_b.fragment.num_onsets)
		gap = vertex_b.onset_range[0] - vertex_a.onset_range[1]

		cost = (self.reuse_weight * reuse) + (self.onset_weight * onsets) + (self.gap_weight * gap)
		return cost

def test_3D_cost_function(transcription):
	print(f'testing {transcription}')
	all_results = search.rolling_hash_search(
		filepath=transcription.filepath,
		part_num=0,
		table=hash_table.GreekFootHashTable(),
		allow_subdivision=True
	)
	for point in path_finding_utils.make_3D_grid(resolution=0.1):
		print()
		print(point)
		cost = ScratchCost(
			reuse_weight=point[0],
			onset_weight=point[1],
			gap_weight=point[2]
		)
		source, sink, mat = dijkstra.dijkstra_best_source_and_sink(
			data=all_results,
			cost_function_class=cost
		)
		print(source.fragment)
		print(sink.fragment)
		print('paff')
		path = search.path_finder(
			filepath=transcription.filepath,
			part_num=0,
			table=hash_table.GreekFootHashTable(),
			allow_subdivision=True,
			cost_function_class=cost
		)
		for x in path:
			print(x.fragment, x.onset_range)


ex24 = Transcription("Ex24")

# # test_3D_cost_function(ex24)