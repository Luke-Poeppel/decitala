####################################################################################################
# File:     hyperparameters.py
# Purpose:  Functions for calculating intial hyperparameters for the CF3D.
#
# Author:   Luke Poeppel
#
# Location: Kent, 2021 / NYC, 2021.
####################################################################################################
import json
import matplotlib.pyplot as plt
import matplotlib as mpl

from tqdm import tqdm
from datetime import datetime

from decitala import (
	search,
	hash_table,
	utils,
)
from decitala.database.db import (
	get_all_transcriptions
)
from decitala.path_finding import (
	path_finding_utils,
)

mpl.rcParams.update(mpl.rcParamsDefault)

sept_haikai_path = "/Users/lukepoeppel/Messiaen/Encodings/Sept_Haikai/1_Introduction.xml"
liturgie_path = "/Users/lukepoeppel/Messiaen/Encodings/Messiaen_Qt/Messiaen_I_Liturgie/Messiaen_I_Liturgie_de_cristal_CORRECTED.xml" # noqa
livre_dorgue_path = "/Users/lukepoeppel/Messiaen/Encodings/Livre_d\'Orgue/V_Piece_En_Trio_Corrected.xml" # noqa

compositions = {
	"sept_haikai_0": {
		"filepath": sept_haikai_path,
		"part_num": 0,
		"annotation": utils.loader("/Users/lukepoeppel/decitala/databases/analyses/sept_haïkaï_0_analysis.json") # noqa
	},
	"sept_haikai_1": {
		"filepath": sept_haikai_path,
		"part_num": 1,
		"annotation": utils.loader("/Users/lukepoeppel/decitala/databases/analyses/sept_haïkaï_1_analysis.json") # noqa
	},
	"liturgie": {
		"filepath": liturgie_path,
		"part_num": 3,
		"annotation": utils.loader("/Users/lukepoeppel/decitala/databases/analyses/liturgie_3-4_analysis.json") # noqa
	},
	"livre_dorgue_0": {
		"filepath": livre_dorgue_path,
		"part_num": 0,
		"annotation": utils.loader("/Users/lukepoeppel/decitala/databases/analyses/livre_dorgue_0_analysis.json") # noqa
	},
	"livre_dorgue_1": {
		"filepath": livre_dorgue_path,
		"part_num": 1,
		"annotation": utils.loader("/Users/lukepoeppel/decitala/databases/analyses/livre_dorgue_1_analysis.json") # noqa
	},
}

logger = utils.get_logger(name=__file__, print_to_console=False)
ALLOW_TRANSCRIPTION_SUBDIVISION = False
ALLOW_COMPOSITION_SUBDIVISION = True
ENFORCE_EARLIEST_START = True

def test_single_transcription(transcription, point, verbose=False, show_fragments=False):
	"""Calculates accuracy of a point for a single transcription."""
	cost = path_finding_utils.CostFunction3D(
		gap_weight=point[0],
		onset_weight=point[1],
		articulation_weight=point[2]
	)
	path = search.path_finder(
		filepath=transcription.filepath,
		part_num=0,
		table=hash_table.GreekFootHashTable(),
		allow_subdivision=ALLOW_TRANSCRIPTION_SUBDIVISION,
		cost_function_class=cost,
		split_dict=path_finding_utils.default_split_dict(),
		enforce_earliest_start=ENFORCE_EARLIEST_START,
		verbose=verbose
	)
	if show_fragments:
		for x in path:
			logger.info(x.fragment, x.onset_range, x.is_spanned_by_slur, x.pitch_content, x.mod_hierarchy_val) # noqa
		print()

	return path_finding_utils.check_accuracy(
		training_data=transcription.analysis,
		calculated_data=path,
		mode="Transcriptions",
		return_list=True
	)

def test_single_work(work, point, verbose=False, show_fragments=False):
	"""Calculates accuracy of a point for a single part in a composition. Uses DHT."""
	cost = path_finding_utils.CostFunction3D(
		gap_weight=point[0],
		onset_weight=point[1],
		articulation_weight=point[2]
	)
	path = search.path_finder(
		filepath=compositions[work]["filepath"],
		part_num=compositions[work]["part_num"],
		table=hash_table.DecitalaHashTable(),
		allow_subdivision=ALLOW_COMPOSITION_SUBDIVISION,
		cost_function_class=cost,
		split_dict=path_finding_utils.default_split_dict(),
		enforce_earliest_start=ENFORCE_EARLIEST_START,
		verbose=verbose
	)
	if show_fragments:
		for x in path:
			logger.info(x.fragment, x.onset_range, x.is_spanned_by_slur, x.pitch_content, x.mod_hierarchy_val) # noqa
		print()

	return path_finding_utils.check_accuracy(
		training_data=compositions[work]["annotation"],
		calculated_data=path,
		mode="Compositions",
		return_list=True
	)

