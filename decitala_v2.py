# -*- coding: utf-8 -*-
####################################################################################################
# File:     decitala_v2.py
# Purpose:  Version 2.0 of decitala.py. Dynamic functions for tala search (e.g. deçi-tâlas), primarily
#			in the music and birdsong transcriptions of Olivier Messiaen. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
CODE SPRING TODO: 
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
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
import re
import statistics
import tqdm

from povel_essens_clock import get_average_c_score

from music21 import converter
from music21 import note
from music21 import pitch
from music21 import stream

decitala_path = '/Users/lukepoeppel/decitala_v.2.0/Decitalas'
greek_path = '/Users/lukepoeppel/decitala_v.2.0/Greek_Metrics/XML'

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
		return get_average_c_score(array = self.ql_array())
	
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
			raise Exception('There are multiple talas with this ID. Please consult the Lavignac.')

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
	('B', [1.0, 0.5, 3.0])
	('C', [1.0, 1.0, 2.0])

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
		def __init__(self, value, name = None):
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
				yield (path[-1].name, p)
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
	def __init__(self, root_path, rep_type, **kwargs):
		if type(root_path) != str:
			raise Exception('Path must be a string.')
		
		self.root_path = root_path
		self.rep_type = rep_type

		super().__init__()

		rawData = []
		for thisFile in os.listdir(root_path):
			rawData.append(Decitala(thisFile))

		self.rawData = rawData

		def filterData(rawData):
			'''
			Given a list of decitala objects (i.e. converted to a matrix of duration vectors), 
			filterData() removes:
			- Trivial fragments (single-onset fragments and double onset fragments, the latter 
			by convention). 
			- Duplicate fragments
			- Multiplicative Augmentations/Diminutions (by using the cauchy-schwarz inequality); if 
			two duration vectors are found to be linearly dependant, one is removed.

			Consider the following set of rhythmic fragments.
			[3.0, 1.5, 1.5, 0.75, 0.75],
			1.5, 1.0],
			[0.75, 0.5, 0.75],
			[0.25, 0.25, 0.5],
			[0.75, 0.5],
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

			NOTE: this function is one of the many reasons I should have the Greek Metric and Decitala
			classes inherit from some greater class RhythmicFragment. I wouldn't have to have the data
			be a list of decitalas, but instead a list of RhythmicFragments
			'''
			copied = copy.copy(rawData)
			size = len(copied)

			i = 0
			while i < size:
				try:
					if len(copied[i].ql_array()) <= 2:
						del copied[i]
					else:
						pass
				except IndexError:
					pass

				for j, cursor_vector in enumerate(copied):
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

							#Equality removes the second one; random choice. 
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

		self.filteredData = filterData(self.rawData)
	
		rootNode = self.Node(value = 1.0, name = 'ROOT')

		possibleOnsetNums = [3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]
		i = 0
		while i < len(possibleOnsetNums):
			currOnsetList = []
			for thisTala in self.filteredData:
				if len(thisTala.ql_array()) == possibleOnsetNums[i]:
					currOnsetList.append(thisTala)
			for thisTala in currOnsetList:
				rootNode.add_path_of_children(path = list(thisTala.successive_ratio_list()), final_node_name = thisTala)
			i += 1

		self.root = rootNode
		
t = FragmentTree(root_path = decitala_path, rep_type = 'ratio')
print(t)

############################### ANALYSIS ##################################
def binary_search(lst, search_val):
	def _checkSorted(lstIn):
		if len(lstIn) == 1:
			return True
		else:
			remainder = _checkSorted(lstIn[1:])
			return lstIn[0] <= lstIn[1] and remainder

	startIndex = 0
	endIndex = len(lst) - 1
	found = False

	if _checkSorted(lst) == False:
		raise Exception('Input list is not sorted.')

	while startIndex <= endIndex and not found:
		midpoint = (startIndex + endIndex) // 2
		if lst[midpoint] == search_val:
			found = True 
		else:
			if lst[midpoint] > search_val:
				endIndex = midpoint - 1
			else:
				startIndex = midpoint + 1

	return found

def get_all_end_overlapping_indices(lst, i, out):
	"""
	Change to make it a binary search –– this is far too slow. 

	Possible paths: 
	[(0.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
	[(0.0, 2.0), (2.5, 4.5), (6.0, 7.25)]
	[(0.0, 2.0), (2.0, 5.75), (6.0, 7.25)]
	[(0.0, 2.0), (2.0, 4.0), (4.0, 5.5), (6.0, 7.25)]

	Eliminate the waste!
	"""
	all_possibilities = []

	def _get_all_end_overlapping_indices_helper(list_in, i, out):
		r = -1
		if i == len(list_in):
			if out:
				if len(all_possibilities) == 0:
					all_possibilities.append(out)
				else:						
					all_possibilities.append(out)

			return 

		n = i + 1

		while n < len(list_in) and r > list_in[n][0]:
			n += 1
		_get_all_end_overlapping_indices_helper(list_in, n, out)

		r = list_in[i][1]

		n = i + 1
		while n < len(list_in) and r > list_in[n][0]:
			n += 1

		_get_all_end_overlapping_indices_helper(list_in, n, out + [list_in[i]])

	_get_all_end_overlapping_indices_helper.count = 0
	lst.sort()
	_get_all_end_overlapping_indices_helper(list_in = lst, i = 0, out = [])
	
	return all_possibilities

'''
indices = [(0.0, 2.0), (0.0, 4.0), (2.5, 4.5), (2.0, 5.75), (2.0, 4.0), (6.0, 7.25), (4.0, 5.5)]
indices.sort()
for this in tqdm.tqdm(get_all_end_overlapping_indices(lst = indices, i = 0, out = [])):
	print(this)
'''

if __name__ == '__main__':
	import doctest
	#doctest.testmod()