####################################################################################################
# File:     vis.py
# Purpose:  Histogram, roll visualization, and Treant FragmentTree diagrams.
#
# Author:   Luke Poeppel
#
# Location: Kent, CT, 2020/21 / NYC, 2021
####################################################################################################
import json
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import shutil
import subprocess
import tempfile

from collections import Counter

from music21 import converter

from . import trees  # To avoid circular dependency.
from .utils import get_logger

here = os.path.abspath(os.path.dirname(__file__))
treant_templates = here + "/treant_templates"

FONTNAME = 'Times'
FONTSIZE_TITLE = 14
FONTSIZE_LABEL = 14

mpl.style.use("bmh")

####################################################################################################
def _prepare_docs_and_screenshot(path, serialized_tree, logger):
	with open("tree.json", "w") as json_file:
		json.dump(serialized_tree, json_file)

	logger.info("-> Copying .js files...")
	for this_file in os.listdir(treant_templates):
		shutil.copyfile(treant_templates + "/" + this_file, path + "/" + this_file)

	logger.info("-> Running browserify...")
	parse_data_file = "/".join([path, "parse_data.js"])
	browserified_file = "/".join([path, "bundle.js"])
	os.system(f"browserify {parse_data_file} -o {browserified_file}")

	logger.info("-> Creating webshot with R...")
	webshot_string = "webshot::webshot(url={0}, file={1}, zoom=3, selector={2})".format(
		"'" + path + "/index.html" + "'",
		"'" + path + "/shot.png" + "'",
		"'" + ".Treant" + "'"
	)
	subprocess.call(
		[
			f"""Rscript -e "{webshot_string}" """
		],
		shell=True
	)

def create_tree_diagram(FragmentTree, path=None, verbose=False):
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
	if verbose:
		logger = get_logger(name=__name__, print_to_console=True)
	else:
		logger = get_logger(name=__name__, print_to_console=False)

	stupid_tree = trees.NaryTree()
	if FragmentTree.rep_type == "ratio":
		root = trees.NaryTree().Node(value=1.0, name=None)
		for this_fragment in FragmentTree.sorted_data:
			fragment_list = this_fragment.successive_ratio_array().tolist()
			root.add_path_of_children(fragment_list, this_fragment.name)
	else:
		root = trees.NaryTree().Node(value=0.0, name=None)
		for this_fragment in FragmentTree.sorted_data:
			fragment_list = this_fragment.successive_difference_array().tolist()
			root.add_path_of_children(fragment_list, this_fragment.name)

	stupid_tree.root = root
	serialized = stupid_tree.serialize(for_treant=True)

	logger.info("-> Creating directory and writing tree to JSON...")
	if path is not None:
		os.mkdir(path)
		os.chdir(path)
		_prepare_docs_and_screenshot(path, serialized_tree=serialized, logger=logger)
		logger.info("Done ✔")
		return path
	else:
		with tempfile.TemporaryDirectory() as tmpdir:
			os.chdir(tmpdir)
			_prepare_docs_and_screenshot(tmpdir, serialized_tree=serialized, logger=logger)
			logger.info("Done ✔")
			with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
				shutil.copyfile(tmpdir + "/shot.png", tmpfile.name)
				return tmpfile.name

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
			if this_obj.offset == this_fragment.onset_range[0]:
				this_obj.lyric = this_fragment.fragment.name
				this_obj.style.color = "green"
			elif this_obj.offset == this_fragment.onset_range[-1] - this_obj.quarterLength:
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