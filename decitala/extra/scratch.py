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
)

def test_single_transcription(transcription):
	print(f'testing {transcription}')
	# all_results = search.rolling_hash_search(
	# 	filepath=transcription.filepath,
	# 	part_num=0,
	# 	table=hash_table.GreekFootHashTable(),
	# 	allow_subdivision=True
	# )
	for point in path_finding_utils.make_3D_grid(resolution=0.1):
		cost = path_finding_utils.CostFunction3D(
			gap_weight=point[0],
			onset_weight=point[1],
			articulation_weight=point[2]
		)
		path = search.path_finder(
			filepath=transcription.filepath,
			part_num=0,
			table=hash_table.GreekFootHashTable(),
			allow_subdivision=True,
			cost_function_class=cost
		)
		accuracy = path_finding_utils.check_accuracy(
			training_data=transcription.analysis,
			calculated_data=path,
			mode="Transcriptions"
		)
		print(f"{point} -> {accuracy}")
	return


ex5 = Transcription("Ex5")
print(ex5.analysis)
print(test_single_transcription(ex5))

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
	print("ACCURACY", path_finding_utils.check_accuracy(
		training_data=transcription.analysis,
		calculated_data=path,
		mode="Transcriptions"
	))
	for x in path:
		print(x.fragment, x.onset_range, x.is_spanned_by_slur, x.pitch_content, x.mod_hierarchy_val)


# ex2 = Transcription("Ex2")
# print(ex2.analysis)
# print(test(ex2))