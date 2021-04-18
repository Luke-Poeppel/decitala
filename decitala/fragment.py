####################################################################################################
# File:     fragment.py
# Purpose:  Representation and tools for dealing with generic rhythmic fragments, as well as those
# 			used specifically by Messiaen. Includes Decitala and GreekFoot objects.
#
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
from __future__ import division, print_function, unicode_literals

import copy
import json
import numpy as np
import os
import re
import sqlite3

from ast import literal_eval

from music21 import converter
from music21 import note

from . import utils

__all__ = [
	"GeneralFragment",
	"Decitala",
	"GreekFoot"
]

# Fragments
here = os.path.abspath(os.path.dirname(__file__))
decitala_path = os.path.dirname(here) + "/fragments/Decitalas"
greek_path = os.path.dirname(here) + "/fragments/Greek_Metrics/XML"

fragment_db = os.path.dirname(here) + "/databases/fragment_database.db"

# ID's of decitalas with "subtalas"
subdecitala_array = np.array([26, 38, 55, 65, 68])

####################################################################################################
class FragmentException(Exception):
	pass

class DecitalaException(FragmentException):
	pass

class GreekFootException(FragmentException):
	pass

# Serialization
class FragmentEncoder(json.JSONEncoder):
	def default(self, obj):
		if type(obj).__name__ == "GeneralFragment":
			d = {
				"frag_type": "general_fragment",
				"data": obj.data
			}
			return d
		elif type(obj).__name__ == "Decitala":
			d = {
				"frag_type": "decitala",
				"name": obj.name
			}
			return d
		elif type(obj).__name__ == "GreekFoot":
			d = {
				"frag_type": "greek_foot",
				"name": obj.name
			}
			return d
		else:
			raise FragmentException("This object is not JSON serializable. File an issue?")

class FragmentDecoder(json.JSONDecoder):
	def __init__(self, *args, **kwargs):
		json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

	def temp_loader(self, obj):
		loaded = json.loads(obj)
		return loaded["name"]

	def object_hook(self, obj):
		"""
		This function already runs json.loads invisibly on ``obj``.
		"""
		try:
			if obj["frag_type"] == "general_fragment" and obj["name"] is not None:
				return GeneralFragment(data=obj["data"])
			elif obj["frag_type"] == "decitala" and obj["name"] is not None:
				return Decitala(obj["name"])
			elif obj["frag_type"] == "greek_foot" and obj["name"] is not None:
				return GreekFoot(obj["name"])
			else:
				raise FragmentException("The {} object is not JSON deserializable. File an issue?".format(obj))
		except KeyError:
			return obj

