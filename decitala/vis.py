####################################################################################################
# File:     vis.py
# Purpose:  Histogram, roll visualization, and Treant FragmentTree diagrams.
#
# Author:   Luke Poeppel
#
# Location: Kent, CT, 2020/21 / NYC, 2021
####################################################################################################
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import treeplotter

from collections import Counter

from music21 import converter
from music21 import pitch

here = os.path.abspath(os.path.dirname(__file__))
treant_templates = here + "/treant_templates"

FONTNAME = 'Times'
FONTSIZE_TITLE = 14
FONTSIZE_LABEL = 14

mpl.style.use("bmh")

####################################################################################################
def create_diagram(
		FragmentTree,
		path=None,
		webshot=False,
		verbose=False
	):
	"""
	This function creates a visualization of a given :obj:`~decitala.trees.FragmentTree`
	using the Treant.js library. If a path is provided, all the files will be stored there. Otherwise,
	they will be stored in a tempfile for the display.

	:param `~decitala.trees.FragmentTree` FragmentTree: A Fragment tree
	:param str path: Path to the folder where the visualization will be optionally stored.
					Default is `None`.
	:return: A folder at the provided path containing an index.html file which has a visualization
			of the provided :obj:`~decitala.trees.FragmentTree`.
	"""
	stupid_tree = treeplotter.Tree()
	if FragmentTree.rep_type == "ratio":
		root = treeplotter.tree.Node(value=1.0, name=None)
		for this_fragment in FragmentTree.sorted_data:
			fragment_list = this_fragment.successive_ratio_array().tolist()
			root.add_path_of_children(fragment_list, this_fragment.name)
	else:
		root = treeplotter.tree.Node(value=0.0, name=None)
		for this_fragment in FragmentTree.sorted_data:
			fragment_list = this_fragment.successive_difference_array().tolist()
			root.add_path_of_children(fragment_list, this_fragment.name)

	stupid_tree.root = root
	treeplotter.plotter.create_tree_diagram(
		tree=stupid_tree,
		save_path=path,
		webshot=webshot,
		verbose=verbose
	)

def fragment_roll(
		data,
		title=None,
		save_filepath=None,
	):
	"""
	Creates a piano-roll type visualization of fragments in the input data.

	:param list data: Data from one of the :obj:`decitala.search` functions.
	:param str title: Title for the plot. Default is `None`.
	:param str save_filepath: Optional path to save the plot (DPI=350). Default is `None`.
	"""
	plt.figure(figsize=(11, 3))
	plt.title(title, fontsize=14, fontname="Times")
	highest_onset = 0
	for fragment in data:
		if highest_onset > fragment.onset_range[1]:
			pass
		else:
			highest_onset = fragment.onset_range[1]

	plt.xticks(list(range(0, int(highest_onset), 10)))
	plt.xlim(-0.02, highest_onset + 2.0)
	plt.xlabel("Onset", fontsize=12, fontname="Times")
	plt.ylabel("Fragment", fontsize=12, fontname="Times")

	for i, fragment in enumerate(sorted(data, key=lambda x: x.fragment.name)):
		plt.barh(
			y=fragment.fragment.name,
			width=fragment.onset_range[1] - fragment.onset_range[0],
			height=0.8,
			left=fragment.onset_range[0],
			color='k'
		)

	# if plot_break_points:
	# 	pass # TODO

	if save_filepath:
		plt.savefig(save_filepath, dpi=350)

	return plt

