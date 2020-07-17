# -*- coding: utf-8 -*-
####################################################################################################
# File:     decitala.py
# Purpose:  Version 2.0 of decitala.py. Dynamic functions for tala search (e.g. deçi-tâlas), primarily
#			in the music and birdsong transcriptions of Olivier Messiaen. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
Big TODO:
- bird decisions
- modify Povel and Essens algorithm to account for fragment length

CODE SPRINT TODO: 
- note to self: doctests are for short examples; doctests are for *actual* testing. 
- should notation conversion functions be standalone? 
- check out added value situation
- change names of successive_X_array
- fix and shorten helper functions below.
- decide convention for kakpadam from Rowley.
- standardize fully to np.array(). Also matplotlib will be easier. 
- fix morris symmetry class
- figure out what the problem is with the c-score. 
"""
from __future__ import division, print_function, unicode_literals

import copy
import datetime
import decimal
import fractions
import itertools
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
import re
import statistics
import tqdm
import unittest

from datetime import datetime
from itertools import chain, combinations
from statistics import StatisticsError

from povel_essens_clock import get_average_c_score
from povel_essens_clock import transform_to_time_scale

from music21 import converter
from music21 import note
from music21 import pitch
from music21 import stream

decitala_path = '/Users/lukepoeppel/decitala_v2/Decitalas'
greek_path = '/Users/lukepoeppel/decitala_v2/Greek_Metrics/XML'

#Doesn't make much sense for these to be np.arrays because of the mixed types... 
carnatic_symbols = np.array([
	['Druta', 'o', 0.25],
	['Druta-Virama', 'oc', 0.375],
	['Laghu', '|', 0.5],
	['Laghu-Virama', '|c', 0.75],
	['Guru', 'S', 1.0],
	['Pluta', 'Sc', 1.5],           #Note: Normally a crescent moon superscript. Since it serves the same function as a virâma––we use the same notation. 
	#['kakapadam', '8X', 2.0]       #Decide what the appropriate convention is...
])

greek_diacritics = [
	['breve', '⏑', 1.0],
	['macron', '––', 2.0]
]

multiplicative_augmentations = np.array([
	['Tiers', 4/3],
	['Un quart', 1.25],
	['Du Point', 1.5],
	['Classique', 2], 
	['Double', 3],
	['Triple', 4],
])

#rounded to 6 decimal places; add more as needed
fraction_dict = {
	0.166667 : fractions.Fraction(1, 6),
	0.333333 : fractions.Fraction(1, 3),
	0.666667 : fractions.Fraction(2, 3), 
	1.333333 : fractions.Fraction(4, 3),
	1.666667 : fractions.Fraction(5, 3)
}

#id_number(s) of decitalas with "subtalas"
subdecitala_array = np.array([26, 38, 55, 65, 68])

############### EXCEPTIONS ###############
class IDException(Exception):
	pass
	#return 'That fragment likely has multiple subfragments under the same ID number.'

############ HELPER FUNCTIONS ############
#Notational Conversion Functions
def carnatic_string_to_ql_array(string):
	"""
	Converts a string of carnatic rhythmic values to a quarter length numpy array. Note that the carnatic characters 
	must have a spaces between them or the string will be converted incorrectly. 

	>>> carnatic_string_to_ql_array(string = 'oc o | | Sc S o o o')
	array([0.375, 0.25 , 0.5  , 0.5  , 1.5  , 1.   , 0.25 , 0.25 , 0.25 ])
	"""
	split_string = string.split()
	return np.array([float(this_carnatic_val[2]) for this_token in split_string for this_carnatic_val in carnatic_symbols if (this_carnatic_val[1] == this_token)])

def ql_array_to_carnatic_string(ql_array):
	"""
	Converts a list of quarter length values to a string of carnatic rhythmic values.
	
	>>> ql_array_to_carnatic_string([0.5, 0.25, 0.25, 0.375, 1.0, 1.5, 1.0, 0.5, 1.0])
	'| o o oc S Sc S | S'
	"""
	return ' '.join(np.array([this_carnatic_val[1] for this_val in ql_array for this_carnatic_val in carnatic_symbols if (float(this_carnatic_val[2]) == this_val)]))

def ql_array_to_greek_diacritics(ql_array):
	pass

def _ratio(array, start_index):
	"""
	Given an array and a starting index, returns the ratio of the element at the provided index 
	to the element at the following one. A ZeroDivision error will only occur if it encounters a 
	difference list.

	>>> _ratio(np.array([1.0, 0.5]), 0)
	0.5
	>>> _ratio(np.array([0.25, 0.25, 0.75]), 1)
	3.0
	>>> _ratio(np.array([1.5, 1.0]), 0)
	0.66667
	"""
	if not (0 <= start_index and start_index <= len(array) - 1):
		raise IndexError('Input ``start_index`` not in appropriate range!')
	try: 
		ratio = array[start_index + 1] / array[start_index]
		return round(ratio, 5)
	except ZeroDivisionError:
		raise Exception('Something is off...')

def _difference(array, start_index):
	"""
	Returns the difference between two elements. 
	"""
	try:
		difference = array[start_index + 1] - array[start_index]
		return difference
	except IndexError:
		pass

def dotProduct(vector1, vector2):
	'''
	Returns the dot product (i.e. component by component product) of two vectors. 

	>>> v1 = [1.0, 2.0, 0.75]
	>>> v2 = [0.5, 0.5, 0.75]
	>>> dotProduct(v1, v2)
	2.0625
	'''
	if len(vector1) != len(vector2):
		raise Exception('Vector dimensions do not match.')
	else:
		dot_product = 0
		for i in range(0, len(vector1)):
			dot_product += vector1[i] * vector2[i]

	return round(dot_product, 5)

def cauchy_schwartz(vector1, vector2):
	'''
	Tests the cauchy-schwartz inequality between two vectors. Namely, if the absolute value of 
	the dot product of the two vectors is less than the product of the norms, the vectors are 
	linearly independant (and the function returns True); if they are equal, they are dependant 
	(and the function returns False). 

	Linear Independance:
	>>> vectorI1 = [0.375, 1.0, 0.25]
	>>> vectorI2 = [1.0, 0.0, 0.5]
	>>> cauchy_schwartz(vectorI1, vectorI2)
	True

	Test:
	>>> cauchy_schwartz([0.75, 0.5], [1.5, 1.0])
	False

	Linear Dependance (D1 = 2D2):
	>>> vectorD1 = [1.0, 2.0, 4.0, 8.0]
	>>> vectorD2 = [0.5, 1.0, 2.0, 4.0]
	>>> cauchy_schwartz(vectorD1, vectorD2)
	False

	Direct Equality:
	>>> vectorE1 = [0.25, 0.25, 0.25, 0.25]
	>>> vectorE2 = [0.25, 0.25, 0.25, 0.25]
	>>> cauchy_schwartz(vectorE1, vectorE2)
	False
	'''
	def _euclidianNorm(vector):
		'''
		Returns the euclidian norm of a duration vector (rounded to 5 decimal places). Defined as the 
		square root of the inner product of a vector with itself.

		>>> euclidianNorm([1.0, 1.0, 1.0])
		Decimal('1.73205')
		>>> euclidianNorm([1, 2, 3, 4])
		Decimal('5.47722')
		'''
		norm_squared = dotProduct(vector, vector)
		norm = decimal.Decimal(str(math.sqrt(norm_squared)))

		return norm.quantize(decimal.Decimal('0.00001'), decimal.ROUND_DOWN)

	if abs(dotProduct(vector1, vector2)) <  (_euclidianNorm(vector1) * _euclidianNorm(vector2)):
		return True
	else:
		return False

def successive_ratio_list(lst):
	"""
	Returns an array of the successive duration ratios. By convention, we set the first value to 1.0. 
	"""
	ratio_array = [1.0] #np.array([1.0])
	i = 0
	while i < len(lst) - 1:
		ratio_array.append(_ratio(lst, i))
		i += 1

	return np.array(ratio_array)
	
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

	return difference_lst

def powerList(lst):
	"""
	Given a list, returns it's 'power set' (excluding, of course, the empty list). 

	>>> l = [1, 2, 3]
	>>> powerList(l)
	array([(1,), (2,), (3,), (1, 2), (1, 3), (2, 3), (1, 2, 3)], dtype=object)

	>>> for x in powerList([(0.0, 2.0), (4.0, 5.5), (6.0, 7.25)]):
	...     print(x)
	((0.0, 2.0),)
	((4.0, 5.5),)
	((6.0, 7.25),)
	((0.0, 2.0), (4.0, 5.5))
	((0.0, 2.0), (6.0, 7.25))
	((4.0, 5.5), (6.0, 7.25))
	((0.0, 2.0), (4.0, 5.5), (6.0, 7.25))
	"""
	s = list(lst)
	preList = list(chain.from_iterable(combinations(s, r) for r in range(len(s) + 1)))

	for x in preList:
		if len(x) == 0:
			preList.remove(x)

	return np.array(preList)

########################## LA VALEUR AJOUTEE #############################

def get_added_values(ql_lst, print_type = True):
	'''
	Given a quarter length list, returns all indices and types of added values found, according to 
	the examples dicussed in Technique de Mon Langage Musical (1944)). 

	>>> get_added_values([0.25, 0.5, 0.5, 0.75, 0.25])
	[(0, 'du Note'), (4, 'du Note')]
	>>> get_added_values([0.5, 0.25, 0.5, 0.25, 1.0])
	[(1, 'du Note'), (3, 'du Note')]
	>>> get_added_values([0.75, 0.75, 0.75, 0.25, 0.5])
	[(3, 'du Note')]
	>>> get_added_values([0.75, 0.75, 0.75, 0.75, 0.25, 0.25])

	>>> get_added_values([0.5, 0.25, 0.5, 0.75, 1.25, 1.5])
	[(1, 'du Note'), (3, 'du Point'), (4, 'du Tie')]

	>>> l = [1.0, 0.5, 0.25, 1.0, 0.5, 0.75, 0.5]
	>>> get_added_values(l)
	[(2, 'du Note'), (5, 'du Point')]

	?????
	>>> get_added_values([0.5, 0.5, 0.75, 1.25, 0.75])
	[(2, 'du Point'), (3, 'du Tie')]

	>>> get_added_values([1.0, 0.25, 0.5], print_type = False)
	[1]

	>>> get_added_values([0.25, 0.25, 0.75, 2.0])
	[(2, 'du Point')]
	>>> get_added_values([0.5, 0.25, 0.75, 0.25, 0.5])
	[(1, 'du Note'), (2, 'du Point'), (3, 'du Note')]
	'''
	if len(ql_lst) < 3:
		raise Exception('List must be of length 3 or greater.')

	addedVals = []
	if ql_lst[0] == 0.25 and ql_lst[1] != 0.25:
		addedVals.append((0, 'du Note'))
	if ql_lst[-1] == 0.25 and ql_lst[-2] != 0.25:
		addedVals.append((len(ql_lst) - 1, 'du Note'))
	if ql_lst[-1] == 0.75 and ql_lst[-2] % 0.5 == 0:
		addedVals.append((len(ql_lst) - 1, 'du Point'))

	for currIndex in range(1, len(ql_lst) - 1):
		prevVal = ql_lst[currIndex - 1]
		currVal = ql_lst[currIndex]
		nextVal = ql_lst[currIndex + 1]

		x = currVal - 0.25
		if x >= 1.0 and x.is_integer():
			addedVals.append((currIndex, 'du Tie'))

		if currVal == 0.25:
			if prevVal != currVal != nextVal:
				if prevVal % 0.5 == 0 and nextVal % 0.5 == 0:
					addedVals.append((currIndex, 'du Note'))
				elif prevVal % 0.75 == 0:
					addedVals.append((currIndex, 'du Note'))
				elif nextVal % 0.75 == 0:
					addedVals.append((currIndex, 'du Note'))
		elif currVal == 0.75:
			if prevVal % 0.5 == 0 and nextVal % 0.5 == 0:
				addedVals.append((currIndex, 'du Point'))
			elif prevVal < currVal and nextVal > currVal:
				addedVals.append((currIndex, 'du Point'))
			elif prevVal == 0.25:
				addedVals.append((currIndex, 'du Point'))

	if len(addedVals) == 0:
		return None

	if print_type == False:
		return [a[0] for a in addedVals]
	else:
		return addedVals

#NOTE: Double check this works.
def removeAddedValuesFromList(lst):
	added_val_indices = get_added_values(ql_lst=lst, print_type=False)
	for i in added_val_indices:
		del lst[i]

	return lst

########################################################################
class GeneralFragment(object):
	"""
	Class for representing a more general rhythmic fragment. This allows for the 
	creation of FragmentTrees with more abstract data sets, beyond the two encoded. 

	Input: path for now.
	>>> random_fragment_path = '/users/lukepoeppel/decitala_v.2.0/Decitalas/63_Nandi.xml'
	>>> g1 = GeneralFragment(path = random_fragment_path, name = 'test')
	>>> g1
	<GeneralFragment_test: [0.5  0.25 0.25 0.5  0.5  1.   1.  ]>
	>>> g1.filename
	'63_Nandi.xml'

	>>> g1.coolness_level = 'pretty cool'
	>>> g1.coolness_level
	'pretty cool'

	>>> g1.num_onsets
	7
	>>> g1.ql_array()
	array([0.5 , 0.25, 0.25, 0.5 , 0.5 , 1.  , 1.  ])
	>>> g1.successive_ratio_list()
	array([1. , 0.5, 1. , 2. , 1. , 2. , 1. ])
	>>> g1.carnatic_string
	'| o o | | S S'
	>>> g1.dseg(as_str = True)
	'<1 0 0 1 1 2 2>'
	>>> g1.std()
	0.29014
	
	g1.morris_symmetry_class()
	'VII. Stream'

	>>> for this_cycle in g1.get_cyclic_permutations():
	...     print(this_cycle)
	...
	[0.5  0.25 0.25 0.5  0.5  1.   1.  ]
	[0.25 0.25 0.5  0.5  1.   1.   0.5 ]
	[0.25 0.5  0.5  1.   1.   0.5  0.25]
	[0.5  0.5  1.   1.   0.5  0.25 0.25]
	[0.5  1.   1.   0.5  0.25 0.25 0.5 ]
	[1.   1.   0.5  0.25 0.25 0.5  0.5 ]
	[1.   0.5  0.25 0.25 0.5  0.5  1.  ]
	"""
	def __init__(self, path, name = None, **kwargs):
		self.path = path
		self.filename = self.path.split('/')[-1]
		self.name = name

		stream = converter.parse(path)
		self.stream = stream

	def __repr__(self):
		if self.name is None:
			return '<GeneralFragment: {}>'.format(self.ql_array())
		else:
			return '<GeneralFragment_{0}: {1}>'.format(self.name, self.ql_array())
	
	def __hash__(self):
		return hash(self.name)
	
	def ql_array(self, retrograde=False):
		'''
		INPUTS
		*-*-*-*-*-*-*-*-
		retrograde : type = ``bool``
		'''
		if not(retrograde):
			return np.array([this_note.quarterLength for this_note in self.stream.flat.getElementsByClass(note.Note)])
		else:
			return np.flip(np.array([this_note.quarterLength for this_note in self.stream.flat.getElementsByClass(note.Note)]))

	def __len__(self):
		return len(self.ql_array())

	@property
	def num_onsets(self):
		count = 0
		for _ in self.stream.flat.getElementsByClass(note.Note):
			count += 1
		return count

	@property
	def carnatic_string(self):
		return ql_array_to_carnatic_string(self.ql_array())

	@property
	def ql_duration(self):
		return sum(self.ql_array())

	def dseg(self, as_str=False):
		"""
		Marvin's d-seg as introducted in "The perception of rhythm in non-tonal music" (1991). Maps a fragment
		into a sequence of relative durations. This allows cross comparison of rhythmic fragments beyond 
		exact augmentation; we may, for instance, filter rhythms by similar the familiar dseg <1 0 0> which 
		corresponds to long-short-short (e.g. dactyl). 

		INPUTS
		*-*-*-*-*-*-*-*-
		as_str : type = ``bool``
		"""
		dseg_vals = copy.copy(self.ql_array())
		valueDict = dict()

		for i, thisVal in zip(range(0, len(sorted(set(dseg_vals)))), sorted(set(dseg_vals))):
			valueDict[thisVal] = str(i)

		for i, thisValue in enumerate(dseg_vals):
			for thisKey in valueDict:
				if thisValue == thisKey:
					dseg_vals[i] = valueDict[thisKey]

		if as_str == True:
			return '<' + ' '.join([str(int(val)) for val in dseg_vals]) + '>'
		else:
			return np.array([int(val) for val in dseg_vals])

	def reduced_dseg(self, as_str=False):
		"""
		Technique used in this paper. Takes a dseg and returns a new dseg where contiguous values are removed. 

		INPUTS
		*-*-*-*-*-*-*-*-
		as_str : type = ``bool``
		"""
		def _remove_adjacent_equal_elements(array):
			as_lst = list(array)
			filtered = [a for a, b in zip(as_lst, as_lst[1:] + [not as_lst[-1]]) if a != b]
			return np.array(filtered)

		orig = self.dseg(as_str = False)
		as_array = _remove_adjacent_equal_elements(array = orig)

		if not(as_str):
			return np.array([int(val) for val in as_array])
		else:
			return '<' + ' '.join([str(int(val)) for val in as_array]) + '>'

	def successive_ratio_list(self):
		"""
		Returns an array of the successive duration ratios. By convention, we set the first value to 1.0. 
		"""
		ratio_array = [1.0] #np.array([1.0])
		i = 0
		while i < len(self.ql_array()) - 1:
			ratio_array.append(_ratio(self.ql_array(), i))
			i += 1

		return np.array(ratio_array)
	
	def successive_difference_array(self):
		'''
		Returns a list containing differences between successive durations. By convention, we set the 
		first value to 0.0. 
		
		>>> d = Decitala.get_by_id(119).successive_difference_array()
		>>> d
		[0.0, 0.5, 0.0, 0.5, -0.5, 0.0, 0.0, -0.5]
		'''
		difference_lst = [0.0]
		i = 0
		while i < len(self.ql_array()) - 1:
			difference_lst.append(_difference(self.ql_array(), i))
			i += 1

		return difference_lst

	def get_cyclic_permutations(self):
		"""
		Returns all cyclic permutations. 
		"""
		return np.array([np.roll(self.ql_array(), -i) for i in range(self.num_onsets)])

	################ ANALYSIS ################
	def is_non_retrogradable(self):
		return self.ql_array(retrograde = False) == self.ql_array(retrograde = True)

	def morris_symmetry_class(self):
		"""
		Robert Morris (year?) notes 7 kinds of interesting rhythmic symmetries. I provided the names.

		I.) Maximally Trivial:				of the form X (one onset, one anga class)
		II.) Trivial Symmetry: 				of the form XXXXXX (multiple onsets, same anga class)
		III.) Trivial Dual Symmetry:  		of the form XY (two onsets, two anga classes)
		IV.) Maximally Trivial Palindrome: 	of the form XXX...XYX...XXX (multiple onsets, two anga classes)
		V.) Trivial Dual Palindromic:		of the form XXX...XYYYX...XXX (multiple onsets, two anga classes)
		VI.) Palindromic: 					of the form XY...Z...YX (multiple onsets, n/2 anga classes)
		VII.) Stream:						of the form XYZ...abc... (n onsets, n anga classes)
		"""
		dseg = self.dseg(as_str = False)
		reduced_dseg = self.reduced_dseg(as_str = False)

		if len(dseg) == 1:
			return 'I. Maximally Trivial'
		elif len(dseg) > 1 and len(np.unique(dseg)) == 1:
			return 'II. Trivial Symmetry'
		elif len(dseg) == 2 and len(np.unique(dseg)) == 2:
			return 'III. Trivial Dual Symmetry'
		elif len(dseg) > 2 and len(np.unique(dseg)) == 2:
			return 'IV. Maximally Trivial Palindrome'
		elif len(dseg) > 2 and len(reduced_dseg) == 3:
			return 'V. Trivial Dual Palindrome'
		elif len(dseg) > 2 and len(np.unique(dseg)) == len(dseg) // 2:
			return 'VI. Palindrome'
		else:
			return 'VII. Stream'

	def std(self):
		return round(np.std(self.ql_array()), 5)

	def c_score(self):
		"""
		Povel and Essens (1985) C-Score. Returns the average across all clocks. 
		Doesn't seem to work...
		"""
		as_time_scale = transform_to_time_scale(array = self.ql_array())
		return get_average_c_score(array = as_time_scale)
	
	def nPVI(self):
		"""
		Normalized pairwise variability index (Low, Grabe, & Nolan, 2000)
		"""
		IOI = self.ql_array()
		num_onsets = len(IOI)
		summation = 0
		prev = IOI[0]
		for i in range(1, num_onsets):
			curr = IOI[i]
			if curr > 0 and prev > 0:
				summation += abs(curr - prev) / ((curr + prev) / 2.0)
			else:
				pass
			prev = curr

		final = summation * 100 / (num_onsets - 1)
		
		return round(final, 6)
	
	def show(self):
		if self.stream:
			return self.stream.show() 

'''
random_fragment_path = '/users/lukepoeppel/decitala_v.2.0/Decitalas/63_Nandi.xml'
print(random_fragment_path.split('/'))
g1 = GeneralFragment(path = random_fragment_path)
l = np.array([0.5, 0.25, 0.25, 0.5, 0.5, 1.0, 1.0])
print(l)
'''
########################################################################
'''
Inheritance notes:
- if you add the init function to the child class, the child class does not inherit 
the parent classes init function. 
'''
class Decitala(GeneralFragment):
	"""
	Class that stores Decitala data. Reads from a folder containing all Decitala XML files.
	Inherits from GeneralFragment. 

	>>> ragavardhana = Decitala('Ragavardhana')
	>>> ragavardhana
	<decitala.Decitala 93_Ragavardhana>
	>>> ragavardhana.filename
	'93_Ragavardhana.xml'
	>>> ragavardhana.name
	'93_Ragavardhana'
	>>> ragavardhana.id_num
	93
	>>> ragavardhana.num_onsets
	4

	>>> ragavardhana.ql_array()
	array([0.25 , 0.375, 0.25 , 1.5  ])
	>>> ragavardhana.successive_ratio_list()
	array([1.     , 1.5    , 0.66667, 6.     ])
	>>> ragavardhana.carnatic_string
	'o oc o Sc'

	>>> ragavardhana.dseg(as_str = True)
	'<0 1 0 2>'
	>>> ragavardhana.std()
	0.52571
	>>> ragavardhana.c_score()
	12.47059
	>>> ragavardhana.nPVI()
	74.285714
	>>> ragavardhana.morris_symmetry_class()
	'VII. Stream'

	>>> Decitala('Jaya').ql_array()
	array([0.5 , 1.  , 0.5 , 0.5 , 0.25, 0.25, 1.5 ])

	>>> for this_cycle in Decitala('Jaya').get_cyclic_permutations():
	...     print(this_cycle)
	...
	[0.5  1.   0.5  0.5  0.25 0.25 1.5 ]
	[1.   0.5  0.5  0.25 0.25 1.5  0.5 ]
	[0.5  0.5  0.25 0.25 1.5  0.5  1.  ]
	[0.5  0.25 0.25 1.5  0.5  1.   0.5 ]
	[0.25 0.25 1.5  0.5  1.   0.5  0.5 ]
	[0.25 1.5  0.5  1.   0.5  0.5  0.25]
	[1.5  0.5  1.   0.5  0.5  0.25 0.25]
	
	Decitala.getByidNum(idNum) retrieves a Decitala based on an input identification number. These 
	numbers are listed in the Lavignac Encyclopédie and Messiaen Traité.
	
	>>> Decitala.get_by_id(89)
	<decitala.Decitala 89_Lalitapriya>
	"""
	def __init__(self, name, **kwargs):
		if name:
			if name.endswith('.xml'):
				searchName = name
			elif name.endswith('.mxl'):
				searchName = name
			else:
				searchName = name + '.xml'
					
			for thisFile in os.listdir(decitala_path):
				x = re.search(searchName, thisFile)
				if bool(x) == True:
					self.full_path = decitala_path + '/' + thisFile
					self.name = os.path.splitext(thisFile)[0]
					self.filename = thisFile
					self.stream = converter.parse(decitala_path + '/' + thisFile)

		super().__init__(path=self.full_path, name = self.name)
	
	def __repr__(self):
		return '<decitala.Decitala {}>'.format(self.name)
	
	@property
	def id_num(self):
		if self.name:
			idValue = re.search(r'\d+', self.name)
			return int(idValue.group(0))
	
	@classmethod
	def get_by_id(cls, input_id):
		'''
		INPUTS
		*-*-*-*-*-*-*-*-
		input_id : type = ``int`` in range 1-120

		TODO: if I want to be more sophisticated, use subdecitala_array to (in one of those cases)
		return the appropriate tala. 
		TODO: what happens with 'Jaya' versus 'Jayacri,' for example? Simple conditional to add if 
		problematic.
		'''
		assert type(input_id) == int
		if input_id > 120 or input_id < 1:
			raise Exception('Input must be between 1 and 120!')
		
		if input_id in subdecitala_array:
			raise IDException('There are multiple talas with this ID. Please consult the Lavignac.')
			#raise Exception('There are multiple talas with this ID. Please consult the Lavignac.')

		for thisFile in os.listdir(decitala_path):
			x = re.search(r'\d+', thisFile)
			try:
				if int(x.group(0)) == input_id:
					return Decitala(name=thisFile)
			except AttributeError:
				pass
	
	@property
	def numMatras(self):
		return (self.ql_duration / 0.5)

class GreekFoot(GeneralFragment):
	"""
	Class that stores greek foot data. Reads from a folder containing all greek feet XML files.
	Inherits from GeneralFragment. 

	>>> bacchius = GreekFoot('Bacchius')
	>>> bacchius
	<decitala.GreekFoot Bacchius>
	>>> bacchius.filename
	'Bacchius.xml'
	>>> bacchius.name
	'Bacchius'
	>>> bacchius.num_onsets
	3

	>>> bacchius.ql_array()
	array([1., 2., 2.])
	>>> bacchius.successive_ratio_list()
	array([1., 2., 1.])
	>>> bacchius.greek_string
	'⏑ –– ––'

	>>> bacchius.dseg(as_str = True)
	'<0 1 1>'
	>>> bacchius.std()
	0.4714

	bacchius.morris_symmetry_class()
	'VII. Stream'

	>>> for this_cycle in bacchius.get_cyclic_permutations():
	...     print(this_cycle)
	...
	[1. 2. 2.]
	[2. 2. 1.]
	[2. 1. 2.]
	"""
	def __init__(self, name, **kwargs):
		if name:
			if name.endswith('.xml'):
				searchName = name
			elif name.endswith('.mxl'):
				searchName = name
			else:
				searchName = name + '.xml'
					
			for thisFile in os.listdir(greek_path):
				x = re.search(searchName, thisFile)
				if bool(x) == True:
					self.full_path = greek_path + '/' + thisFile
					self.name = os.path.splitext(thisFile)[0]
					self.filename = thisFile
					self.stream = converter.parse(greek_path + '/' + thisFile)

		super().__init__(path=self.full_path, name = self.name)
	
	def __repr__(self):
		return '<decitala.GreekFoot {}>'.format(self.name)
	
	@property
	def greek_string(self):
		greek_string_lst = []
		for this_val in self.ql_array():
			for this_diacritic_name, this_diacritic_symbol, this_diacritic_val in greek_diacritics:
				if this_val == this_diacritic_val:
					greek_string_lst.append(this_diacritic_symbol)

		return ' '.join(greek_string_lst)

################################# WINDOWS ###################################
def partitionByWindows(lst, partitionLengths = [], repeat = True):
	'''
	This function takes in a sequence and a list of partition lengths. It generates sub-lists,
	each with a length corresponding to the values in partitionLengths. If repeat is set to True,
	it will do so repeatedly. Given that there may be a remainder (modulus), the final subset 
	returned may be of a different size. 

	>>> s = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
	>>> for thisPartition in partitionByWindows(s, partitionLengths = [1, 2, 3]):
	...     print(thisPartition)
	[3]
	[1, 4]
	[1, 5, 9]
	[2]
	[6, 5]
	[3, 5]

	>>> s2 = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7]
	>>> partitionByWindows(s2, partitionLengths = [7, 4])
	[[3, 1, 4, 1, 5, 9, 2], [6, 5, 3, 5], [8, 9, 7]]
	'''
	it = iter(lst)

	numOfRepeats = (len(lst) // sum(partitionLengths)) + 1
	newPartitions = numOfRepeats * partitionLengths
	allSlices = [s for s in (list(itertools.islice(it, 0, i)) for i in newPartitions)]

	remainder = list(it)
	if remainder:
		allSlices.append(remainder)

	for thisSlice in allSlices:
		if len(thisSlice) == 0:
			allSlices.remove(thisSlice)

	return allSlices

def roll_window(lst, window):
	'''
	This function takes in a list and returns a list of all windows of a provided length, rolling
	from the starting index to the point at which the window hits the final value of the list. 

	>>> l = ['Mozart', 'Monteverdi', 'Messiaen', 'Mahler', 'MacDowell', 'Massenet']
	>>> for this in roll_window(l, 3):
	...     print(this)
	['Mozart', 'Monteverdi', 'Messiaen']
	['Monteverdi', 'Messiaen', 'Mahler']
	['Messiaen', 'Mahler', 'MacDowell']
	['Mahler', 'MacDowell', 'Massenet']
	'''
	if type(window) != int:
		raise Exception('The window must be an integer!')

	l = []

	iterable = iter(lst)
	win = []
	for _ in range(0, window):
		win.append(next(iterable))
	
	l.append(win)

	for thisElem in iterable:
		win = win[1:] + [thisElem]
		l.append(win)

	return l

#l = [(1.0, 'a'), (2.0, 'b'), (3.0, 'c'), (4.0, 'd'), (5.0, 'e'), (6.0, 'f')]
#print(roll_window(lst = l, window = 3))

################################### TREES ###################################

class NaryTree(object):
	"""
	A single-rooted nary tree for ratio and difference representations of rhythmic fragments. Nodes are 
	hashed by their value and are stored in a set. For demonstration, we will create the following tree: 
	(If a string appears next to a node value, this means the path from the root to that node is an encoded fragment.) 

										1.0				    |	(full path)				LEVEL 1
							0.5			1.0		    3.0A.   |		4.0					LEVEL 2
						0.5		3.0B		 2.0C		    |		1.0					LEVEL 3
						1.0D				 1.0 'Overwrite'|	0.5						LEVEL 4
														    |		2.0 'Full Path'		LEVEL 5

	>>> root = NaryTree().Node(value = 1.0, name = None)			# LEVEL 1

	>>> c1 = NaryTree().Node(value = 0.5, name = None)					# LEVEL 2				
	>>> c2 = NaryTree().Node(value = 1.0, name = None)
	>>> c3 = NaryTree().Node(value = 3.0, name = 'A')
	>>> c3.value 
	3.0

	>>> gc1 = NaryTree().Node(value = 0.5, name = None)					# LEVEL 3
	>>> gc2 = NaryTree().Node(value = 3.0, name = 'B')
	>>> gc3 = NaryTree().Node(value = 2.0, name = 'C')

	>>> ggc = NaryTree().Node(value = 1.0, name = 'D')					# LEVEL 4

	>>> root.parent = None
	>>> root.children = {c1, c2, c3}
	>>> root.children
	{<NODE: value=0.5, name=None>, <NODE: value=1.0, name=None>, <NODE: value=3.0, name=A>}
	>>> c1 in root.children
	True
	
	>>> root.ordered_children()
	[<NODE: value=0.5, name=None>, <NODE: value=1.0, name=None>, <NODE: value=3.0, name=A>]

	>>> c1.add_children([gc1, gc2])
	>>> c1.num_children
	2
	>>> c2.add_child(gc3)
	>>> gc1.add_child(ggc)

	(January 16 Addition)
	I implemented an add_path_of_children() method. This allows for the creation of a path from
	a node through its children. 

	>>> root.add_path_of_children(path = [root.value, 4.0, 1.0, 0.5, 2.0], final_node_name = 'Full Path')
	>>> root.children
	{<NODE: value=0.5, name=None>, <NODE: value=1.0, name=None>, <NODE: value=3.0, name=A>, <NODE: value=4.0, name=None>}

	Check for overwriting data...
	>>> root.add_path_of_children(path = [root.value, 1.0, 2.0, 1.0], final_node_name = 'Test Overwrite')

	We can access children by referencing a node or by calling to its representative value. 

	>>> newValue = root.get_child_by_value(4.0)
	>>> newValue.children
	{<NODE: value=1.0, name=None>}

	>>> c2.get_child(gc3)
	<NODE: value=2.0, name=C>

	>>> c2.get_child_by_value(2.0)
	<NODE: value=2.0, name=C>
	>>> c2.get_child_by_value(4.0)

	>>> TestTree = NaryTree()

	>>> TestTree.root = root
	>>> TestTree
	<NaryTree: nodes=13>
	>>> TestTree.is_empty()
	False

	Calling the size returns the number of nodes in the tree. 
	>>> TestTree.size()
	13

	>>> TestTree.all_possible_paths()
	[1.0]
	[1.0, 0.5]
	[1.0, 0.5, 0.5]
	[1.0, 0.5, 0.5, 1.0]
	[1.0, 0.5, 3.0]
	[1.0, 1.0]
	[1.0, 1.0, 2.0]
	[1.0, 1.0, 2.0, 1.0]
	[1.0, 3.0]
	[1.0, 4.0]
	[1.0, 4.0, 1.0]
	[1.0, 4.0, 1.0, 0.5]
	[1.0, 4.0, 1.0, 0.5, 2.0]

	To iterate through named paths in the tree...
	>>> for thisNamedPath in TestTree:
	...     print(thisNamedPath)
	...
	('D', [1.0, 0.5, 0.5, 1.0])
	('B', [1.0, 0.5, 3.0])
	('C', [1.0, 1.0, 2.0])
	('Test Overwrite', [1.0, 1.0, 2.0, 1.0])
	('A', [1.0, 3.0])
	('Full Path', [1.0, 4.0, 1.0, 0.5, 2.0])

	Get paths of a particular length:
	>>> for thisPath in TestTree.all_named_paths_of_length_n(length = 3):
	...     print(thisPath)
	B
	C

	We can search for paths as follows. 

	>>> TestTree.search_for_path([1.0, 0.5, 0.5, 1.0])
	'D'
	>>> TestTree.search_for_path([1.0, 0.5, 3.0])
	'B'
	>>> TestTree.search_for_path([1.0, 2.0, 4.0])
	>>> TestTree.search_for_path([1.0, 1.0, 2.0])
	'C'
	"""
	class Node(object):
		"""
		A Node object stores an item and references its parent and children. In an nary tree, a parent
		may have any arbitrary number of children, but each child has only 1 parent. 
		"""
		def __init__(self, value, name = None, **kwargs):
			self.value = value
			self.name = name
			self.parent = None
			self.children = set()

		def __repr__(self):
			return '<NODE: value={0}, name={1}>'.format(self.value, self.name)

		def __hash__(self):
			return hash(self.value)

		def __eq__(self, other):
			"""
			Without this, you can add nodes with the same value to the set of children.
			"""
			return (self.value == other.value) 

		def __lt__(self, other):
			return (self.value < other.value)

		def add_child(self, child_node):
			"""
			Adds a single child to the set of children in a node.
			"""
			self.children.add(child_node)
			return

		def add_children(self, children_nodes = []):
			"""
			Adds multiple children to self.children. 
			"""
			if type(children_nodes) != list: 
				raise Exception('Nodes must be contained in a list.')
			
			for this_child in children_nodes:
				self.add_child(this_child)
			return

		def add_path_of_children(self, path, final_node_name):
			"""
			Allows for the the addition of a path of values from a node down through its children. 
			"""
			if path[0] != self.value:
				raise Exception('First value in the path must be self.value.')

			curr = self
			i = 1
			while i < len(path):
				check = curr.get_child_by_value(path[i])
				if check is not None:
					curr = check
					i += 1
				else:
					if i == len(path) - 1:
							child = NaryTree().Node(value = path[i], name = final_node_name)
					else:
						child = NaryTree().Node(value = path[i])

					curr.add_child(child)
					curr = child
					i += 1

			return

		def remove_child(self, child_node):
			if child_node.item.value not in self.children:
				raise Exception('This parent does not have that child!')
			self.children.remove(child_node.item.value)
			return

		def remove_children(self, children_nodes):
			for this_child in children_nodes:
				self.remove_child(this_child)
			return

		def get_child(self, node):
			"""
			Given a ``value``, returns the node in the set of children with that associated value. 
			"""
			for this_child in self.children:
				if this_child.value == node.value:
					return this_child
			else:
				return None

		def get_child_by_value(self, value):
			"""
			Same as the above, but allows for search just by value without Node object. 
			"""
			for this_child in self.children:
				if this_child.value == value:
					return this_child
			else:
				return None

		@property
		def num_children(self) -> int:
			return len(self.children)

		@property
		def has_children(self) -> bool:
			return (self.num_children != 0)

		def ordered_children(self):
			"""
			Returns the children of a node in list format, ordered by value. 
			"""
			return sorted([child for child in self.children])

	def __init__(self):
		self.root = None

	def __repr__(self):
		return '<NaryTree: nodes={0}>'.format(self.size())

	def __iter__(self):
		"""
		Iterates through all named paths in the tree (not nodes), beginning with the 
		shortest paths (of length 2) and ending with paths from the root to the leaves. Ignores 
		paths that do not conclude with a labeled node. 
		"""
		for this_named_path in self.all_named_paths():
			yield this_named_path

	def _size_helper(self, node):
		"""
		Helper function for self.size()
		"""
		num_nodes = 1
		for child in node.children:
			num_nodes += self._size_helper(child)

		return num_nodes

	def size(self):
		"""
		Returns the number of nodes in the nary tree. 
		"""
		return self._size_helper(self.root)

	def is_empty(self) -> bool:
		return (self.size() == 0)

	################################################################################################
	def _all_possible_paths_helper(self, node, path = []):
		"""
		Helper function for self.all_possible_paths()
		"""
		path.append(node.value)
		print(path)
		if len(node.children) == 0:
			pass
		else:
			for child in node.children:
				self._all_possible_paths_helper(child, path)
		path.pop()

	def all_possible_paths(self):
		"""
		Prints all possible paths from the root node, not all of which are necesarrily named. 
		"""
		return self._all_possible_paths_helper(self.root)

	################################################################################################
	def _all_named_paths_helper(self, node, path = []):
		"""
		Helper function for self.all_named_paths. 
		"""
		path.append(node)

		if path[-1].name is not None:
			p = [node.value for node in path]
			yield (path[-1].name, p)
		else:
			pass

		if len(node.children) == 0:
			pass
		else:
			for child in node.children:
				yield from self._all_named_paths_helper(child, path)

		path.pop()

	def all_named_paths(self):
		"""
		Returns all paths from the root that are named. Each path is returned as a tuple consisting
		of the path followed by its name, i.e., ([PATH], 'NAME'). 
		"""
		for this_named_path in self._all_named_paths_helper(self.root):
			yield this_named_path

	################################################################################################
	def _all_mamed_paths_of_length_n_helper(self, node, length_in, path = []):
		'''
		Helper function for self.all_named_paths_of_length_n
		'''
		path.append(node)

		if path[-1].name is not None:
			p = [node.value for node in path]
			if len(p) == length_in:
				yield path[-1].name
				#yield (path[-1].name, p)
		else:
			pass

		if len(node.children) == 0:
			pass
		else:
			for child in node.children:
				yield from self._all_mamed_paths_of_length_n_helper(child, length_in, path)

		path.pop()

	def all_named_paths_of_length_n(self, length):
		"""
		Returns all named paths from the root of provided length. 
		"""
		for this_named_path_of_length_n in self._all_mamed_paths_of_length_n_helper(node = self.root, length_in = length):
			yield this_named_path_of_length_n

	################################################################################################
	def search_for_path(self, path_from_root):
		"""
		Searches through the nary tree for a path consisting of the values in the path_from_root
		list. Note: the first value of the path must either be 1 (ratio representation search) or 
		0 (difference representation search). Call me old-fashioned, but I feel like there should be 
		a difference in output between a path being present but unnamed and path not existing. 
		"""
		#if pathFromRoot[0] != 1.0 or 0.0:
			#raise Exception('Path provided is invalid.')
		if len(path_from_root) <= 2:
			raise Exception('Path provided must be at least 3 values long.')

		curr = self.root
		i = 1
		
		while i < len(path_from_root):
			try:
				curr = curr.get_child_by_value(value = path_from_root[i])
				if curr is None:
					return None
			except AttributeError:
				break

			if (i == len(path_from_root) - 1) and len(curr.children) == 0:
				return curr.name
			elif (i == len(path_from_root) - 1) and curr.name is not None:
				return curr.name
			else:
				i += 1

############################### FRAGMENT TREES ##################################
class FragmentTree(NaryTree):
	"""
	Nary tree for holding ratio and different representation of rhythmic fragments. 

	TODO
	- keep track of rests in all cases. The indices of occurrence can't be based
	upon placement of notes, but have to be based on placement of *all* musical objects. 
	- cauchy-schwartz inequality is completely unnecessary (I think) since we're using ratio representations.
	not sure how this applies for difference representations. 
	- decide on double-onset fragment convention. I'm leaning towards keep them since some of them are odd. 
	"""
	def __init__(self, root_path, frag_type, rep_type, **kwargs):
		if type(root_path) != str:
			raise Exception('Path must be a string.')
		
		if rep_type.lower() not in ['ratio', 'difference']:
			raise Exception('The only possible types are "ratio" and "difference"')
		
		self.root_path = root_path
		self.frag_type = frag_type
		self.rep_type = rep_type

		super().__init__()

		if frag_type.lower() == 'decitala':
			raw_data = []
			for this_file in os.listdir(root_path):
				raw_data.append(Decitala(this_file))
			self.raw_data = raw_data
		elif frag_type.lower() == 'greek_foot':
			raw_data = []
			for this_file in os.listdir(root_path):
				raw_data.append(GreekFoot(this_file))
			self.raw_data = raw_data
		else:
			raw_data = []
			for this_file in os.listdir(root_path):
				raw_data.append(GeneralFragment(this_file))
			self.raw_data = raw_data

		def filter_data(raw_data):
			"""
			Given a list of decitala objects (i.e. converted to a matrix of duration vectors), 
			filter_data() removes:
			- Trivial fragments (single-onset fragments and double onset fragments, the latter 
			by convention). 
			- Duplicate fragments
			- Multiplicative Augmentations/Diminutions (by using the cauchy-schwarz inequality); if 
			two duration vectors are found to be linearly dependant, one is removed.

			Consider the following set of rhythmic fragments.
			[3.0, 1.5, 1.5, 0.75, 0.75]
			[1.5, 1.0]
			[0.75, 0.5, 0.75]
			[0.25, 0.25, 0.5]
			[0.75, 0.5]
			[0.5, 1.0, 2.0, 4.0],
			[1.5, 1.0, 1.5],
			[1.0, 1.0, 2.0],
			[1.0, 0.5, 0.5, 0.25, 0.25],
			[0.25, 0.5, 1.0, 2.0]
			This function reduces this list to:
			[0.75, 0.5], 
			[0.75, 0.5, 0.75], 
			[0.25, 0.25, 0.5], 
			[0.25, 0.5, 1.0, 2.0], 
			[1.0, 0.5, 0.5, 0.25, 0.25]
			"""
			copied = copy.copy(raw_data)
			size = len(copied)

			i = 0
			while i < size:
				try:
					if len(copied[i].ql_array()) == 1:
						del copied[i]
					#if len(copied[i].ql_array()) < 2:
						#del copied[i]
					else:
						pass
				except IndexError:
					pass

				for j, _ in enumerate(copied):
					try: 
						if i == j:
							pass
						elif len(copied[i].ql_array()) != len(copied[j].ql_array()):
							pass
						elif cauchy_schwartz(copied[i].ql_array(), copied[j].ql_array()) == True:
							pass
						elif cauchy_schwartz(copied[i].ql_array(), copied[j].ql_array()) == False:
							firsti = copied[i].ql_array()[0]
							firstj = copied[j].ql_array()[0]

							#Equality removes the second one by convention
							if firsti == firstj:
								del copied[j]
							elif firsti > firstj:
								del copied[i]
							else:
								del copied[j]
						else:
							pass
					except IndexError:
						pass

				i += 1

			return copied

		self.filtered_data = filter_data(self.raw_data)

		if rep_type == 'ratio':
			root_node = self.Node(value = 1.0, name = 'ROOT')
	
			possible_num_onsets = [3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]
			i = 0
			while i < len(possible_num_onsets):
				curr_onset_list = []
				for thisTala in self.filtered_data:
					if len(thisTala.ql_array()) == possible_num_onsets[i]:
						curr_onset_list.append(thisTala)
				for thisTala in curr_onset_list:
					root_node.add_path_of_children(path = list(thisTala.successive_ratio_list()), final_node_name = thisTala)
				i += 1

			self.root = root_node
		
		if rep_type == 'difference':
			root_node = NaryTree().Node(value = 0.0, name = 'ROOT')

			possible_num_onsets = [3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]
			i = 0
			while i < len(possible_num_onsets):
				curr_onset_list = []
				for thisTala in self.filtered_data:
					if len(thisTala.ql_array()) == possible_num_onsets[i]:
						curr_onset_list.append(thisTala)
				for thisTala in curr_onset_list:
					root_node.add_path_of_children(path = thisTala.successive_difference_array(), final_node_name = thisTala)
				i += 1

			self.root = root_node
	
	def get_by_ql_list(self, ql_list, try_all_methods = True):
		'''
		Given a quarter length list, returns whether the fragment is found in the tree. If
		try_all_methods is set to true, searches the tree for the exact ratio/difference representation. 
		Otherwise, checks in the following order. 

		NOTE: want ql -> retro -> ratio/difference! 

		1.) Check ratio/difference tree normal.
		2.) Check ratio/difference tree retrograde.
		4.) Checks all permutations of added values removed. 
		'''
		retrograde = ql_list[::-1]
		ratio_list = successive_ratio_list(ql_list)
		difference_list = successive_difference_array(ql_list)
		retrograde_ratio_list = successive_ratio_list(retrograde)
		retrograde_difference_list = successive_difference_array(retrograde)

		if self.rep_type == 'ratio':
			if not (try_all_methods):
				return self.search_for_path(ratio_list)
			else:
				ratio_search = self.search_for_path(ratio_list)
				if ratio_search is None:
					retrograde_ratio_search = self.search_for_path(retrograde_ratio_list)
					if retrograde_ratio_search is None:
						#ADDED VALUE PERMUTATIONS
						return None	
					else:
						ratio = _ratio(retrograde_ratio_search.ql_array(), 0)
						return (retrograde_ratio_search, ('retrograde', ratio))
				else:
					ratio = _ratio(ratio_search.ql_array(), 0)
					return (ratio_search, ('ratio', ratio))

		if self.rep_type == 'difference':
			if not (try_all_methods):
				return self.search_for_path(difference_list)
			else:
				difference_search = self.search_for_path(difference_list)
				if difference_search is None:
					retrograde_difference_search = self.search_for_path(retrograde_difference_list)
					if retrograde_difference_search is None:
						#ADDED VALUE PERMUTATIONS
						return None	
					else:
						return retrograde_difference_search, '(retrograde)'
				else:
					return difference_search, '(difference)'
	
	def search_with_added_values_removed(self, ql_list):
		'''
		Given a quarter length list, checks if there are any added values in it. If so, removes them 
		and searches the tree. One important thing to note is that some of the fragments already have
		added values in them; as such, we first check the tree with the input fragment before removing
		any values. 
		
		We generate the 'power list' (length 2^n - 1) of the set of indices where added values have been found. 
		We then run the standard search with all possible combinations of indices included/removed. There
		may be several options, so this function returns a generator. 
		'''
		indices = get_added_values(ql_list, print_type=False)
		all_combinations = powerList(lst = indices)

		for thisCombination in all_combinations:
			asLst = list(thisCombination)
			newQlList = copy.copy(ql_list)
			for thisIndex in sorted(asLst, reverse = True):
				del newQlList[thisIndex]

			x = self.get_by_ql_list(ql_list = newQlList)
			if x is not None:
				yield x
			else:
				continue
	
	def get_by_num_onsets(self, num_onsets):
		"""
		Searches the ratio tree for all paths of length numOnsets. 
		"""
		for thisTala in self.all_named_paths_of_length_n(length = num_onsets):
			yield thisTala
	
	############################# Search #############################

	def _getStrippedQlListOfStream(self, filePath, part):
		'''
		Returns the quarter length list of an input stream (with all ties removed).  
		'''
		fullScore = converter.parse(filePath)
		part = fullScore.parts[part]

		flattenedAndStripped = part.flat.stripTies()

		qlList = []
		for thisNote in flattenedAndStripped.notes:
			qlList.append(thisNote.quarterLength)

		return qlList
	
	def _getStrippedObjectList(self, f, p = 0):
		'''
		Returns the quarter length list of an input stream (with ties removed), but also includes 
		spaces for rests! 

		NOTE: this used to be .iter.notesAndRest, but I took it away, for now, to avoid complications.
		'''
		score = converter.parse(f)
		partIn = score.parts[p]
		objLst = []

		stripped = partIn.stripTies(retainContainers = True)
		for thisObj in stripped.recurse().iter.notes: 
			objLst.append(thisObj)

		return objLst
	
	def get_indices_of_object_occurrence(self, file_path, part_num):
		'''
		Given a file path and part number, returns a list containing tuples

		[(OBJ, (start, end))]
		'''
		indices = []
		strippedObjects = self._getStrippedObjectList(f = file_path, p = part_num)
		for thisObj in strippedObjects:
			indices.append((thisObj, (thisObj.offset, thisObj.offset + thisObj.quarterLength)))

		return indices
	
	def partitionSearch(self, filePath, pathToWrite, part, partitions = [], showScore = False):
		"""
		This method of search is not as comprehensive as rollingSearch, but it still has useful 
		applications. 

		TODO: implement the set check. If tala is not found, try the translational augmentation and 
		then the retrograde. 
		TODO: If the fragment is not found on partition, lyric shouldn't be STOP, it should be nff or 
		something similar.
		TODO: Data should have a count under every tala. 
		TODO: Since the hashing algorithm has been improved (should this be in Decitala...?), after 
		a fragment has been found, add it to a set. Before searching the tree for a fragment, check
		for inclusion in the set. 
		"""
		fullScore = converter.parse(filePath)
		p = fullScore.parts[part]
		objectList = []
		qlList = []

		title = fullScore.metadata.title
		pName = p.partName

		foundTalas = set()

		#TOP OF FILE
		current = datetime.datetime.now()
		currStr = current.strftime('%Y-%m-%d_%H:%M')
		fileName = 'Tala_Data_{}'.format(currStr)
		complete = os.path.join(pathToWrite, fileName+ '.txt')
		data = open(complete, 'w+')
		data.write('DECITALA DATA: ' + title + '\n')
		data.write('PART: ' + pName + ' ({0})'.format(str(part)) + '\n')
		data.write('SEARCH TYPE: Partition \n')
		data.write('Partition Lengths: ' + str(partitions) + '\n')
		data.write('--------------------------------------------------------- \n')

		#--------------------------------------
		#QL-LIST
		'''
		Double for loop for ql list and min-offset. Can they be combined?
		'''
		for thisObj in p.recurse().iter.notes:
			objectList.append(thisObj)

		for i, thisObj in enumerate(objectList):
			if thisObj.tie is not None:
				nextObj = objectList[i + 1]
				qlList.append(thisObj.duration.quarterLength + nextObj.duration.quarterLength)
				del objectList[i + 1]
			else:
				qlList.append(thisObj.duration.quarterLength)

		#--------------------------------------
		#MIN OFFSET
		for thisObj in p.recurse().iter.notes:
			try:
				if thisObj.isNote:
					minMusOffset = thisObj.offset
					break
				elif thisObj.isChord:
					minMusOffset = thisObj.offset
					break
			except AttributeError:
				break

		data.write('[0.0-{0}]: Empty\n'.format(str(minMusOffset)))

		partitions = partitionByWindows(lst = qlList, partitionLengths = partitions)
		partitions_copy = copy.copy(partitions)
		offsets = [minMusOffset]
		netSum = sum(qlList)

		i = minMusOffset
		talas = []

		while (i < netSum):
			for j, thisChunk in enumerate(partitions_copy):
				if len(thisChunk) < 3:
					pass
				else:
					x = self.get_by_ql_list(ql_list = thisChunk)
				if x is not 'Tala Not Found in Search Tree.': # not None? 
					foundTalas.add(x)
					talas.append(x)

					sumTo = sum(partitions_copy[j][0:-1]) + i
					try: 
						offsets.append(sumTo)
						data.write('[{0}-{1}]: '.format(str(i), str(sumTo)))
						data.write(x.name + '\n')
					except (IndexError, AttributeError) as e:
						pass

					offsets.append(sum(partitions_copy[j]) + i)
					i += sum(partitions_copy[j])
				else:
					pass

		#ADD TEXT
		for thisObj in p.recurse().iter.notes:
			for thisOffset, thisTala in zip(offsets[0::2], talas):
				try:
					if thisOffset == thisObj.offset:
						thisObj.lyric = thisTala.name
						thisObj.style.color = 'green'
				except AttributeError:
					pass
			for thisOffset in offsets[1::2]:
				try:
					if thisOffset == thisObj.offset:
						thisObj.lyric = 'STOP'
						thisObj.style.color = 'red'
				except AttributeError:
					pass

		if showScore == True:
			p.show()
		else:
			return

	def rolling_search(self, path, part_num, possible_windows = [3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]):
		"""
		Runs a windowed search on an input stream and path number. Returns the decitalas found and the 
		indices of occurrence. 
		"""
		object_list = self.get_indices_of_object_occurrence(file_path = path, part_num = part_num)
		fragments_found = []
		frames = []

		for this_win in possible_windows:
			for this_frame in roll_window(lst = object_list, window = this_win):
				frames.append(this_frame)

		for this_frame in frames:
			as_quarter_lengths = []
			for this_obj, thisRange in this_frame:
				if this_obj.isRest:
					if this_obj.quarterLength == 0.25:
						as_quarter_lengths.append(this_obj)
					else:
						pass		
				as_quarter_lengths.append(this_obj.quarterLength)

			searched = self.get_by_ql_list(ql_list = as_quarter_lengths, try_all_methods=True)
			if searched is not None:
				offset_1 = this_frame[0][0]
				offset_2 = this_frame[-1][0]

				fragments_found.append((searched, (offset_1.offset, offset_2.offset + offset_2.quarterLength)))
				#fragments_found.append((searched, (thisFrame[0][0].offset, thisFrame[0][-1].offset))) #SUM OVER FOR RANGE!#

		return fragments_found

t = FragmentTree(root_path = decitala_path, frag_type = 'decitala', rep_type = 'ratio')
#c = converter.parse('/Users/lukepoeppel/Desktop/Messiaen/Sept_Haikai/1_Introduction.xml')
#sept = '/Users/lukepoeppel/Desktop/Messiaen/Sept_Haikai/1_Introduction.xml'

#new = t.get_indices_of_object_occurrence(sept, 0)

'''
d = Decitala('Jhampa')
d2 = Decitala('Gajajhampa')
d3 = Decitala('Jhampa')

lst = [d, d2, d3]

from collections import Counter

print(lst)
new = []
for x in lst:
	new.append(x.name)

print(new)
print(Counter(new))
'''
#print(Counter(lst))

'''
num_onsets = []
for this_file in os.listdir(decitala_path):
	d = Decitala(this_file)
	num_onsets.append(d.num_onsets)

print(sorted(num_onsets, reverse=True))
'''


#print(new)

#print(t.get_by_ql_list([1.0, 1.0, 1.0, 0.5, 0.75, 0.5]))
#print(Decitala.get_by_id(21).ql_array())
#print(Decitala.get_by_id(21).successive_ratio_list())
#print(_ratio(Decitala.get_by_id(21).ql_array(), 0))

###############################################################################
class Test(unittest.TestCase):
	def runTest(self):
		pass
	
	def testDecitalaName(self):
		kumudaName = Decitala('Vanamali').name
		self.assertEqual(kumudaName, '29_Vanamali')
		
	def testCarnaticStrings(self):
		carnaticStrings = []
		for i in range(21, 24):
			carnaticStrings.append([Decitala.get_by_id(i).carnatic_string])
			
		expectedStrings = [['| S Sc'], ['o o | | | o o | S'], ['S S S | Sc']]
		self.assertEqual(carnaticStrings, expectedStrings)
	
	def testidNum(self):
		'''
		This generates all decitalas with prime id num below 20.
		'''
		talaList = []
		for num in range(2,18):
			if all(num%i!=0 for i in range(2,num)):
				talaList.append(Decitala.get_by_id(num).name)
		
		expectedTalas = ['2_Dvitiya', '3_Tritiya', '5_Pancama', '7_Darpana', '11_Kandarpa', '13_Ranga', '17_Yatilagna']
		
		self.assertEqual(talaList, expectedTalas)
		
	def testConversionA(self):
		danseQlList = [0.25, 0.375, 0.5, 0.25, 0.5, 1.0, 0.5, 1.5, 0.375, 1.0]
		
		converted = ql_array_to_carnatic_string(ql_array=danseQlList)
		expectedConversion = 'o oc | o | S | Sc oc S'
		
		self.assertEqual(converted, expectedConversion)
	
	'''
	def testConversionB(self):
		abime = '| | o |c | oc o Sc'
		
		converted = carnatic_string_to_ql_array(abime)
		expected = [0.5, 0.5, 0.25, 0.75, 0.5, 0.375, 0.25, 1.5]
		
		self.assertEqual(converted, expected)
	'''

if __name__ == '__main__':
	import doctest
	doctest.testmod()
	#unittest.main()