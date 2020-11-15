# -*- coding: utf-8 -*-
####################################################################################################
# File:     fragment.py
# Purpose:  Representation and tools for dealing with generic rhythmic fragments, as well as those
#			used specifically by Messiaen. Includes Decitala and GreekFoot objects. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
from __future__ import division, print_function, unicode_literals

import copy
import numpy as np
import os
import re
import unittest
import warnings

from music21 import converter
from music21 import note
from music21 import stream

from tools import (
	carnatic_string_to_ql_array, 
	ql_array_to_carnatic_string,
	ql_array_to_greek_diacritics,
	successive_ratio_array,
	successive_difference_array,
)

####################################################################################################
# Fragments
decitala_path = '/Users/lukepoeppel/decitala/Fragments/Decitalas'
greek_path = '/Users/lukepoeppel/decitala/Fragments/Greek_Metrics/XML'

# ID's of decitalas with "subtalas"
subdecitala_array = np.array([26, 38, 55, 65, 68])

####################################################################################################
class DecitalaException(Exception):
	pass

class GeneralFragment(object):
	"""
	Class representing a generic rhythmic fragment. 

	:param str path: path to encoded fragment.
	:param str name: optional name argument.
	
	>>> random_fragment_path = '/users/lukepoeppel/decitala/Fragments/Decitalas/63_Nandi.xml'
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
	>>> g1.successive_ratio_array()
	array([1. , 0.5, 1. , 2. , 1. , 2. , 1. ])
	>>> g1.carnatic_string
	'| o o | | S S'
	>>> g1.dseg(as_str = True)
	'<1 0 0 1 1 2 2>'
	>>> g1.std()
	0.2901442287369986
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
		"""
		:return: hash of the tala by its name.
		"""
		return hash(self.name)

	def __eq__(self, other):
		"""
		:return: whether or not one decitala is equal to another, as defined by its hash.
		"""
		if self.__hash__() == other.__hash__():
			return True
		else:
			return False

	@classmethod
	def make_by_array(cls, array):
		"""
		Creates a fragment.GeneralFragment object from an array. 
		"""
		raise NotImplementedError
	
	def ql_array(self, retrograde=False):
		"""
		:param bool retrograde: whether or not to return the fragment in its original form or in retrograde.
		:return: the quarter length array of the fragment. 
		:rtype: numpy.array
		"""
		if not(retrograde):
			return np.array([this_note.quarterLength for this_note in self.stream.flat.getElementsByClass(note.Note)])
		else:
			return np.flip(np.array([this_note.quarterLength for this_note in self.stream.flat.getElementsByClass(note.Note)]))

	def ql_tuple(self, retrograde=False):
		"""
		:param bool retrograde: whether or not to return the fragment in its original form or in retrograde.
		:return: the quarter length array of the fragment (as a tuple).
		:rtype: tuple
		"""
		return tuple(self.ql_array(retrograde=retrograde))

	def __len__(self):
		"""
		:return: the length of the fragment, i.e. the number of onsets.
		:rtype: int
		"""
		return len(self.ql_array())

	@property
	def num_onsets(self):
		"""
		:return: the number of onsets in the fragment.
		:rtype: int
		"""
		return self.__len__()

	@property
	def carnatic_string(self):
		"""
		:return: the fragment in carnatic rhythmic notation.
		:rtype: str
		"""
		return ql_array_to_carnatic_string(self.ql_array())

	@property
	def ql_duration(self):
		"""
		:return: the overall duration of the fragment (as expressed in quarter lengths).
		:rtype: float
		"""
		return sum(self.ql_array())

	def dseg(self, as_str=False):
		"""
		:param bool as_str: whether or not to return the d-seg as a string.
		:return: the d-seg of the fragment, as introducted in "The Perception of Rhythm in Non-Tonal Music" (Marvin, 1991). Maps a fragment into a sequence of relative durations. 
		:rtype: numpy.array
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
		:param bool as_str: whether or not to return the reduced d-seg as a string.
		:return: d-seg of the fragment with all contiguous equal values reduced to a single instance.
		:rtype: numpy.array
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
		"""See docstring of :obj:`decitala.tools.successive_ratio_array`."""
		return successive_ratio_array(self.ql_array())
	
	def successive_difference_array(self):
		"""See docstring of :obj:`decitala.tools.successive_difference_array`."""
		return successive_difference_array(self.ql_array())
		
	def cyclic_permutations(self):
		"""
		:return: all cyclic permutations of self.ql_array(), as in Morris (year?).
		:rtype: numpy.array
		"""
		return np.array([np.roll(self.ql_array(), -i) for i in range(self.num_onsets)])

	################ ANALYSIS ################
	@property
	def is_non_retrogradable(self):
		"""
		:return: whether or not the given fragment is palindromic (i.e. non-retrogradable.)
		:rtype: bool
		"""
		return (self.ql_array(retrograde = False) == self.ql_array(retrograde = True)).all()

	def morris_symmetry_class(self):
		"""
		:return: the fragment's form of rhythmic symmetry, as defined by Morris (?). 
		:rtype: str

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
		"""
		:return: the standard deviation of the fragment's ql_array.
		:rtype: float
		"""
		return np.std(self.ql_array())

	def c_score(self):
		"""
		:return: the c-score of the fragment, as defined in Povel and Essens (1985).
		:rtype: float
		"""
		raise NotImplementedError
		#as_time_scale = transform_to_time_scale(array = self.ql_array())
		#return get_average_c_score(array = as_time_scale)
	
	def nPVI(self):
		"""
		:return: the nPVI of the fragment (Low, Grabe, & Nolan, 2000).
		:rtype: float
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
		
		return final
	
	def show(self):
		if self.stream:
			return self.stream.show() 

########################################################################
# Decitala object
class Decitala(GeneralFragment):
	"""
	Class defining a Decitala object. The class currently reads from the Fragments/Decitala
	folder which contains XML files for each fragment. 

	Base class: `fragment.GeneralFragment`. 	

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
	0.5257063700393976
	>>> ragavardhana.nPVI()
	74.28571428571429
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
	
	Decitala.get_by_id retrieves a decitala based on an input identification number. These 
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
		"""
		:return: the ID of the fragment, as given by Lavignac.
		:rtype: int
		"""
		if self.name:
			idValue = re.search(r'\d+', self.name)
			return int(idValue.group(0))
	
	@classmethod
	def get_by_id(cls, input_id):
		"""
		A class method which retrieves a `fragment.Decitala` object based on a given ID
		number. Some talas have (as I'm calling them) "sub-talas," meaning that their 
		id num is not unique. Querying by those talas is currently not supported.

		:return: fragment.Decitala object.
		:param int input_id: id number of the tala (in range 1-120).
		:rtype: fragment.Decitala
		"""
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
		"""		
		:return: returns the number of matras in the tala (here, the number of eighth notes).
		:rtype: int
		"""
		return (self.ql_duration / 0.5)
	
	@property
	def num_anga_classes(self):
		"""
		:return: the number of anga classes in the tala (the number of unique rhythmic values).
		:rtype: int.
		"""
		return len(set(self.ql_array()))
	
######################################
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
	0.4714045207910317
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
		"""See docstring of :obj:`decitala.tools.ql_array_to_greek_diacritics`."""
		return ql_array_to_greek_diacritics(self.ql_array())

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

if __name__ == '__main__':
	import doctest
	doctest.testmod()
	unittest.main()