# print(test_single_work("livre_dorgue_0", point=[0.8, 0.1, 0.1]))

def test_all_transcriptions_on_single_point(point):
	"""Calculates accuracy for single input point."""
	total = 0
	correct = 0
	for transcription in tqdm(get_all_transcriptions()):
		if transcription.analysis:
			logger.info(transcription)
			res = test_single_transcription(
				transcription=transcription,
				point=point,
				show_fragments=False,
				verbose=False
			)
			logger.info(res)
			correct += res[0]
			total += res[1]

	return (correct, total, correct / total)

# print(test_all_transcriptions_on_single_point([0.89, 0.02, 0.09]))#019]))

def test_all_works_on_single_point(point):
	"""Calculates accuracy for single input point."""
	total = 0
	correct = 0
	for work, data in tqdm(compositions.items()):
		logger.info(work)
		res = test_single_work(
			work=work,
			point=point,
			show_fragments=False,
			verbose=False
		)
		logger.info(res)
		correct += res[0]
		total += res[1]

	return (correct, total, correct / total)

# print(test_all_works_on_single_point([0.8, 0.1, 0.1]))

def test_all_points_transcriptions(resolution):
	date = datetime.today().strftime("%m-%d-%Y")
	out = dict()
	for point in path_finding_utils.make_3D_grid(resolution=resolution):
		print(point)
		res = []
		transcription_results = test_all_transcriptions_on_single_point(point)
		res.extend(transcription_results)
		out[str(point)] = res

	filepath = f"/Users/lukepoeppel/decitala/decitala/extra/{date}_transcription_hyperparameters_{resolution}.json" # noqa
	with open(filepath, "w") as fp:
		json.dump(obj=out, fp=fp, ensure_ascii=False, indent=4)
	return

# test_all_points_transcriptions(resolution=0.05)

def test_all_points_works(resolution):
	date = datetime.today().strftime("%m-%d-%Y")
	out = dict()
	for point in path_finding_utils.make_3D_grid(resolution=resolution):
		print(point)
		res = []
		composition_results = test_all_works_on_single_point(point)
		res.extend(composition_results)
		out[str(point)] = res

	filepath = f"/Users/lukepoeppel/decitala/decitala/extra/{date}_works_hyperparameters_{resolution}.json" # noqa
	with open(filepath, "w") as fp:
		json.dump(obj=out, fp=fp, ensure_ascii=False, indent=4)
	return

# test_all_points_works(resolution=0.05)

####################################################################################################
# Plotting results
latest_transcription_data = "/Users/lukepoeppel/decitala/decitala/extra/07-05-2021_transcription_hyperparameters_0.05.json" # noqa
latest_composition_data = "/Users/lukepoeppel/decitala/decitala/extra/07-05-2021_works_hyperparameters_0.05.json" # noqa

def point_accuracy(filepath, point):
	loaded = utils.loader(filepath)
	results = None
	for p, results in loaded.items():
		loaded_point = json.loads(p)
		if loaded_point == point:
			results = loaded[str(loaded_point)]
			break

	return results[-1]  # = correct / total

# print(point_accuracy(latest_composition_data, point=[0.8, 0.1, 0.1]))

def plot_3D_points(
		transcription_results,
		composition_results,
		show=False,
		save_path=None
	):
	fig = plt.figure() # noqa
	ax = plt.axes(projection="3d")

	ax.set_title(
		"Dijkstra Algorithm Accuracy for Annotated Transcriptions and Compositions \n 3D Cost Function",
		fontname="Times",
		fontsize=14
	)
	ax.set_xlabel("Gap Weight", fontname="Times", fontsize=12)
	ax.set_ylabel("Onset Weight", fontname="Times", fontsize=12)
	ax.set_zlabel("Accuracy (%)", fontname="Times", fontsize=12)

	# Plot transcription and point data
	for i, point in enumerate(path_finding_utils.make_3D_grid(resolution=0.1)):
		acc_transcription = point_accuracy(
			filepath=transcription_results,
			point=point
		)
		acc_composition = point_accuracy(
			filepath=composition_results,
			point=point
		)
		if i == 0:
			ax.scatter(point[0], point[1], acc_transcription, c="k", s=8, label="Transcriptions (n=103)")
			ax.scatter(point[0], point[1], acc_composition, c="r", s=8, label="Compositions (n=5)")
		else:
			ax.scatter(point[0], point[1], acc_transcription, c="k", s=8)
			ax.scatter(point[0], point[1], acc_composition, c="r", s=8)

	ax.view_init(azim=-125, elev=15)

	plt.legend(prop="Times")

	if save_path:
		plt.savefig(save_path, dpi=350)

# plot_3D_points(
# 	transcription_results=latest_transcription_data,
# 	composition_results=latest_composition_data,
# 	show=False,
# 	save_path="/Users/lukepoeppel/Messiaen/ODNC_Analysis/ODNC_A/figures/figure_5/3D_accuracy.png"
# )