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
- full id as string (only for those who have subtalas)
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
import unittest
import warnings

from datetime import datetime
from itertools import chain, combinations
from statistics import StatisticsError

#from povel_essens_clock import get_average_c_score
#from povel_essens_clock import transform_to_time_scale

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
class DecitalaException(Exception):
	pass

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

def successive_ratio_array(lst):
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

	return np.array(difference_lst)

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
	the examples dicussed in Technique de Mon Langage Musical (1944). 

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

	TODO: allow the input to be a numpy array/list, too. 
	- how about a class method: GeneralFragment.make_by_array([...])

	Input: path for now.
	>>> random_fragment_path = '/users/lukepoeppel/decitala_v2/Decitalas/63_Nandi.xml'
	>>> g1 = GeneralFragment(path = random_fragment_path, name = 'test')
	>>> g1
	<GeneralFragment_test: [0.5  0.25 0.25 0.5  0.5  1.   1.  ]>
	>>> g1.filename
	'63_Nandi.xml'

	Allows for unique arguments.
	>>> g1.coolness_level = 'pretty cool'
	>>> g1.coolness_level
	'pretty cool'

	>>> g1.num_onsets
	7
	>>> g1.ql_array()
	array([0.5 , 0.25, 0.25, 0.5 , 0.5 , 1.  , 1.  ])
	>>> g1.successive_ratio_array()
	array([1. , 0.5, 1. , 2. , 1. , 2. , 1. ])
	>>> g1.carnatic_string
	'| o o | | S S'
	>>> g1.dseg(as_str = True)
	'<1 0 0 1 1 2 2>'
	>>> g1.std()
	0.29014
	
	g1.morris_symmetry_class()
	'VII. Stream'

	>>> for this_cycle in g1.cyclic_permutations():
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

	def __eq__(self, other):
		if self.__hash__() == other.__hash__():
			return True
		else:
			return False

	@classmethod
	def make_by_array(cls, array):
		"""
		Creates a GeneralFragment object 
		"""
		pass
	
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

	def successive_ratio_array(self):
		"""
		Returns an array of the successive duration ratios. By convention, we set the first value to 1.0. 
		"""
		return successive_ratio_array(self.ql_array())
	
	def successive_difference_array(self):
		'''
		Returns a list containing differences between successive durations. By convention, we set the 
		first value to 0.0. 
		
		>>> d = Decitala.get_by_id(119).successive_difference_array()
		>>> d
		array([ 0. ,  0.5,  0. ,  0.5, -0.5,  0. ,  0. , -0.5])
		'''
		return successive_difference_array(self.ql_array())
		
	def cyclic_permutations(self):
		"""
		Returns all cyclic permutations of self.ql_array().
		"""
		return np.array([np.roll(self.ql_array(), -i) for i in range(self.num_onsets)])

	################ ANALYSIS ################
	@property
	def is_non_retrogradable(self):
		return (self.ql_array(retrograde = False) == self.ql_array(retrograde = True)).all()

	def morris_symmetry_class(self):
		"""
		Robert Morris (year?) describes 7 forms of rhythmic symmetry. (I provided the names.)

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

	'''
	def c_score(self):
		"""
		Povel and Essens (1985) C-Score. Returns the average across all clocks. 
		Doesn't seem to work...
		"""
		as_time_scale = transform_to_time_scale(array = self.ql_array())
		return get_average_c_score(array = as_time_scale)
	'''
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
	>>> ragavardhana.successive_ratio_array()
	array([1.     , 1.5    , 0.66667, 6.     ])
	>>> ragavardhana.successive_difference_array()
	array([ 0.   ,  0.125, -0.125,  1.25 ])
	>>> ragavardhana.carnatic_string
	'o oc o Sc'

	>>> ragavardhana.is_non_retrogradable
	False
	>>> ragavardhana.dseg(as_str = True)
	'<0 1 0 2>'
	>>> ragavardhana.std()
	0.52571
	
	ragavardhana.c_score()
	12.47059
	>>> ragavardhana.nPVI()
	74.285714
	>>> ragavardhana.morris_symmetry_class()
	'VII. Stream'

	>>> Decitala('Jaya').ql_array()
	array([0.5 , 1.  , 0.5 , 0.5 , 0.25, 0.25, 1.5 ])

	>>> for this_cycle in Decitala('Jaya').cyclic_permutations():
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
			else:
				searchName = name + '.xml'
			
			search_name_split = searchName.split('_')
			matches = []
			for thisFile in os.listdir(decitala_path):
				x = re.search(searchName, thisFile)
				if bool(x):
					matches.append(thisFile)

			for match in matches:
				split = match.split('_')
				if len(search_name_split) == len(split) - 1:
					self.full_path = decitala_path + '/' + match
					self.name = match[:-4]
					self.filename = match
					self.stream = converter.parse(decitala_path + '/' + match)
				elif len(search_name_split) == len(split) - 2 and len(split[1]) == 1:
					self.full_path = decitala_path + '/' + match
					self.name = match[:-4]
					self.filename = match
					self.stream = converter.parse(decitala_path + '/' + match)
			else:
				pass

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
		if input_id > 121 or input_id < 1:
			raise DecitalaException('Input must be between 1 and 120!')
		
		if input_id in subdecitala_array:
			raise DecitalaException('There are multiple talas with this ID. Please consult the Lavignac.')

		for thisFile in os.listdir(decitala_path):
			x = re.search(r'\d+', thisFile)
			try:
				if int(x.group(0)) == input_id:
					span_end = x.span()[1] + 1
					return Decitala(name=thisFile[span_end:])
			except AttributeError:
				pass
	
	@property
	def num_matras(self):
		return (self.ql_duration / 0.5)
	
	@property
	def num_anga_classes(self):
		return len(set(self.ql_array()))

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
	>>> bacchius.successive_ratio_array()
	array([1., 2., 1.])
	>>> bacchius.greek_string
	'⏑ –– ––'

	>>> bacchius.dseg(as_str = True)
	'<0 1 1>'
	>>> bacchius.std()
	0.4714

	bacchius.morris_symmetry_class()
	'VII. Stream'

	>>> for this_cycle in bacchius.cyclic_permutations():
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

###############################################################################
# Helper function to ignore annoying warnings 
# source: https://www.neuraldump.net/2017/06/how-to-suppress-python-unittest-warnings/

def ignore_warnings(test_func):
	def do_test(self, *args, **kwargs):
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			test_func(self, *args, **kwargs)
	return do_test

class Test(unittest.TestCase):
	def setUp(self):
		warnings.simplefilter('ignore', category=ImportWarning)
	
	def testDecitalaName(self):
		kumudaName = Decitala('Vanamali').name
		self.assertEqual(kumudaName, '29_Vanamali')
		
	def testCarnaticStrings(self):
		carnaticStrings = []
		for i in range(21, 24):
			carnaticStrings.append([Decitala.get_by_id(i).carnatic_string])
			
		expectedStrings = [['| S Sc'], ['o o | | | o o | S'], ['S S S | Sc']]
		self.assertEqual(carnaticStrings, expectedStrings)
	
	def testIDNum(self):
		'''
		This generates all decitalas with prime id num below 20.
		'''
		talaList = []
		for num in range(2,18):
			if all(num%i!=0 for i in range(2,num)):
				talaList.append(Decitala.get_by_id(num).name)
		
		expectedTalas = ['2_Dvitiya', '3_Tritiya', '5_Pancama', '7_Darpana', '11_Kandarpa', '13_Ranga', '17_Yatilagna']
		
		self.assertEqual(talaList, expectedTalas)
		
	def testConversionToCarnaticNotation(self):
		danseQlList = [0.25, 0.375, 0.5, 0.25, 0.5, 1.0, 0.5, 1.5, 0.375, 1.0]
		
		converted = ql_array_to_carnatic_string(ql_array=danseQlList)
		expectedConversion = 'o oc | o | S | Sc oc S'
		
		self.assertEqual(converted, expectedConversion)
	
	def testConversionToWesternNotation(self):
		abime = '| | o |c | oc o Sc'
		
		converted = list(carnatic_string_to_ql_array(abime))
		expected = [0.5, 0.5, 0.25, 0.75, 0.5, 0.375, 0.25, 1.5]
		
		self.assertEqual(converted, expected)

if __name__ == '__main__':
	import doctest
	doctest.testmod()
	unittest.main()