def annotate_score(
		data,
		filepath,
		part_num,
		transcription_mode=False
	):
	"""
	Function for annotating a score with data.

	:param list data: Data from one of the :obj:`decitala.search` functions.
	:param str filepath: Filepath to the score to be annotated. Should correspond to the filepath
						used in the creation of the `data`.
	:param int part_num: Part number in the filepath which is to be annotated.Should correspond to
						the filepath used in the creation of the `data`.
	"""
	converted = converter.parse(filepath)
	for this_fragment in data:
		for this_obj in converted.flat.iter.notes:
			if not(transcription_mode):
				if this_obj.offset == this_fragment.onset_range[0]:
					this_obj.lyric = this_fragment.fragment.name
					this_obj.style.color = "green"
				elif this_obj.offset == this_fragment.onset_range[-1] - this_obj.quarterLength:
					this_obj.style.color = "red"
			else:
				if this_obj.offset == this_fragment[1][0]:
					this_obj.lyric = this_fragment[0].name
					this_obj.style.color = "green"
				elif this_obj.offset == this_fragment[1][1] - this_obj.quarterLength:
					this_obj.style.color = "red"

	return converted

def result_bar_plot(
		data,
		title=None,
		save_filepath=None
	):
	"""
	Returns a bar plot of input data.

	:param list data: Data from one of the :obj:`decitala.search` functions.
	:param str title: Title for the plot. Default is `None`.
	:param str save_filepath: Optional path to save the plot (DPI=350). Default is `None`.
	"""
	if type(data) == list:
		fragments = [x["fragment"].name for x in data]

	counter = Counter(fragments)

	if title:
		plt.title(title, fontname="Times", fontsize=14)

	plt.xlabel("Fragment", fontname="Times", fontsize=12)
	plt.ylabel("Count (n)", fontname="Times", fontsize=12)
	plt.yticks(list(range(0, max(counter.values()) + 1)))

	if len(counter.keys()) == 2:
		plt.xlim(-0.5, 1.5)

	plt.bar(counter.keys(), counter.values(), width=0.3, color="k")
	return plt

def plot_2D_search_results(data=None, path=None, title=None, save_filepath=None):
	"""
	Function for plotting the results of (usually) the full extracted data from a composition,
	as well as a path extracted from it. The ``data`` parameter will plot the fragments as a
	scatter plot of their start and end; the ``path`` parameter will plot the connected line
	between the ``path`` fragments.

	:param list data: Data from one of the :obj:`decitala.search` functions. Default is `None`.
	:param list path: Intended for data from :obj:`decitala.search.path_finder`. Default is `None.
	:param str title: Title for the plot. Default is `None`.
	:param str save_filepath: Optional path to save the plot (DPI=350). Default is `None`.
	"""
	if data:
		xs = [x.onset_range[0] for x in data]
		ys = [x.onset_range[1] for x in data]
		plt.scatter(xs, ys, s=5, color="k")

	if path:
		xs = [x.onset_range[0] for x in path]
		ys = [x.onset_range[1] for x in path]
		plt.plot(xs, ys, "--o", color="r", markersize=3, linewidth=1, label="Extracted Path")

	plt.xticks(fontname="Times")
	plt.yticks(fontname="Times")

	if title:
		plt.title(title, fontname="Times", fontsize=14)

	plt.xlabel("Onset Start", fontname="Times", fontsize=12)
	plt.ylabel("Onset Stop", fontname="Times", fontsize=12)

	plt.legend(prop="Times")

	if save_filepath:
		plt.savefig(save_filepath, dpi=350)

	return plt

def plot_pitch_class_distribution_by_species(species, save_path=None):
	combined_pc_dict = species.aggregate_pc_distribution(as_vector=False)
	keys = list(combined_pc_dict.keys())
	values = list(combined_pc_dict.values())

	plt.title(
		"Net Pitch Class Distribution for {}".format(species.name),
		fontname="Times",
		fontsize=14
	)
	plt.xlabel("Pitch Class", fontname="Times", fontsize=12)
	plt.ylabel("Proportion (%)", fontname="Times", fontsize=12)

	plt.xticks(list(range(0, 12)), fontname="Times")
	plt.yticks(fontname="Times")

	plt.bar(keys, values, color="k")
	for i in range(12):
		pc = pitch.Pitch(i)
		if pc.accidental.name == "flat":
			pc = pc.getEnharmonic()
		plt.annotate(pc.name, xy=(keys[i], values[i]), ha='center', va='bottom', fontname="Times")

	if save_path:
		plt.savefig(save_path, dpi=350)

	return plt