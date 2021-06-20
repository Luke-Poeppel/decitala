from moiseaux.db import (
	Transcription
)

from decitala import (
	fragment,
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

		if source.fragment.name == "Peon_IV" and sink.fragment.name == "Iamb":
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

def test(transcription):
	cost = path_finding_utils.CostFunction3D(
		gap_weight=0.4,
		onset_weight=0.3,
		articulation_weight=0.3
	)
	all_results = search.rolling_hash_search(
		filepath=transcription.filepath,
		part_num=0,
		table=hash_table.GreekFootHashTable(),
		allow_subdivision=True
	)
	path = search.path_finder(
		filepath=transcription.filepath,
		part_num=0,
		table=hash_table.GreekFootHashTable(),
		allow_subdivision=True,
		cost_function_class=cost
	)
	path = path_finding_utils.split_extractions(
		data=path,
		split_dict={
			fragment.GreekFoot("Diiamb"): [fragment.GreekFoot("Iamb"), fragment.GreekFoot("Iamb")]
		},
		all_res=all_results
	)
	print(path_finding_utils.check_accuracy(
		training_data=transcription.analysis,
		calculated_data=path,
		mode="Transcriptions"
	))
	for x in path:
		print(x.fragment, x.onset_range, x.is_spanned_by_slur, x.pitch_content, x.mod_hierarchy_val)


ex2 = Transcription("Ex2")
print(ex2.analysis)
print(test(ex2))