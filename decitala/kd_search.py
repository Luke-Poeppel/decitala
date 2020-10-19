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
NOTE

INFORMATION TO STORE:
- SCORE
- INSTRUMENT
- ONSET START
- ONSET STOP
"""
import kdtree
import numpy as np

MAX_DIMENSIONS = 3


#tree.add([1, 2, 3])

#list(tree.inorder())

def generate_all_augmentations(array, dim):
    """
    Generates all possible additive and multiplicative augmentations of a given fragment. 
    """
    factors = [0.5, 0.75, 1.25, 1.5, 2.0, 3.0, 4.0]
    all_augmentations = []
    for this_factor in factors:
        all_augmentations.append([this_factor * x for x in array])
    
    return np.vstack(all_augmentations)


def generate_all_modifications(array):
    pass

def create_tree(array):
    tree = kdtree.create(dimensions=MAX_DIMENSIONS)

    for this_point in generate_all_augmentations(array = np.array([1.0, 1.0, 0.5]), dim=2):
        tree.add(this_point)

    return tree


t = create_tree(array=1)
#print(kdtree.visualize(t))
print(t.is_balanced)
t.rebalance()
print(t.is_balanced)