class GeneralFragment:
	"""
	Class representing a generic rhythmic fragment. The user must provide either a path to a music21
	readable file or an array of quarter length values.

	:param data: either an array of quarter length values or a path to a music21 readable file.
	:param str name: optional name.
	:raises `~decitala.fragment.FragmentException`: if an array **and** file are provided or if \
		neither are provided.

	>>> random_fragment_path = "./fragments/Decitalas/63_Nandi.xml"
	>>> g1 = GeneralFragment(data=random_fragment_path, name='test')
	>>> g1
	<fragment.GeneralFragment test: [0.5  0.25 0.25 0.5  0.5  1.   1.  ]>
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
			return '<fragment.GeneralFragment {0}: {1}>'.format(self.name, self.ql_array())

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
		:param bool retrograde: whether or not to return the fragment in its original form \
								or in retrograde.
		:return: the quarter length array of the fragment.
		:rtype: numpy.array
		"""
		if self.creation_type == 'filepath':
			if not(retrograde):
				data = [this_note.quarterLength for this_note in self.stream.flat.getElementsByClass(note.Note)]
				return np.array(data)
			else:
				data = [this_note.quarterLength for this_note in self.stream.flat.getElementsByClass(note.Note)]
				return np.flip(np.array(data))
		else:
			if not(retrograde):
				return self.temp_ql_array
			else:
				return np.flip(self.temp_ql_array)

	def ql_tuple(self, retrograde=False):
		"""
		:param bool retrograde: whether or not to return the fragment in its original form \
								or in retrograde.
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
	def num_anga_classes(self):
		"""
		:return: the number of anga classes in the fragment (the number of unique rhythmic values).
		:rtype: int

		>>> GeneralFragment(data=np.array([0.75, 0.75, 0.5, 0.25])).num_anga_classes
		3
		"""
		return len(set(self.ql_array()))

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
		:return: the d-seg of the fragment, as introducted in `The Perception of Rhythm \
		in Non-Tonal Music <https://www.jstor.org/stable/745974?seq=1#metadata_info_tab_contents>`_ \
		(Marvin, 1991). Maps a fragment into a sequence of relative durations.
		:rtype: numpy.array (or string if ``as_str=True``)

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

		if as_str is True:
			return '<' + ' '.join([str(int(val)) for val in dseg_vals]) + '>'
		else:
			return np.array([int(val) for val in dseg_vals])

	def reduced_dseg(self, as_str=False):
		"""
		:param bool as_str: whether or not to return the reduced d-seg as a string.
		:return: d-seg of the fragment with all contiguous equal values reduced to a single instance.
		:rtype: numpy.array (or string if ``as_str=True``)

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

		orig = self.dseg(as_str=False)
		as_array = _remove_adjacent_equal_elements(array=orig)

		if not(as_str):
			return np.array([int(val) for val in as_array])
		else:
			return '<' + ' '.join([str(int(val)) for val in as_array]) + '>'

	def successive_ratio_array(self, retrograde=False):
		"""See docstring of :obj:`decitala.utils.successive_ratio_array`."""
		if not retrograde:
			return utils.successive_ratio_array(self.ql_array())
		else:
			return utils.successive_ratio_array(self.ql_array(retrograde=True))

	def successive_difference_array(self):
		"""See docstring of :obj:`decitala.utils.successive_difference_array`."""
		return utils.successive_difference_array(self.ql_array())

	def cyclic_permutations(self):
		"""
		:return: all cyclic permutations of :meth:`~decitala.fragment.Decitala.ql_array` as in Morris.
		:rtype: numpy.array
		"""
		return np.array([np.roll(self.ql_array(), -i) for i in range(self.num_onsets)])

	@property
	def is_non_retrogradable(self):
		"""
		:return: whether or not the given fragment is palindromic (i.e. non-retrogradable.)
		:rtype: bool
		"""
		return (self.ql_array(retrograde=False) == self.ql_array(retrograde=True)).all()

	def is_sub_fragment(self, other, try_retrograde=True):
		"""
		:param other: a :obj:`~decitala.fragment.GeneralFragment`, :obj:`~decitala.fragment.Decitala`, \
						or :obj:`~decitala.fragment.GreekFoot` object.
		:param bool try_retrograde: whether to allow searching in retrograde.
		:return: whether or not self is a sub-fragment, meaning its successive_ratio_array exists \
				inorder in the others.
		:rtype: bool
		"""
		def _check(array_1, array_2):
			n = len(array_1)
			m = len(array_2)
			return any((array_1.tolist() == array_2[i:i + n].tolist()) for i in range(m - n + 1))

		if self.num_onsets > other.num_onsets:
			return False

		res = _check(
			array_1=self.successive_ratio_array(retrograde=False),
			array_2=other.successive_ratio_array(retrograde=False)
		)
		if res is False and try_retrograde is True:
			res = _check(
				array_1=self.successive_ratio_array(retrograde=False),
				array_2=other.successive_ratio_array(retrograde=True)
			)
		return res

	def morris_symmetry_class(self):
		"""
		:return: the fragment's form of rhythmic symmetry, as defined by Morris in \
				`Sets, Scales and Rhythmic Cycles. A Classification of Talas in Indian \
				Music <http://ecmc.rochester.edu/rdm/pdflib/talapaper.pdf>`_ (1999).
		:rtype: str

		- I. Maximally Trivial:	of the form :math:`X` (one onset, one anga class)
		- II. Trivial Dual Symmetry:  		of the form :math:`XY`
		- III. Trivial Symmetry: 			of the form :math:`XXXXXX`
		- IV. Maximally Trivial Palindrome: of the form :math:`XXX...XYX...XXX`
		- V. Trivial Dual Palindromic:		of the form :math:`XXX...XYYYX...XXX`
		- VI. Palindromic: 					of the form :math:`XY...Z...YX`
		- VII. Stream:						of the form :math:`XYZ...abc...`
		"""
		dseg = self.dseg(as_str=False)
		reduced_dseg = self.reduced_dseg(as_str=False)

		if len(dseg) == 1:
			return 1
		elif len(dseg) == 2 and len(np.unique(dseg)) == 2:
			return 2
		elif len(dseg) > 1 and len(np.unique(dseg)) == 1:
			return 3
		elif len(dseg) > 2 and len(np.unique(dseg)) == 2:
			return 4
		elif len(dseg) > 2 and len(reduced_dseg) == 3:
			return 5
		elif len(dseg) > 2 and len(np.unique(dseg)) == len(dseg) // 2:
			return 6
		else:
			return 7

	def std(self):
		"""
		:return: the standard deviation of :func:`~decitala.GeneralFragment.ql_array`.
		:rtype: float
		"""
		return np.std(self.ql_array())

	def c_score(self):
		"""
		:return: the c-score of the fragment, as defined in Povel and Essens (1985).
		:rtype: float
		:raises: NotImplementedError
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

	def augment(self, factor=1.0, difference=0.0):
		"""
		This method returns a new :obj:`~decitala.fragment.GeneralFragment` object with a ql_array
		corresponding to the original fragment augmented by a given ratio and difference.

		:param float factor: the factor by which the GeneralFragment will be augmented.
		:param float difference: the difference by which the GeneralFragment will be augmented.
		:rtype: :obj:`~decitala.fragment.GeneralFragment` object.

		>>> pre_augmentation = GeneralFragment([2.0, 2.0], name="Spondee")
		>>> pre_augmentation
		<fragment.GeneralFragment Spondee: [2. 2.]>
		>>> pre_augmentation.augment(factor=2.0, difference=0.75)
		<fragment.GeneralFragment Spondee/r:2.0/d:0.75: [4.75 4.75]>
		"""
		new_ql_array = utils.augment(self.ql_array(), factor=factor, difference=difference)
		new_name = self.name + "/r:{}/".format(factor) + "d:{}".format(difference)
		return GeneralFragment(new_ql_array, new_name)

	def show(self):
		if self.stream:
			return self.stream.show()

####################################################################################################
class Decitala(GeneralFragment):
	"""
	Class defining a Decitala object. The class reads from the fragments_db file in the
	databases directory (see the Decitalas table).

	:param str name: Name of the decitala, as is transliterated in the Lavignac (1921).
	:raises `~decitala.fragment.DecitalaException`: when there is an issue with the name.

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
	>>> # We can check if a fragment is a sub-fragment of another (meaning its
	>>> # successive_ratio_array appears inorder in another with the is_sub_fragment method.
	>>> Decitala("75_Pratapacekhara").is_sub_fragment(Decitala("Ragavardhana"), try_retrograde=True)
	True
	"""
	def __init__(self, name, **kwargs):
		conn = sqlite3.connect(fragment_db)
		cur = conn.cursor()

		decitala_table_string = "SELECT * FROM Decitalas"
		cur.execute(decitala_table_string)
		decitala_rows = cur.fetchall()

		matches = []
		for this_row in decitala_rows:
			x = re.search(name, this_row[0] + ".xml")
			if bool(x):
				matches.append(this_row[0])

		matches = [x + ".xml" for x in matches]

		if len(matches) == 0:
			raise DecitalaException("No matches were found for name {}.".format(name))

		if len(matches) == 1:
			match = matches[0]
			self.full_path = decitala_path + "/" + match
			self.name = match[:-4]
			self.filename = match
		elif len(matches) > 1:
			new_name = "".join([x for x in name if not x.isdigit()])
			if new_name[-4:] == ".xml":
				pass
			else:
				new_name = new_name + ".xml"

			if new_name[0] == "_":
				new_name = new_name[1:]
			new_name_split = new_name.split("_")

			for this_match in matches:
				match_new_name = "".join([x for x in this_match if not x.isdigit()])
				if match_new_name[0] == "_":
					match_new_name = match_new_name[1:]

				match_split = match_new_name.split("_")

				if match_split == new_name_split:
					self.full_path = decitala_path + "/" + this_match
					self.name = this_match[:-4]
					self.filename = this_match

		super().__init__(data=self.full_path, name=self.name)

	def __repr__(self):
		return '<fragment.Decitala {}>'.format(self.name)

	@property
	def id_num(self):
		"""
		:return: the ID of the fragment, as given by Lavignac (1921).
		:rtype: int
		"""
		idValue = re.search(r'\d+', self.name)
		return int(idValue.group(0))

	@classmethod
	def get_by_id(cls, input_id):
		"""
		A class method which retrieves a :obj:`~decitala.fragment.Decitala` object based \
		on a given ID number. These numbers are listed in the Lavignac Encyclopédie (1921) \
		and Messiaen Traité. Some talas have "sub-talas," meaning that their id is not \
		unique. Querying by those talas is currently not supported.

		:return: a :obj:`~decitala.fragment.Decitala` object
		:param int input_id: id number of the tala (in range 1-120).
		:rtype: :obj:`~decitala.fragment.Decitala`
		:raises `~decitala.fragment.DecitalaException`: when there is an issue with the `input_id`.

		>>> Decitala.get_by_id(89)
		<fragment.Decitala 89_Lalitapriya>
		"""
		assert type(input_id) == int
		if input_id > 121 or input_id < 1:
			raise DecitalaException("Input must be between 1 and 120.")
		elif input_id in subdecitala_array:
			raise DecitalaException("There are multiple talas with id: {}. \
									Please consult the Lavignac (1921).".format(input_id))

		conn = sqlite3.connect(fragment_db)
		cur = conn.cursor()
		decitala_table_string = "SELECT * FROM Decitalas"
		cur.execute(decitala_table_string)
		decitala_rows = cur.fetchall()

		for this_row in decitala_rows:
			name = this_row[0]
			split = name.split("_")
			id_num = int(split[0])
			if id_num == input_id:
				return Decitala(name=name)

	@property
	def carnatic_string(self):
		"""See docstring of :obj:`decitala.utils.ql_array_to_carnatic_string`."""
		return utils.ql_array_to_carnatic_string(self.ql_array())

	@property
	def num_matras(self):
		"""
		:return: returns the number of matras in the tala (here, the number of eighth notes).
		:rtype: int
		"""
		return (self.ql_duration / 0.5)

	def equivalents(self, rep_type="ratio"):
		"""
		:return: list of Decitala and Greek foot objects that are equivalent to the given fragment under \
				the provided ``rep_type``.
		:rtype: list

		>>> fragment = Decitala("Tritiya")
		>>> fragment.equivalents(rep_type="ratio")
		[<fragment.Decitala 95_Anlarakrida>]
		>>> fragment.equivalents(rep_type="difference")
		[<fragment.Decitala 76_Jhampa>, <fragment.Decitala 95_Anlarakrida>]
		"""
		assert rep_type.lower() in ["ratio", "difference"], DecitalaException("The only possible rep_types are \
																				`ratio` and `difference`")

		conn = sqlite3.connect(fragment_db)
		cur = conn.cursor()
		row_string = "SELECT * FROM Decitalas WHERE Name = '{}'".format(self.name)
		cur.execute(row_string)
		row_data = cur.fetchall()

		if rep_type == "ratio":
			r_equivalents = literal_eval(row_data[0][2])
			if r_equivalents:
				fragments = [Decitala(x[1]) if x[0] == "decitala" else GreekFoot(x[1]) for x in r_equivalents]
				return fragments
		if rep_type == "difference":
			d_equivalents = literal_eval(row_data[0][3])
			if d_equivalents:
				fragments = [Decitala(x[1]) if x[0] == "decitala" else GreekFoot(x[1]) for x in d_equivalents]
				return fragments

####################################################################################################
class GreekFoot(GeneralFragment):
	"""
	Class that stores greek foot data. The class reads from the fragments_db file in the databases
	directory (see the Greek_Metrics table).

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
		conn = sqlite3.connect(fragment_db)
		self.conn = conn
		cur = self.conn.cursor()

		greek_metric_table_string = "SELECT * FROM Greek_Metrics"
		cur.execute(greek_metric_table_string)
		greek_metric_rows = cur.fetchall()

		matches = []
		for this_row in greek_metric_rows:
			x = re.search(name, this_row[0] + ".xml")
			if bool(x):
				matches.append(this_row[0])

		matches = [x + ".xml" for x in matches]
		if len(matches) == 0:
			raise DecitalaException("No matches were found for name {}.".format(name))

		if len(matches) == 1:
			match = matches[0]
			self.full_path = greek_path + "/" + match
			self.name = match[:-4]
			self.filename = match
		else:
			if name[-4:] == ".xml":
				name = name[:-4]

			for this_match in matches:
				if name == this_match[:-4]:
					self.full_path = greek_path + "/" + this_match
					self.name = this_match[:-4]
					self.filename = this_match

		super().__init__(data=self.full_path, name=self.name)

	def __repr__(self):
		return '<fragment.GreekFoot {}>'.format(self.name)

	@property
	def greek_string(self):
		"""See docstring of :obj:`decitala.utils.ql_array_to_greek_diacritics`."""
		return utils.ql_array_to_greek_diacritics(self.ql_array())

	def equivalents(self, rep_type="ratio"):
		"""
		:return: list of Decitala and Greek foot objects that are equivalent to the given fragment under \
				the provided ``rep_type``.
		:rtype: list

		>>> fragment = GreekFoot("Ionic_Minor")
		>>> for equivalent in fragment.equivalents(rep_type="ratio"):
		... 	print(equivalent)
		<fragment.Decitala 49_Crikirti>
		<fragment.Decitala 32_Kudukka>
		<fragment.Decitala 9_Ratilila>
		<fragment.Decitala 36_Tribhangi>
		"""
		assert rep_type.lower() in ["ratio", "difference"], DecitalaException("The only possible rep_types \
																				are ratio and difference")

		cur = self.conn.cursor()
		row_string = "SELECT * FROM Greek_Metrics WHERE Name = '{}'".format(self.name)
		cur.execute(row_string)
		row_data = cur.fetchall()

		if rep_type == "ratio":
			r_equivalents = literal_eval(row_data[0][2])
			if r_equivalents:
				fragments = [GreekFoot(x[1]) if x[0] == "greek_foot" else Decitala(x[1]) for x in r_equivalents]
				return fragments
		if rep_type == "difference":
			d_equivalents = literal_eval(row_data[0][3])
			if d_equivalents:
				fragments = [GreekFoot(x[1]) if x[0] == "greek_foot" else Decitala(x[1]) for x in d_equivalents]
				return fragments