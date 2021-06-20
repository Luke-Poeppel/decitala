####################################################################################################
# File:     hyperparameters.py
# Purpose:  Script for calculating the best weights (hyperparameter search) for Dijkstra.
#
# Author:   Luke Poeppel
#
# Location: NYC, 2021
####################################################################################################
"""
This file requires private, non-shareable data. I'm storing it here for reference and personal use.
If you run the file with `INTERACTIVE=True`, it'll ask for some inputs and then generate the results
accordingly.
"""
import numpy as np
import json
import matplotlib.pyplot as plt
import matplotlib as mpl

from datetime import datetime

from decitala import (
	search,
	utils,
)
from decitala.path_finding import path_finding_utils
from decitala.fragment import GreekFoot
from decitala.hash_table import (
	GreekFootHashTable,
	DecitalaHashTable,
	AllCorporaHashTable
)

from moiseaux.db import (
	get_all_transcriptions
)

INTERACTIVE = False
mpl.style.use("bmh")

####################################################################################################
# Annotated works.
sept_haikai_path = "/Users/lukepoeppel/Messiaen/Encodings/Sept_Haikai/1_Introduction.xml"
liturgie_path = "/Users/lukepoeppel/Messiaen/Encodings/Messiaen_Qt/Messiaen_I_Liturgie/Messiaen_I_Liturgie_de_cristal_CORRECTED.xml" # noqa
livre_dorgue_path = "/Users/lukepoeppel/Messiaen/Encodings/Livre_d\'Orgue/V_Piece_En_Trio_Corrected.xml" # noqa

compositions = {
	"sept_haikai_0": {
		"filepath": sept_haikai_path,
		"part_num": 0,
		"training_data": utils.loader("/Users/lukepoeppel/decitala/databases/analyses/sept_haïkaï_0_analysis.json") # noqa
	},
	"sept_haikai_1": {
		"filepath": sept_haikai_path,
		"part_num": 1,
		"training_data": utils.loader("/Users/lukepoeppel/decitala/databases/analyses/sept_haïkaï_1_analysis.json") # noqa
	},
	"liturgie": {
		"filepath": liturgie_path,
		"part_num": 3,
		"training_data": utils.loader("/Users/lukepoeppel/decitala/databases/analyses/liturgie_3-4_analysis.json") # noqa
	},
	"livre_dorgue_0": {
		"filepath": livre_dorgue_path,
		"part_num": 0,
		"training_data": utils.loader("/Users/lukepoeppel/decitala/databases/analyses/livre_dorgue_0_analysis.json") # noqa
	},
	"livre_dorgue_1": {
		"filepath": livre_dorgue_path,
		"part_num": 1,
		"training_data": utils.loader("/Users/lukepoeppel/decitala/databases/analyses/livre_dorgue_1_analysis.json") # noqa
	},
}

####################################################################################################
# Running on Compositions
def run_on_all_compositions(
		frag_type,
		resolution,
	):
	date = datetime.today().strftime("%m-%d-%Y")

	logger = utils.get_logger(
		name=__name__,
		print_to_console=True,
	)
	logger.info(f"Running Dijkstra on the Compositions (with the {frag_type} corpus) at a resolution of {resolution}.") # noqa

	if frag_type == "greek_foot":
		hash_table = GreekFootHashTable()
	elif frag_type == "decitala":
		hash_table = DecitalaHashTable()
	elif frag_type == "combined":
		hash_table = AllCorporaHashTable()

	parameter_space = [round(x, 3) for x in np.linspace(0, 1, int(1 / resolution) + 1)]
	all_results = dict()
	for composition, data in compositions.items():
		composition_results = dict()
		logger.info("COMPOSITION={}".format(composition))
		for gap_weight in parameter_space:
			onset_weight = round(1.0 - gap_weight, 3)
			logger.info("\nRunning Dijkstra for ({0}, {1}).".format(gap_weight, onset_weight))
			path = search.path_finder(
				filepath=data["filepath"],
				part_num=data["part_num"],
				table=hash_table,
				allow_subdivision=True,
				weights={"gap": gap_weight, "onsets": onset_weight}
			)

			training_data = data["training_data"]
			accuracy = path_finding_utils.check_accuracy(
				training_data=training_data,
				calculated_data=path,
				mode="Compositions"
			)
			logger.info("{0} -> ({1}, {2}): {3}%".format(composition, gap_weight, onset_weight, accuracy)) # noqa
			composition_results[str((gap_weight, onset_weight))] = accuracy

		all_results[composition] = composition_results

	filepath = f"/Users/lukepoeppel/decitala/decitala/extra/{date}_composition_hyperparameters_{resolution}_{frag_type}.json" # noqa
	with open(filepath, "w") as fp:
		json.dump(obj=all_results, fp=fp, ensure_ascii=False, indent=4)

