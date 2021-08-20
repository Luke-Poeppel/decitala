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
import natsort
import shutil
import itertools
import subprocess

from collections import Counter

from music21 import converter
from music21 import pitch

from . import search
from .path_finding import path_finding_utils
from .utils import get_logger

here = os.path.abspath(os.path.dirname(__file__))
treant_templates = here + "/treant_templates"

FONTNAME = 'Times'
FONTSIZE_TITLE = 14
FONTSIZE_LABEL = 14

mpl.style.use("bmh")

class VisException(Exception):
	pass

####################################################################################################
def create_tree_diagram(
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
	stupid_tree = treeplotter.tree.Tree()
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
		flip=False,
		title=None,
		save_path=None,
	):
	"""
	Creates a piano-roll type visualization of the fragments given in ``data``.

	:param list data: a list of :obj:`decitala.search.Extraction` objects. Probably from
						:obj:`decitala.search.path_finder`.
	:param bool flip: whether to flip the x-axis of the plot. Default is ``False``.
	:param str title: title for the plot. Default is ``None``.
	:param str save_path: optional path to save the plot (DPI=350). Default is `None`.
	"""
	plt.figure(figsize=(11, 3))
	highest_onset = 0
	for fragment in data:
		if highest_onset > fragment.onset_range[1]:
			pass
		else:
			highest_onset = fragment.onset_range[1]

	for i, fragment in enumerate(natsort.natsorted(data, key=lambda x: x.fragment.name, reverse=True)): # noqa
		plt.barh(
			y=fragment.fragment.name,
			width=fragment.onset_range[1] - fragment.onset_range[0],
			height=0.8,
			left=fragment.onset_range[0],
			color="k",
		)

	if flip:
		plt.xlim(highest_onset + 2.0, -2.0)
	else:
		plt.xlim(-2.0, highest_onset + 2.0)

	plt.xticks(list(range(0, int(highest_onset), 10)), fontname="Times")
	plt.xlabel("Onset", fontsize=12, fontname="Times")
	plt.ylabel("Fragment", fontsize=12, fontname="Times")
	plt.yticks(fontname="Times")

	if title:
		plt.title(title, fontsize=14, fontname="Times")

	plt.tight_layout()

	if save_path:
		plt.savefig(save_path, dpi=350)

	return plt

def annotate_score(
		data,
		filepath,
		part_num,
		transcription_mode=False
	):
	"""
	Function for annotating a score with data.

	:param list data: a list of :obj:`decitala.search.Extraction` objects.
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

	:param list data: a list of :obj:`decitala.search.Extraction` objects.
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

def plot_2D_search_results(
		data=None,
		path=None,
		title=None,
		legend=True,
		save_path=None
	):
	"""
	Function for plotting the results of (usually) the full extracted data from a composition,
	as well as a path extracted from it. The ``data`` parameter will plot the fragments as a
	scatter plot of their start and end; the ``path`` parameter will plot the connected line
	between the ``path`` fragments.

	:param list data: a list of :obj:`decitala.search.Extraction` objects.
	:param list path: Intended for data from :obj:`decitala.search.path_finder`. Default is `None.
	:param str title: Title for the plot. Default is `None`.
	:param bool legend: Whether to include a legend in the final plot. Default is ``True``.
	:param str save_path: Optional path to save the plot (DPI=350). Default is `None`.
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

	if legend:
		plt.legend(prop="Times")

	plt.tight_layout()

	if save_path:
		plt.savefig(save_path, dpi=350)

	return plt

def plot_pitch_class_distribution_by_species(species, save_path=None):
	combined_pc_dict = species.aggregated_pc_distribution(as_vector=False)
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

def _stupid_flatten(data):
	out = []
	for val in data:
		if isinstance(val, list):
			out.extend(_stupid_flatten(val))
		else:
			out.append(val)
	return out

def dijkstra_gif(
		filepath,
		part_num,
		table,
		windows=list(range(2, 19)),
		allow_subdivision=False,
		allow_contiguous_summation=False,
		algorithm="dijkstra",
		cost_function_class=path_finding_utils.CostFunction3D(),
		split_dict=None,
		slur_constraint=False,
		enforce_earliest_start=False,
		title=None,
		rate=20,
		show=False,
		save_path=None
	):
	"""
	Function for creating a GIF file of the Dijkstra algorithm for a given
	filepath-part-num combination using imagemagick.

	:param str save_path: path to a folder that will be created. This folder will contain the
							GIF file along with a subfolder containing the source images for
							the GIF.
	"""
	if not(save_path):
		raise VisException("No path provided.")

	logger = get_logger(name=__file__)

	os.mkdir(save_path)
	################################################################################################
	# Base Plot.
	all_data = search.rolling_hash_search(
		filepath=filepath,
		part_num=part_num,
		table=table,
		windows=windows,
		allow_subdivision=allow_subdivision,
		allow_contiguous_summation=allow_contiguous_summation
	)
	xs = [x.onset_range[0] for x in all_data]
	ys = [x.onset_range[1] for x in all_data]
	plt.scatter(xs, ys, s=5, color="k")

	plt.xticks(fontname="Times")
	plt.xlabel("Offset Start", fontname="Times", fontsize=12)
	plt.yticks(fontname="Times")
	plt.ylabel("Offset End", fontname="Times", fontsize=12)

	if title:
		plt.title(title, fontname="Times", fontsize=14)
	plt.tight_layout()

	logger.info("Saving base image...")
	base_path = save_path + "/f1.png"
	plt.savefig(base_path, dpi=350)
	for i in range(2, 6):
		shutil.copyfile(base_path, save_path + f"/f{i}.png")

	plt.clf()
	################################################################################################
	# Plot each pair
	sources, sinks = path_finding_utils.sources_and_sinks(
		data=all_data,
		enforce_earliest_start=enforce_earliest_start
	)
	pairs = list(itertools.product(sources, sinks))

	def _dijkstra_gif_pair(i, data, pair, title=None, save_path=None):
		plt.text(0.05, pair[1].onset_range[1], f"Pair {i}...", fontname="Times")

		xs = [x.onset_range[0] for x in data]
		ys = [x.onset_range[1] for x in data]
		plt.scatter(xs, ys, s=5, color="k")

		plt.scatter(pair[0].onset_range[0], pair[0].onset_range[1], marker="d", s=25, color="r")
		plt.scatter(pair[1].onset_range[0], pair[1].onset_range[1], marker="d", s=25, color="r")

		plt.xticks(fontname="Times")
		plt.xlabel("Offset Start", fontname="Times", fontsize=12)
		plt.yticks(fontname="Times")
		plt.ylabel("Offset End", fontname="Times", fontsize=12)

		if title:
			plt.title(title, fontname="Times", fontsize=14)

		curr_path = save_path + f"/f{5 * i}.png"
		plt.savefig(curr_path, dpi=350)
		for i in range((5 * i) + 1, (5 * i) + 5 + 1):
			shutil.copyfile(curr_path, save_path + f"/f{i + 1}.png")

	for i, pair in enumerate(pairs, start=1):
		_dijkstra_gif_pair(i, all_data, pair, title, save_path)
		plt.clf()

	################################################################################################
	# Making the GIF:
	gif_filepath = os.path.join(save_path, "final.gif")
	file_order = [os.path.join(save_path, f"f{i}.png") for i in range(1, len(os.listdir(save_path)))]
	run_elems = [
		"convert",
		"-delay",
		str(rate),
		file_order,
		"-loop",
		"0",
		gif_filepath
	]
	subprocess.run(_stupid_flatten(run_elems))

	################################################################################################
	if show:
		plt.show()