# -*- coding: utf-8 -*-
####################################################################################################
# File:     kd_search.py
# Purpose:  Brute force search algorithm using kd trees.
# 
# Author:   Luke Poeppel
#
# Location: Frankfurt, DE 2020
####################################################################################################
"""
As an alternative to constructing ratio & difference n-ary trees for precise searches, here we will try 
building a kd-tree (using nearest neighbour search) that stores all possible modifications of a given 
fragment. Essentially, a brute force method.
"""
import kdtree
import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

from tools import augment

mpl.style.use('seaborn')

MAX_DIMENSIONS = 3
MAX_NUM_ADDED_VALUES = 3

####################################################################################################

def generate_all_augmentations(fragment):
	"""
	Generates all possible additive and multiplicative augmentations of a fragment. 

	:param fragment numpy.array: array defining the rhythmic fragment.

	>>> all_dvitiya_augmentations = generate_all_augmentations(fragment=[0.25, 0.25, 0.5])
	>>> for possible_augmentation in all_dvitiya_augmentations[:15]:
	...     print(possible_augmentation)
	[0.125 0.125 0.25 ]
	[0.375 0.375 0.5  ]
	[0.625 0.625 0.75 ]
	[0.875 0.875 1.   ]
	[0.1875 0.1875 0.375 ]
	[0.4375 0.4375 0.625 ]
	[0.6875 0.6875 0.875 ]
	[0.9375 0.9375 1.125 ]
	[0.25 0.25 0.5 ]
	[0.5  0.5  0.75]
	[0.75 0.75 1.  ]
	[1.   1.   1.25]
	[0.0625 0.0625 0.375 ]
	[0.3125 0.3125 0.625 ]
	[0.5625 0.5625 0.875 ]
	"""
	factors = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
	differences = [-0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75]
	all_augmentations = []
	for this_factor in factors:
		for this_difference in differences:
			augmentation = augment(fragment=fragment, factor=this_factor, difference=this_difference)
			if all(x > 0 for x in augmentation):
				all_augmentations.append(augmentation)

	return np.vstack(all_augmentations)

def insert_added_values(fragment, n=1):
	"""
	TODO: Inserts n added values into the fragment, according to the "rules" derived from Messiaen's writing.

	:param fragment numpy.array: array defining the rhythmic fragment.
	:param n int: number of added values of be inserted.
	"""
	if n > MAX_NUM_ADDED_VALUES:
		raise Exception('{} is too many added values.'.format(n))
	if len(fragment) < 3:
		raise Exception('A fragment of length {} is too short for added values.'.format(n))

	curr = 0
	while curr <= n:
		if fragment[0] != 0.25:
			pass
		n += 1

def generate_all_modifications(fragment, max_dimensions):
	"""
	Generates all modifications. NOTE: not currently supporting added values. 
	"""
	all_modifications = []
	if fragment == fragment[::-1]:
		return generate_all_augmentations(fragment)
	else:
		all_modifications.extend(generate_all_augmentations(fragment))
		all_modifications.extend(generate_all_augmentations(fragment[::-1]))
	
	stupid = [x.tolist() for x in all_modifications]
	unique = []
	for this_modification in stupid:
		if this_modification not in unique:
			unique.append(this_modification)
		else:
			pass

	# Normalizes the number of dimensions in the tree.
	pre = [np.array(x) for x in unique]
	len_diff = max_dimensions - len(pre[0])
	if len_diff == 0:
		return np.vstack(pre)
	elif len_diff < 0:
		raise Exception('{} is too few dimensions for this fragment'.format(max_dimensions))
	else:
		normalized_length = []
		for this_array in pre:
			new = np.append(this_array, [0] * len_diff)
			normalized_length.append(new)
		return np.vstack(normalized_length)

#print(generate_all_modifications(fragment=[0.25, 0.25, 0.5], max_dimensions=6))

####################################################################################################
# 3D visualization
def visualize_3D_modifications(fragment):
	'''
	Helper function to make an array of random numbers having shape (n, )
	with each number distributed Uniform(vmin, vmax).
	'''
	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d')

	all_modifications = generate_all_modifications(fragment, max_dimensions=3)
	for fragment in all_modifications:
		ax.scatter(fragment[0], fragment[1], fragment[2], marker='X', color='r')

	ax.set_xlabel('Onset 1')
	ax.set_ylabel('Onset 2')
	ax.set_zlabel('Onset 3')

	plt.show()

#visualize_3D_modifications(fragment=[0.25, 0.25, 0.5])

####################################################################################################
# KD-tree
"""
TODO: follow same structure as FragmentTree –- provide a data PATH!
"""
def create_kd_tree_from_dataset(dataset, max_dimensions):
	"""Returns a kd-tree from a dataset of rhythmic fragments."""
	fragment_tree = kdtree.create(dimensions=max_dimensions)
	for this_fragment in dataset:
		all_modifications = generate_all_modifications(this_fragment, max_dimensions)
		for this_modification in all_modifications:
			fragment_tree.add(this_modification)

	return fragment_tree

#t = create_kd_tree_from_dataset(dataset = [[0.25, 0.25, 0.5], [1.0, 1.25, 0.5, 1.0]], max_dimensions=3)

#print(t.search_nn((1.25, 1.25, 2.25)))


if __name__ == '__main__':
	import doctest
	doctest.testmod()