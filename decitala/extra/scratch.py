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

def test_cost_function(transcription):
	print(f'testing {transcription}')
	all_results = search.rolling_hash_search(
		filepath=transcription.filepath,
		part_num=0,
		table=hash_table.GreekFootHashTable(),
		allow_subdivision=True
	)
	count = 0
	good = 0
	for point in path_finding_utils.make_3D_grid(resolution=0.1):
		count += 1
		cost = ScratchCost(
			gap_weight=point[0],
			onset_weight=point[1],
			articulation_weight=point[2]
		)
		source, sink, mat = dijkstra.dijkstra_best_source_and_sink(
			data=all_results,
			cost_function_class=cost
		)

		if source.fragment.name == "Peon_IV" and sink.fragment.name == "Diiamb":
			good += 1
			path = search.path_finder(
				filepath=transcription.filepath,
				part_num=0,
				table=hash_table.GreekFootHashTable(),
				allow_subdivision=True,
				cost_function_class=cost
			)
			for x in path:
				print(x.fragment, x.onset_range)
			print()
	return good / count


ex1 = Transcription("Ex1")
print(test_cost_function(ex1))