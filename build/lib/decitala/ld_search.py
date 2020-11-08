# -*- coding: utf-8 -*-
####################################################################################################
# File:     ld_search.py
# Purpose:  New method for search: store tuples in dict (hash map) & test linear dependence.
# 
# Author:   Luke Poeppel
#
# Location: Frankfurt, DE 2020
####################################################################################################
"""
Are retrograde talas going to be linearly dependent too? Something to consider.
"""
import numpy as np
from decitala import Decitala
from trees import FragmentTree
from tools import cauchy_schwartz

decitala_path = '/Users/lukepoeppel/decitala/Fragments/Decitalas'
ratio_tree = FragmentTree(data_path=decitala_path, frag_type='decitala', rep_type='ratio')

def _difference(array, start_index):
	"""
	Returns the difference between two elements. 
	"""
	try:
		difference = array[start_index + 1] - array[start_index]
		return difference
	except IndexError:
		pass

def successive_difference_array(lst):
	"""
	Returns a list containing differences between successive durations. By convention, we set the 
	first value to 0.0. 
	"""
	difference_lst = [0.0]
	i = 0
	while i < len(lst) - 1:
		difference_lst.append(_difference(lst, i))
		i += 1

	return np.array(difference_lst)

def create_tala_dict():
	tala_dict = dict()
	for this_tala in ratio_tree.filtered_data:
		difference_rep = this_tala.successive_difference_array()
		tala_dict[this_tala.name] = tuple(difference_rep)
	
	return tala_dict

def search(fragment):
	tala_dict = create_tala_dict()
	length_filter = {key : value for key, value in tala_dict.items() if len(value) == len(fragment)}
	ld_filter = {key : value for key, value in length_filter.items() if cauchy_schwartz(np.array(value), successive_difference_array(fragment)) == False}

	return ld_filter

print(search(np.array([0.25, 0.25, 0.5])))