# -*- coding: utf-8 -*-
####################################################################################################
# File:     vis.py
# Purpose:  Histogram, roll visualization, and Treant FragmentTree diagrams. 
#
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import os
import shutil

from collections import Counter

from Naked.toolshed.shell import execute_js

from . import trees # To avoid circular dependency. 

import logging
logging.basicConfig(level=logging.INFO)

__all__ = [
	"create_tree_diagram"
]

FONTNAME = 'Times'
FONTSIZE_TITLE = 14
FONTSIZE_LABEL = 14

####################################################################################################
def create_tree_diagram(FragmentTree, path):
	"""
	This function creates a visualization of a given :obj:`~decitala.trees.FragmentTree` 
	using the Treant.js library.

	:param `~decitala.trees.FragmentTree` FragmentTree: A Fragment tree
	:param str path: path to the folder where the visualization will be stored.
	:return: folder at the provided path containing an index.html file which has a visualization of the provided :obj:`~decitala.trees.FragmentTree`.
	"""
	if os.path.isdir(path):
		logging.info("A FragmentTree diagram already exists at that location ✔")
		return
	stupid_tree = trees.NaryTree()
	if FragmentTree.rep_type == "ratio":
		root = trees.NaryTree().Node(value = 1.0, name = None)
		for this_fragment in FragmentTree.sorted_data:
			fragment_list = this_fragment.successive_ratio_array().tolist()
			root.add_path_of_children(fragment_list, this_fragment.name)
	else:
		root = trees.NaryTree().Node(value = 0.0, name = None)
		for this_fragment in FragmentTree.sorted_data:
			fragment_list = this_fragment.successive_difference_array().tolist()
			root.add_path_of_children(fragment_list, this_fragment.name)
	
	stupid_tree.root = root
	serialized = stupid_tree.serialize(for_treant=True)
	
	logging.info("Creating directory and writing tree to JSON...")
	os.mkdir(path)
	os.chdir(path)
	with open("tree.json", "w") as json_file:
		json.dump(serialized, json_file)
	logging.info("Done ✔")
	
	logging.info("Copying .js files...")
	templates = "/Users/lukepoeppel/decitala/decitala/treant_templates"
	for this_file in os.listdir(templates):
		shutil.copyfile(templates+"/"+this_file, path+"/"+this_file)
	logging.info("Done ✔")

	logging.info("Running browserify...")
	parse_data_file = path+"/parse_data.js"
	browserified_file = path+"/"+"bundle.js"
	
	os.system("browserify {0} -o {1}".format(parse_data_file, browserified_file))

	logging.info("Creating tree...")
	# execute_js("parse_data.js")
	logging.info("Done ✔")
	logging.info("See {}".format(path))