####################################################################################################
# File:     hyperparameters.py
# Purpose:  Script for calculating the best weights (hyperparameter search) to Dijkstra.
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
from decitala.hash_table import (
	GreekFootHashTable,
	DecitalaHashTable,
	AllCorporaHashTable
)

from moiseaux.db import (
	Transcription,
	get_all_transcriptions
)

INTERACTIVE = False
mpl.style.use("bmh")

ex26 = Transcription("Ex26")

####################################################################################################
# Annotated works.
sept_haikai_path = "/Users/lukepoeppel/Messiaen/Encodings/Sept_Haikai/1_Introduction.xml"
liturgie_path = "/Users/lukepoeppel/Messiaen/Encodings/Messiaen_Qt/Messiaen_I_Liturgie/Messiaen_I_Liturgie_de_cristal_CORRECTED.xml" # noqa
livre_dorgue_path = "/Users/lukepoeppel/Messiaen/Encodings/Livre_d\'Orgue/V_Piece_En_Trio_Corrected.xml" # noqa

compositions = {
	"sept_haïkaï_0": {
		"filepath": sept_haikai_path,
		"part_num": 0,
		"training_data": utils.loader("/Users/lukepoeppel/decitala/databases/analyses/sept_haïkaï_0_analysis.json") # noqa
	},
	"sept_haïkaï_1": {
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
# Accuracy checking.
def check_accuracy(training_data, calculated_data, mode):
	"""
	The `training_data` is the analysis as provided by Messiean. The `input_data`
	is the data calculated by Dijkstra path-finding.
	NOTE: the data is stored in two different formats, hence the use of `mode`.
	"""
	accuracy = 0
	for this_training_fragment in training_data:
		for this_fragment in calculated_data:
			if mode == "Compositions":
				if (this_training_fragment["fragment"] == this_fragment.fragment) and (tuple(this_training_fragment["onset_range"]) == this_fragment.onset_range): # noqa
					accuracy += 1
			elif mode == "Transcriptions":
				if (this_training_fragment[0] == this_fragment.fragment) and (tuple(this_training_fragment[1]) == this_fragment.onset_range): # noqa
					accuracy += 1

	return (accuracy / len(training_data)) * 100

####################################################################################################
# Running on Compositions
def run_on_all_compositions(
		frag_type,
		resolution
	):
	# Useful if writing to a file.
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
			accuracy = check_accuracy(training_data=training_data, calculated_data=path, mode="Compositions") # noqa
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
		resolution
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
	for transcription in get_all_transcriptions():
		if transcription.analysis is None:
			continue

		transcription_results = dict()
		for gap_weight in parameter_space:
			onset_weight = round(1.0 - gap_weight, 3)
			logger.info("\nRunning Dijkstra for ({0}, {1}).".format(gap_weight, onset_weight))
			path = search.path_finder(
				filepath=transcription.filepath,
				part_num=0,
				table=hash_table,
				allow_subdivision=True,
				weights={"gap": gap_weight, "onsets": onset_weight}
			)

			training_data = transcription.analysis
			accuracy = check_accuracy(training_data=training_data, calculated_data=path, mode="Transcriptions") # noqa
			logger.info("{0} -> ({1}, {2}): {3}%".format(transcription, gap_weight, onset_weight, accuracy)) # noqa
			transcription_results[str((gap_weight, onset_weight))] = accuracy

		all_results[transcription.name] = transcription_results

	filepath = f"/Users/lukepoeppel/decitala/decitala/extra/{date}_transcription_hyperparameters_{resolution}_{frag_type}.json" # noqa
	with open(filepath, "w") as fp:
		json.dump(obj=all_results, fp=fp, ensure_ascii=False, indent=4)

####################################################################################################
# Plotting
def get_results_for_composition(name, filepath):
	vals = []
	with open(filepath) as results:
		loaded = json.load(results)
		composition_results = loaded[name]
		for key, val in composition_results.items():
			as_list = "[" + key[1:-1] + "]"
			loaded_key = json.loads(as_list)
			gap_weight = loaded_key[0]
			onset_weight = loaded_key[1]
			result = val
			vals.append([gap_weight, onset_weight, result])

	return vals

def get_all_results(filepath):
	all_points = []
	for this_composition in compositions:
		all_points.extend(get_results_for_composition(this_composition, filepath))

	return all_points

def get_mean_and_std_by_gap_weight(weight, all_points):
	results = []
	for this_point in all_points:
		if this_point[0] == weight:
			results.append(this_point[2])

	return [weight, np.mean(results), np.std(results)]

def plot_composition_results(filepath, resolution, title, save_fig=False):
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

	ALL_RESULTS = get_all_results(filepath)

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

	# These spanners come from looking at the data.
	plt.axvspan(0.125, 0.975, facecolor="r", alpha=0.2, label="$\mu_{g}$=0.55") # noqa
	plt.vlines(0.55, 0, 110, colors="k", linestyles="dashed")
	plt.legend(prop="Times")

	plt.tight_layout()

	# if save is True:
	# 	plt.savefig("/Users/lukepoeppel/Messiaen/Avg_Parameters_5_Compositions_0.05.png", dpi=400)

	return plt

fp = "/Users/lukepoeppel/decitala/decitala/extra/06-06-2021_composition_hyperparameters_0.025_decitala.json" # noqa
print(plot_composition_results(fp, resolution=0.025, title="Average Accuracy From Dijkstra Algorithm for 5 Compositions").show()) # noqa

if __name__ == "__main__":
	if INTERACTIVE:
		dataset = input("Would you like to run on `Compositions` or `Transcriptions`, or `Both`? ")
		resolution = input("At what resolution? ")
		resolution = float(resolution)
		frag_type = input("What rhythmic dataset (options are `decitala`, `greek_foot`, and `combined`)? ") # noqa

		if dataset == "Compositions":
			run_on_all_compositions(frag_type=frag_type, resolution=resolution)