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
import numpy as np

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
	for transcription in get_all_transcriptions():
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

# print(test_all_transcriptions_on_single_point([0.8, 0.1, 0.1]))

def test_all_works_on_single_point(point):
	"""Calculates accuracy for single input point."""
	total = 0
	correct = 0
	for work, data in compositions.items():
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

def test_all_points_transcriptions(resolution=0.1):
	date = datetime.today().strftime("%m-%d-%Y")
	ALL_RES = dict()
	for transcription in get_all_transcriptions():
		if transcription.analysis:
			transcription_results = dict()
			print(transcription)
			for point in path_finding_utils.make_3D_grid(resolution=resolution):
				result = test_single_transcription(transcription, point=point)
				print(result)
				transcription_results[str(point)] = str(result)

			ALL_RES[transcription.name] = transcription_results

	filepath = f"/Users/lukepoeppel/decitala/decitala/extra/{date}_transcription_hyperparameters_{resolution}_greek_foot_4.json" # noqa
	with open(filepath, "w") as fp:
		json.dump(obj=ALL_RES, fp=fp, ensure_ascii=False, indent=4)
	return

def test_all_points_works(resolution=0.1):
	date = datetime.today().strftime("%m-%d-%Y")
	ALL_RES = dict()
	for work in compositions:
		results = dict()
		logger.info(work)
		for point in path_finding_utils.make_3D_grid(resolution=resolution):
			result = test_single_work(work, point=point)
			logger.info(result)
			results[str(point)] = str(result)

		ALL_RES[work] = results

	filepath = f"/Users/lukepoeppel/decitala/decitala/extra/{date}_composition_hyperparameters_{resolution}_greek_foot_4.json" # noqa
	with open(filepath, "w") as fp:
		json.dump(obj=ALL_RES, fp=fp, ensure_ascii=False, indent=4)
	return

# print(test_all_points_works())

####################################################################################################
# Plotting results
latest = "/Users/lukepoeppel/decitala/decitala/extra/06-25-2021_transcription_hyperparameters_0.1_greek_foot_4.json" # noqa

def point_accuracy(filepath, point_in):
	loaded = utils.loader(filepath)
	results = []
	for work in loaded.keys():
		points = loaded[work]
		for point in points.keys():
			if json.loads(point) == point_in:
				results.append(json.loads(points[point]))

	total = sum([x[1] for x in results])
	correct = sum([x[0] for x in results])
	return correct / total

def plot_3D_points(filepath, save_path=None):
	"""
	Each points should looks like [(x, y, z), res].
	"""
	fig = plt.figure() # noqa
	ax = plt.axes(projection="3d")

	ax.set_title(
		"Accuracy From Dijkstra Algorithm for Annotated Transcriptions \n (3D Cost Function)",
		fontname="Times",
		fontsize=14
	)
	ax.set_xlabel("Gap Weight", fontname="Times", fontsize=12)
	ax.set_ylabel("Onset Weight", fontname="Times", fontsize=12)
	ax.set_zlabel("Accuracy (%)", fontname="Times", fontsize=12)

	# Dumb, but it's ok. :-)
	max_acc = 0
	max_acc_point = None
	for p in path_finding_utils.make_3D_grid(resolution=0.1):
		acc = point_accuracy(
			filepath=filepath,
			point_in=p,
		)
		if acc > max_acc:
			max_acc = acc
			max_acc_point = p

	for point in path_finding_utils.make_3D_grid(resolution=0.1):
		acc = point_accuracy(
			filepath=filepath,
			point_in=point,
		)
		if point == max_acc_point:
			ax.scatter(max_acc_point[0], max_acc_point[1], max_acc, c="r", marker="X")
		else:
			ax.scatter(point[0], point[1], acc, c="k", s=8)

	ax.set_zlim(0, 0.8)
	x = np.linspace(max_acc_point[0], max_acc_point[0], 50)
	y = np.linspace(max_acc_point[1], max_acc_point[1], 50)
	z = np.linspace(0, 0.75, 50)
	ax.plot(x, y, z)

	ax.text(
		max_acc_point[0],
		max_acc_point[1],
		max_acc + 0.05,
		str(round(max_acc, 4)),
		color="red",
		fontdict={"family": "Times"}
	)

	ax.view_init(azim=-145, elev=15)

	if save_path:
		plt.savefig(save_path, dpi=350)

	plt.show()

# plot_3D_points(latest, "/Users/lukepoeppel/decitala/decitala/extra/3D_results_74.71.png")