####################################################################################################
# Running on Transcriptions.
def run_on_all_analyzed_transcriptions(
		frag_type,
		resolution,
	):
	date = datetime.today().strftime("%m-%d-%Y")

	logger = utils.get_logger(
		name=__name__,
		print_to_console=True,
	)
	logger.info(f"Running Dijkstra on the Compositions (with the {frag_type} corpus) at a resolution of {resolution}.") # noqa

	if frag_type == "greek_foot":
		hash_table = GreekFootHashTable()
	elif frag_type == "decitala":
		hash_table = DecitalaHashTable()
	elif frag_type == "combined":
		hash_table = AllCorporaHashTable()

	all_results = dict()
	for transcription in get_all_transcriptions():
		if transcription.analysis is None:
			continue

		ALL_EXTRACTED = search.rolling_hash_search(
			filepath=transcription.filepath,
			part_num=0,
			table=hash_table,
			allow_subdivision=True
		)

		transcription_results = dict()
		for point in path_finding_utils.make_3D_grid(resolution=resolution):
			logger.info(f"\nRunning Dijkstra for {point}.")
			path = search.path_finder(
				filepath=transcription.filepath,
				part_num=0,
				table=hash_table,
				allow_subdivision=True,
				cost_function_class=path_finding_utils.CostFunction3D(
					gap_weight=point[0],
					onset_weight=point[1],
					articulation_weight=point[2]
				),
			)
			path = path_finding_utils.split_extractions(
				data=path,
				split_dict={GreekFoot("Diiamb"): [GreekFoot("Iamb"), GreekFoot("Iamb")]},
				all_res=ALL_EXTRACTED
			)

			training_data = transcription.analysis
			accuracy = path_finding_utils.check_accuracy(
				training_data=training_data,
				calculated_data=path,
				mode="Transcriptions"
			)
			logger.info("{0} -> ({1}): {2}%".format(transcription, point, accuracy)) # noqa
			transcription_results[str(point)] = accuracy

		all_results[transcription.name] = transcription_results

	filepath = f"/Users/lukepoeppel/decitala/decitala/extra/{date}_transcription_hyperparameters_{resolution}_{frag_type}.json" # noqa
	with open(filepath, "w") as fp:
		json.dump(obj=all_results, fp=fp, ensure_ascii=False, indent=4)

# run_on_all_analyzed_transcriptions(frag_type="greek_foot", resolution=0.2)

####################################################################################################
# Plotting
def get_individual_results(mode, name, data_filepath):
	vals = []
	with open(data_filepath) as results:
		loaded = json.load(results)
		if mode == "Compositions":
			results = loaded[name]
		elif mode == "Transcriptions":
			results = loaded[name.name]
		for key, val in results.items():
			as_list = "[" + key[1:-1] + "]"
			loaded_key = json.loads(as_list)
			gap_weight = loaded_key[0]
			onset_weight = loaded_key[1]
			result = val
			vals.append([gap_weight, onset_weight, result])

	return vals

def get_all_composition_results(data_filepath):
	all_points = []
	for this_composition in compositions:
		all_points.extend(get_individual_results("Compositions", this_composition, data_filepath))

	return all_points

def get_all_transcription_results(data_filepath):
	all_points = []
	for transcription in get_all_transcriptions():
		if not(transcription.analysis):
			continue

		all_points.extend(get_individual_results("Transcriptions", transcription, data_filepath))

	return all_points

def get_mean_and_std_by_gap_weight(weight, all_points):
	results = []
	for this_point in all_points:
		if this_point[0] == weight:
			results.append(this_point[-1])

	return [weight, np.mean(results), np.std(results)]

def plot_results(mode, data_filepath, resolution, title, save_path=False):
	"""
	The data_input should be of the form from get_average_result_by_weight
	"""
	plt.title(title, fontname="Times", fontsize=14)
	plt.xlabel("Gap Weight", fontname="Times", fontsize=12)
	plt.ylabel("Accuracy (%)", fontname="Times", fontsize=12)

	gap_weights = [round(x, 3) for x in np.linspace(0, 1, int(1 / resolution) + 1)]
	plt.xticks(np.linspace(0, 1, 11), fontname="Times", fontsize=12)
	plt.yticks(list(range(0, 110, 10)), fontname="Times", fontsize=12)
	plt.ylim(-8, 105)

	if mode == "Compositions":
		ALL_RESULTS = get_all_composition_results(data_filepath)
	elif mode == "Transcriptions":
		ALL_RESULTS = get_all_transcription_results(data_filepath)

	data = []
	errors = []
	for this_point in gap_weights:
		res = get_mean_and_std_by_gap_weight(this_point, ALL_RESULTS)
		data.append([res[0], res[1]])
		errors.append(res[2])
	data = np.array(data)

	x, y = data.T
	plt.errorbar(
		x,
		y,
		yerr=errors,
		fmt="o",
		c="k",
		ms=2,
		capsize=3,
		elinewidth=1,
		markeredgewidth=1,
		ls="-"
	)

	# # These spanners come from looking at the data.
	# plt.axvspan(0.125, 0.975, facecolor="r", alpha=0.2, label="$\mu_{g}$=0.55") # noqa
	# plt.vlines(0.55, 0, 110, colors="k", linestyles="dashed")
	# plt.legend(prop="Times")

	plt.tight_layout()

	if save_path:
		plt.savefig(save_path, dpi=350)

	return plt

# # fp = "/Users/lukepoeppel/decitala/decitala/extra/06-06-2021_composition_hyperparameters_0.025_decitala.json" # noqa
# fp = "/Users/lukepoeppel/decitala/decitala/extra/06-06-2021_transcription_hyperparameters_0.025_greek_foot.json" # noqa
# fp_3D_cost = "/Users/lukepoeppel/decitala/decitala/extra/06-07-2021_transcription_hyperparameters_0.1_greek_foot_3D_cost.json" # noqa
# print(plot_results(mode="Transcriptions", data_filepath=fp_3D_cost, resolution=0.1, title="Average Accuracy From Dijkstra Algorithm for Annotated Transcriptions").show()) # noqa
####################################################################################################
# Testing

# ex23 = Transcription("Ex23")


if __name__ == "__main__":
	if INTERACTIVE:
		dataset = input("Would you like to run on `Compositions` or `Transcriptions`, or `Both`? ")
		resolution = input("At what resolution? ")
		resolution = float(resolution)
		frag_type = input("What rhythmic dataset (options are `decitala`, `greek_foot`, and `combined`)? ") # noqa

		if dataset == "Compositions":
			run_on_all_compositions(frag_type=frag_type, resolution=resolution)