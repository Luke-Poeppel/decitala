from moiseaux.db import (
	Transcription,
	get_all_transcriptions
)

from decitala import (
	search,
	hash_table,
	utils,
)
from decitala.path_finding import (
	path_finding_utils,
)

import json

from datetime import datetime

def test_single_transcription(transcription, point):
	cost = path_finding_utils.CostFunction3D(
		gap_weight=point[0],
		onset_weight=point[1],
		articulation_weight=point[2]
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
		cost_function_class=cost,
		verbose=True
	)
	path = path_finding_utils.split_extractions(
		data=path,
		split_dict=path_finding_utils.default_split_dict(),
		all_res=all_results
	)
	# for x in path:
	# 	print(x.fragment, x.onset_range, x.is_spanned_by_slur, x.pitch_content, x.mod_hierarchy_val, x.slur_count) # noqa
	# print()

	return path_finding_utils.check_accuracy(
		training_data=transcription.analysis,
		calculated_data=path,
		mode="Transcriptions",
		return_list=True
	)


ex = Transcription("Ex114")

# print(ex.analysis)
# ex.show()
# print()
print(test_single_transcription(ex, point=(0.4, 0.3, 0.3)))
# # # print()
# for point in path_finding_utils.make_3D_grid(resolution=0.1):
# 	print(test_single_transcription(ex, point=point))  #  (0.4, 0.3, 0.3)))

def test_all(resolution=0.1):
	date = datetime.today().strftime("%m-%d-%Y")
	ALL_RES = dict()
	for transcription in get_all_transcriptions():
		if transcription.name == "Ex114":
			continue
		if transcription.analysis:
			transcription_results = dict()
			print(transcription)
			for point in path_finding_utils.make_3D_grid(resolution=resolution):
				result = test_single_transcription(transcription, point=point)
				print(result)
				transcription_results[str(point)] = str(result)

			ALL_RES[transcription.name] = transcription_results

	filepath = f"/Users/lukepoeppel/decitala/decitala/extra/{date}_transcription_hyperparameters_{resolution}_greek_foot_3.json" # noqa
	with open(filepath, "w") as fp:
		json.dump(obj=ALL_RES, fp=fp, ensure_ascii=False, indent=4)
	return

# print(test_all())

def point_accuracy(filepath, point_in, ignore_works):
	loaded = utils.loader(filepath)
	results = []
	for work in loaded.keys():
		if work in ignore_works:
			continue
		points = loaded[work]
		for point in points.keys():
			if json.loads(point) == point_in:
				results.append(json.loads(points[point]))

	total = sum([x[1] for x in results])
	correct = sum([x[0] for x in results])
	return correct / total

# for point in path_finding_utils.make_3D_grid(resolution=0.1):
# 	acc = point_accuracy(
# 		filepath="/Users/lukepoeppel/decitala/decitala/extra/06-21-2021_transcription_hyperparameters_0.1_greek_foot_2.json",
# 		point_in=point,
# 		ignore_works=["Ex106"]
# 	)
# 	print(point, acc)


# ex108 = Transcription("Ex114")
# analysis = ex108.analysis
# for x in analysis:
# 	print(x)
# vis.annotate_score(analysis, ex108.filepath, 0, transcription_mode=True).show()