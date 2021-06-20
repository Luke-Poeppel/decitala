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
		cost = path_finding_utils.CostFunction3D(
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
			print(point)
			for x in path:
				print(x.fragment, x.onset_range)
			print()
	return good / count


ex1 = Transcription("Ex3")
print(test_cost_function(ex1))