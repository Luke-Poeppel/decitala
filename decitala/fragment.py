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

from music21 import converter
from music21 import note
from music21 import stream

from .utils import (
	carnatic_string_to_ql_array,
	ql_array_to_carnatic_string,
	ql_array_to_greek_diacritics,
	successive_ratio_array,
	successive_difference_array,
)

# Fragments
here = os.path.abspath(os.path.dirname(__file__))

decitala_path = os.path.dirname(here) + "/Fragments/Decitalas"
greek_path = os.path.dirname(here) + "/Fragments/Greek_Metrics/XML"

# ID's of decitalas with "subtalas"
subdecitala_array = np.array([26, 38, 55, 65, 68])

############### EXCEPTIONS ###############
class FragmentException(Exception):
	pass

class DecitalaException(FragmentException):
	pass

############### EXCEPTIONS ###############
class GeneralFragment(object):
	"""
	Class representing a generic rhythmic fragment. The user must provide either a path to a music21 readable
	file or an array of quarter length values. 

	:param str filepath: path to encoded fragment (initialized to None).
	:param numpy.array: array of quarter length values (initialized to None).
	:param str name: optional name argument.
	:raises `~decitala.fragment.FragmentException`: when an array and file are provided or neither are provided.
	
	>>> random_fragment_path = '/Users/lukepoeppel/decitala/Fragments/Decitalas/63_Nandi.xml'
	>>> g1 = GeneralFragment(data=random_fragment_path, name='test')
	>>> g1
	<fragment.GeneralFragment_test: [0.5  0.25 0.25 0.5  0.5  1.   1.  ]>
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
	>>> g1.dseg(as_str=True)
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
	>>> 
	>>> # We may also initialize with an array...
	>>> GeneralFragment(data=np.array([0.75, 0.75, 0.5, 0.25]))
	<fragment.GeneralFragment: [0.75 0.75 0.5  0.25]>
	"""
	def __init__(self, data, name=None, **kwargs):
		if isinstance(data, str):
			assert os.path.isfile(data), FragmentException("The path provided does not lead to a file.")
		
			self.creation_type = 'filepath'
			self.filepath = data
			self.filename = self.filepath.split('/')[-1]

			stream = converter.parse(self.filepath)
			self.stream = stream
		elif isinstance(data, np.ndarray) or isinstance(data, list):
			assert len(data) >= 1
			
			self.creation_type = 'array'
			self.temp_ql_array = np.array(data)
		else:
			raise FragmentException("{} is an invalid instantiation.".format(data))

		self.name = name

	def __repr__(self):
		if self.name is None:
			return '<fragment.GeneralFragment: {}>'.format(self.ql_array())
		else:
			return '<fragment.GeneralFragment_{0}: {1}>'.format(self.name, self.ql_array())
	
	def __hash__(self):
		"""
		:return: hash of the tala by its name.
		"""
		return hash(self.name)

	def __eq__(self, other):
		"""
		:return: whether or not one fragment is equal to another, as defined by its hash.
		"""
		if self.__hash__() == other.__hash__():
			return True
		else:
			return False
	
	def ql_array(self, retrograde=False):
		"""
		:param bool retrograde: whether or not to return the fragment in its original form or in retrograde.
		:return: the quarter length array of the fragment. 
		:rtype: numpy.array
		"""
		if self.creation_type == 'filepath':
			if not(retrograde):
				return np.array([this_note.quarterLength for this_note in self.stream.flat.getElementsByClass(note.Note)])
			else:
				return np.flip(np.array([this_note.quarterLength for this_note in self.stream.flat.getElementsByClass(note.Note)]))
		else:
			if not(retrograde):
				return self.temp_ql_array
			else:
				return np.flip(self.temp_ql_array)

	def ql_tuple(self, retrograde=False):
		"""
		:param bool retrograde: whether or not to return the fragment in its original form or in retrograde.
		:return: the quarter length array of the fragment (as a tuple).
		:rtype: tuple
		"""
		return tuple(self.ql_array(retrograde=retrograde))

	@property
	def num_onsets(self):
		"""
		:return: the number of onsets in the fragment.
		:rtype: int
		"""
		return len(self.ql_array())

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

		>>> g3 = GeneralFragment(np.array([0.25, 0.75, 2.0, 1.0]), name='marvin-p70')
		>>> g3.dseg()
		array([0, 1, 3, 2])
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

		>>> g4 = GeneralFragment([0.125, 0.125, 1.75, 0.5], name='marvin-p74-x')
		>>> g4.dseg(as_str=True)
		'<0 0 2 1>'
		>>> g4.reduced_dseg(as_str=True)
		'<0 2 1>'
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
		"""See docstring of :obj:`decitala.utils.successive_ratio_array`."""
		return successive_ratio_array(self.ql_array())
	
	def successive_difference_array(self):
		"""See docstring of :obj:`decitala.utils.successive_difference_array`."""
		return successive_difference_array(self.ql_array())
		
	def cyclic_permutations(self):
		"""
		:return: all cyclic permutations of :meth:`~decitala.fragment.Decitala.ql_array` as in Morris (year?).
		:rtype: numpy.array
		"""
		return np.array([np.roll(self.ql_array(), -i) for i in range(self.num_onsets)])

	@property
	def is_non_retrogradable(self):
		"""
		:return: whether or not the given fragment is palindromic (i.e. non-retrogradable.)
		:rtype: bool
		"""
		return (self.ql_array(retrograde = False) == self.ql_array(retrograde = True)).all()

	def morris_symmetry_class(self):
		"""
		:return: the fragment's form of rhythmic symmetry, as defined by Morris ("Sets, Scales and Rhythmic Cycles 
		A Classification of Talas in Indian Music"). 
		:rtype: str

		- I. Maximally Trivial:				of the form :math:`X` (one onset, one anga class)
		- II. Trivial Symmetry: 			of the form :math:`XXXXXX` (multiple onsets, same anga class)
		- III. Trivial Dual Symmetry:  		of the form :math:`XY` (two onsets, two anga classes)
		- IV. Maximally Trivial Palindrome: of the form :math:`XXX...XYX...XXX` (multiple onsets, two anga classes)
		- V. Trivial Dual Palindromic:		of the form :math:`XXX...XYYYX...XXX` (multiple onsets, two anga classes)
		- VI. Palindromic: 					of the form :math:`XY...Z...YX` (multiple onsets, :math:`n/2` anga classes)
		- VII. Stream:						of the form :math:`XYZ...abc...` (:math:`n` onsets, :math:`n` anga classes)
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
	
	def nPVI(self):
		"""
		:return: the nPVI of the fragment (Low, Grabe, & Nolan, 2000).
		:rtype: float
		"""
		assert len(self.ql_array()) > 1

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

####################################################################################################
class Decitala(GeneralFragment):
	"""
	Class defining a Decitala object. The class currently reads from the `Fragments/Decitala`
	folder which contains XML files for each fragment. 

	:param str name: Name of the decitala, as is transliterated in the Lavignac, 1921. 
	:raises `decitala.fragment.DecitalaException`: when there is an issue with the name.
		
	>>> ragavardhana = Decitala('Ragavardhana')
	>>> ragavardhana
	<fragment.Decitala 93_Ragavardhana>
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

		super().__init__(data=self.full_path, name=self.name)
	
	def __repr__(self):
		return '<fragment.Decitala {}>'.format(self.name)
	
	@property
	def id_num(self):
		"""
		:return: the ID of the fragment, as given by Lavignac (1921).
		:rtype: int
		"""
		if self.name:
			idValue = re.search(r'\d+', self.name)
			return int(idValue.group(0))
	
	@classmethod
	def get_by_id(cls, input_id):
		"""
		A class method which retrieves a `decitala.fragment.Decitala` object based on a given ID number. These 
		numbers are listed in the Lavignac Encyclopédie (1921) and Messiaen Traité. Some talas have (as I'm calling them) 
		"sub-talas," meaning that their id is not unique. Querying by those talas is currently not supported.

		:return: a Decitala object
		:param int input_id: id number of the tala (in range 1-120).
		:rtype: decitala.fragment.Decitala
		:raises `decitala.fragment.DecitalaException`: when there is an issue with the `input_it`.

		>>> Decitala.get_by_id(89)
		<fragment.Decitala 89_Lalitapriya>
		"""
		assert type(input_id) == int
		if input_id > 121 or input_id < 1:
			raise DecitalaException('Input must be between 1 and 120!')
		
		if input_id in subdecitala_array:
			raise DecitalaException('There are multiple talas with this ID. Please consult the Lavignac (1921).')

		for thisFile in os.listdir(decitala_path):
			x = re.search(r'\d+', thisFile)
			try:
				if int(x.group(0)) == input_id:
					span_end = x.span()[1] + 1
					return Decitala(name=thisFile[span_end:])
			except AttributeError:
				pass
	
	@property
	def carnatic_string(self):
		"""See docstring of :`decitala.tools.successive_ratio_array`."""
		return ql_array_to_carnatic_string(self.ql_array())
	
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

		>>> Decitala('Karanayati').num_anga_classes
		1
		>>> Decitala('Rajatala').num_anga_classes
		4
		"""
		return len(set(self.ql_array()))
	
####################################################################################################
class GreekFoot(GeneralFragment):
	"""
	Class that stores greek foot data. Reads from a folder containing all greek feet XML files.
	Inherits from GeneralFragment. 

	>>> bacchius = GreekFoot('Bacchius')
	>>> bacchius
	<fragment.GreekFoot Bacchius>
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
		if name: # all files either of the form X, X_Y
			if name.endswith('.xml'):
				searchName = name
			else:
				searchName = name + '.xml'
			
			search_name_split = searchName.split('_')
			matches = []
			for thisFile in os.listdir(greek_path):
				x = re.search(searchName, thisFile)
				if bool(x):
					matches.append(thisFile)

			for match in matches:
				split = match.split('_')
				if len(search_name_split) == len(split):
					self.full_path = greek_path + '/' + match
					self.name = match[:-4]
					self.filename = match
					self.stream = converter.parseFile(self.full_path)

		super().__init__(data=self.full_path, name=self.name)
	
	def __repr__(self):
		return '<fragment.GreekFoot {}>'.format(self.name)
	
	@property
	def greek_string(self):
		"""See docstring of :obj:`decitala.tools.ql_array_to_greek_diacritics`."""
		return ql_array_to_greek_diacritics(self.ql_array())

####################################################################################################
# Testing
def test_sama_kankala_sama():
	d1 = Decitala("Sama")
	d2 = Decitala("Kankala_Sama")

	assert d1.name == "53_Sama"
	assert d2.name == "65_C_Kankala_Sama"

def test_rati_ratilila():
	d3 = Decitala("Rati")
	d4 = Decitala("Ratilila")

	assert d3.id_num == 82
	assert d4.id_num == 9

if __name__ == '__main__':
	import doctest
	doctest.testmod()