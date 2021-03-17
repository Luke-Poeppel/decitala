# -*- coding: utf-8 -*-
####################################################################################################
# File:     vis.py
# Purpose:  Histogram, roll visualization, and Treant FragmentTree diagrams.
#
# Author:   Luke Poeppel
#
# Location: Kent, CT, 2020 / NYC, 2021
####################################################################################################
import json
import matplotlib.pyplot as plt
import os
import shutil
import subprocess
import tempfile

from . import trees  # To avoid circular dependency.
from .utils import get_logger

here = os.path.abspath(os.path.dirname(__file__))
treant_templates = here + "/treant_templates"

__all__ = [
	"create_tree_diagram",
	"fragment_roll"
]

FONTNAME = 'Times'
FONTSIZE_TITLE = 14
FONTSIZE_LABEL = 14

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
	os.system("browserify {0} -o {1}".format(parse_data_file, browserified_file))

	logger.info("-> Creating webshot with R...")
	webshot_string = "webshot::webshot(url={0}, file={1})".format("'" + path + "/index.html" + "'", "'" + path + "/shot.pdf" + "'")
	subprocess.call(
		[
			"""Rscript -e "{}" """.format(webshot_string),
		],
		shell=True
	)

def create_tree_diagram(FragmentTree, path=None, pdf_path=None, verbose=False):
	"""
	This function creates a visualization of a given :obj:`~decitala.trees.FragmentTree`
	using the Treant.js library. If a path is provided, all the files will be stored there. Otherwise,
	they will be stored in a tempfile for the display. 

	:param `~decitala.trees.FragmentTree` FragmentTree: A Fragment tree
	:param str path: path to the folder where the visualization will be stored.
	:return: folder at the provided path containing an index.html file which has a visualization
			of the provided :obj:`~decitala.trees.FragmentTree`.
	"""
	try:
		if os.path.isdir(path):
			logger.info("A diagram already exists at that location ✔")
	except TypeError:
		pass

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
				shutil.copyfile(tmpdir + "/shot.pdf", tmpfile.name)
				return tmpfile.name

def fragment_roll(
		data,
		title=None,
		show=True,
		save=None,
		plot_break_points=False
	):
	"""
	Creates a piano-roll type visualization of fragments in the input data.

	:param list data: intended for output of
					:obj:`~database.DBParser.model_full_path(return_data=True)`.
	:param str title: optional title.
	:param bool show: displays the plot.
	:param str save: optional path to save the file.
	"""
	plt.figure(figsize=(11, 3))
	plt.title(title, fontsize=14, fontname="Times")
	highest_onset = 0
	for fragment in data:
		if highest_onset > fragment["onset_range"][1]:
			pass
		else:
			highest_onset = fragment["onset_range"][1]

	plt.xticks(list(range(0, int(highest_onset), 10)))
	plt.xlim(-0.02, highest_onset + 2.0)
	plt.xlabel("Onset", fontsize=12, fontname="Times")
	plt.ylabel("Fragment", fontsize=12, fontname="Times")

	for i, fragment in enumerate(sorted(data, key=lambda x: x["fragment"].name)):
		plt.barh(
			y=fragment["fragment"].name,
			width=fragment["onset_range"][1] - fragment["onset_range"][0],
			height=0.8,
			left=fragment["onset_range"][0],
			color='k'
		)

	# if plot_break_points:
	# 	pass # TODO

	if show:
		plt.show()
	if save:
		plt.savefig(save, dpi=300)
	return plt