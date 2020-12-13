# -*- coding: utf-8 -*-
####################################################################################################
# File:     vis.py
# Purpose:  Histogram and roll visualization for talas found in a particular piece. Either 
#           path-dependant or net find. 
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

from .trees import (
	NaryTree,
	FragmentTree
)

import logging
logging.basicConfig(level=logging.INFO)

FONTNAME = 'Times'
FONTSIZE_TITLE = 14
FONTSIZE_LABEL = 14

####################################################################################################
def make_tree_diagram(FragmentTree, path):
	"""Powered by Treant."""
	stupid_tree = NaryTree()
	if FragmentTree.rep_type == "ratio":
		root = NaryTree().Node(value = 1.0, name = None)
		for this_fragment in FragmentTree.sorted_data:
			fragment_list = this_fragment.successive_ratio_array().tolist()
			root.add_path_of_children(fragment_list, this_fragment.name)
	else:
		root = NaryTree().Node(value = 0.0, name = None)
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

####################################################################################################

def tala_counter(data, title, show = True, filename = None):
	"""
	Returns a histogram of the talas found in a Path object. 
	"""
	mpl.style.use('seaborn')

	if isinstance(data, SubPath) or isinstance(data, Path):
		pass
	else:
		raise Exception('Invalid input; must be SubPath or Path.')

	talas = data.decitalas
	c = Counter(talas)
	sorted_c = sorted(c.items(), key = lambda x: x[1], reverse=False)

	# Reduce names to 12 characters. 
	names = [x[0].name if (len(x[0].name) <= 12) else ((x[0].name)[0:12] + '.') for x in sorted_c]
	counts = [x[1] for x in sorted_c]

	max_count = counts[-1]
	
	plt.figure(figsize=(11, 3))
	plt.xticks(list(range(0, max_count + 1, 1)))

	plt.subplots_adjust(bottom=0.17, top=0.81)
	plt.title(title, fontname=FONTNAME, fontsize=FONTSIZE_TITLE)
	plt.xlabel('Count (n)', fontname=FONTNAME, fontsize=12)
	plt.ylabel('Deçitâla Name', fontname=FONTNAME, fontsize=12)

	plt.barh(names, counts, height=0.8)
	
	if filename:
		plt.savefig(filename, dpi=800)#, format='eps')
		#plt.close()
	if show:
		plt.show()

#rename to fragment roll
def tala_roll(data, title, show = True, filename = None):
	"""
	To fix the color situation, maybe make a dictionary that assigns to 
	each tala a random color and then in the loop, add a conditional. 
	"""
	mpl.style.use('seaborn')
	#plt.plot([1, 2, 3], [4, 5, 6])
	names = ['121_Varied.', '105_Candra.', '88_Laksm.']
	counts = [12, 3, 4]

	m = data.data
	plt.figure(figsize=(11, 3))

	#highest_onset = max(m, key = lambda x: x[0][1])
	highest_onset = 0
	for x in m:
		if highest_onset > x[0][1]:
			pass
		else:
			highest_onset = x[0][1]
		
	plt.xticks(list(range(0, int(highest_onset), 10)))
	plt.xlim(-0.02, highest_onset + 2.0)

	for i in range(len(data.data)):
		m = data.data
		plt.barh(m[i][1].name, m[i][0][1] - m[i][0][0], height = 0.8, left = m[i][0][0])

	plt.show()

####################################################################################################
# Testing

#databases
haikai0_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_0.db'
haikai1_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_1.db'

liturgie3_database_path = '/Users/lukepoeppel/decitala_v2/liturgie_3.db'
liturgie4_database_path = '/Users/lukepoeppel/decitala_v2/liturgie_4.db'

livre_dorgue_0_path = '/Users/lukepoeppel/decitala_v2/livre_dorgue_0.db'
livre_dorgue_1_path = '/Users/lukepoeppel/decitala_v2/livre_dorgue_1.db'

#print(type('a'))
#print(type(sb))

# subpaths = get_full_model3_path(liturgie3_database_path)
# full_path = Path(subpaths)

# tala_roll(full_path, 'Haikai Testing', show = True)

# #tala_counter(data=full_path, title="$Sept \: Haïkaï \: Reduction$ \n (Part 0)", show = True, filename='testwrite')
# #tala_counter(data=full_path, title="$Liturgie \: de \: Cristal$ \n (Part 4)", show = False, filename='liturgie4_hist')


