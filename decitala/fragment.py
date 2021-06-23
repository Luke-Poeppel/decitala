####################################################################################################
# File:     fragment.py
# Purpose:  (OOP) Tools for dealing with generic rhythmic fragments, as well as those used
# 			specifically by Messiaen.
#
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020 / NYC, 2021
####################################################################################################
import json
import numpy as np
import os
import unidecode

from collections import Counter
from functools import lru_cache

from music21 import converter
from music21 import note

from . import utils
from .database.corpora_models import (
	DecitalaData,
	GreekFootData,
	ProsodicFragmentData,
)
from .database.db_utils import get_session

# Fragments
here = os.path.abspath(os.path.dirname(__file__))
decitala_path = os.path.dirname(here) + "/corpora/Decitalas"
greek_path = os.path.dirname(here) + "/corpora/Greek_Metrics"
prosody_path = os.path.dirname(here) + "/corpora/Prosody"

fragment_db = os.path.dirname(here) + "/databases/fragment_database.db"

# ID's of decitalas with "subtalas"
subdecitala_array = np.array([26, 38, 55, 65, 68])

session = get_session(db_path=fragment_db)

####################################################################################################
class FragmentException(Exception):
	pass

class DecitalaException(FragmentException):
	pass

class GreekFootException(FragmentException):
	pass

class ProsodicException(FragmentException):
	pass

# Serialization
class FragmentEncoder(json.JSONEncoder):
	def default(self, obj):
		if type(obj) == GeneralFragment:
			if isinstance(obj.data, str):
				d = {
					"frag_type": "general_fragment",
					"data": obj.data,
					"name": obj.name  # May be None!
				}
			else:
				data = list(obj.data)  # numpy array is not JSON serializable.
				d = {
					"frag_type": "general_fragment",
					"data": data,
					"name": obj.name  # May be None!
				}
			return d
		elif type(obj) == Decitala:
			d = {
				"frag_type": "decitala",
				"name": obj.name
			}
			return d
		elif type(obj) == GreekFoot:
			d = {
				"frag_type": "greek_foot",
				"name": obj.name
			}
			return d

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
			if obj["frag_type"] == "general_fragment":
				return GeneralFragment(data=obj["data"], name=obj["name"])
			elif obj["frag_type"] == "decitala" and obj["name"] is not None:
				return Decitala(obj["name"])
			elif obj["frag_type"] == "greek_foot" and obj["name"] is not None:
				return GreekFoot(obj["name"])
		except KeyError:
			return obj

def _process_matches(name, matches, data_path):
	if len(matches) == 1:
		match = matches[0]
		full_path = data_path + "/" + match
		name = match[:-4]
		filename = match
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
				full_path = data_path + "/" + this_match
				name = this_match[:-4]
				filename = this_match

	return full_path, name, filename

def _decitala_full_id_from_filename(filename):
	split = filename.split("_")
	if len(split) == 2:
		full_id = split[0]
	elif len(split) >= 3:
		if len(split[1]) == 1:  # e.g. ["80", "B", "..."]
			full_id = "_".join([split[0], split[1]])
		else:
			full_id = split[0]

	return full_id

class GeneralFragment:
	"""
	Class representing a generic rhythmic fragment. The user must provide either a path to a music21
	readable file or an array of quarter length values.

	:param data: Either an array of quarter length values or a path to a music21 readable file.
	:param str name: Optional name.
	:raises `~decitala.fragment.FragmentException`: If an array **and** file are provided or if
													neither are provided.

	>>> random_fragment_path = "./corpora/Decitalas/63_Nandi.xml"
	>>> g1 = GeneralFragment(data=random_fragment_path, name='MyNandi')
	>>> g1
	<fragment.GeneralFragment MyNandi: [0.5  0.25 0.25 0.5  0.5  1.   1.  ]>
	>>> g1.filename
	'63_Nandi.xml'
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
	>>> # We can also initialize with an array.
	>>> GeneralFragment(data=np.array([0.75, 0.75, 0.5, 0.25]))
	<fragment.GeneralFragment: [0.75 0.75 0.5  0.25]>
	>>> # We can also set keyword arguments
	>>> g1.coolness_level = 'pretty cool'
	>>> g1.coolness_level
	'pretty cool'
	"""
	frag_type = "general_fragment"

	def __init__(self, data, name=None, **kwargs):
		if isinstance(data, str):
			assert os.path.isfile(data), FragmentException("The input data is not a file.")
			self.filepath = data
			self.filename = self.filepath.split("/")[-1]
			self.data = data
		elif isinstance(data, np.ndarray) or isinstance(data, list):
			assert len(data) >= 1
			self.data = np.array(data)
		else:
			raise FragmentException(f"{data} is an invalid input to GeneralFragment.")

		self.name = name

	def __repr__(self):
		if self.name is None:
			return f"<fragment.GeneralFragment: {self.ql_array()}>"
		else:
			return f"<fragment.GeneralFragment {self.name}: {self.ql_array()}>"

	def __hash__(self):
		lil_repr = "-".join([str(self.name), str(self.data)])
		return hash(lil_repr)

	def __eq__(self, other):
		if self.__hash__() == other.__hash__():
			return True
		else:
			return False

	@lru_cache(maxsize=None)
	def ql_array(self, retrograde=False):
		"""
		:param bool retrograde: Whether to return the fragment in its original form or
								in retrograde.
		:return: The quarter length array of the fragment.
		:rtype: numpy.array
		"""
		if isinstance(self.data, str):
			converted = converter.parse(self.data)
			data = np.array([this_note.quarterLength for this_note in converted.flat.getElementsByClass(note.Note)]) # noqa
			if not(retrograde):
				return data
			else:
				return np.flip(data)
		else:

			if not(retrograde):
				return self.data
			else:
				return np.flip(self.data)

	@lru_cache(maxsize=None)
	def ql_tuple(self, retrograde=False):
		"""
		:param bool retrograde: Whether to return the fragment in retrograde.
		:return: The quarter length array of the fragment as a tuple.
		:rtype: tuple
		"""
		return tuple(self.ql_array(retrograde=retrograde))

	@property
	def carnatic_string(self):
		"""See docstring of :obj:`decitala.utils.ql_array_to_carnatic_string`."""
		return utils.ql_array_to_carnatic_string(self.ql_array())

	@property
	def greek_string(self):
		"""See docstring of :obj:`decitala.utils.ql_array_to_greek_diacritics`."""
		return utils.ql_array_to_greek_diacritics(self.ql_array())

	@property
	@lru_cache(maxsize=None)  # Caching *extremely* useful for cost function in path-finding.
	def num_onsets(self):
		"""
		:return: The number of onsets in the fragment.
		:rtype: int
		"""
		return len(self.ql_array())

	@property
	def num_anga_classes(self):
		"""
		:return: The number of anga classes in the fragment (the number of unique rhythmic values).
		:rtype: int

		>>> GeneralFragment(data=np.array([0.75, 0.75, 0.5, 0.25])).num_anga_classes
		3
		"""
		return len(set(self.ql_array()))

	@property
	def ql_duration(self):
		"""
		:return: The overall duration of the fragment (expressed in quarter lengths).
		:rtype: float
		"""
		return sum(self.ql_array())

	def split(self, *args):
		full_qls = utils.flatten([list(fragment.ql_array()) for fragment in args])
		assert full_qls == list(self.ql_array())
		return [fragment for fragment in args]

	def dseg(self, reduced=False, as_str=False):
		"""See docstring of :obj:`decitala.utils.dseg`."""
		return utils.dseg(self.ql_array(), reduced=reduced, as_str=as_str)

	def successive_ratio_array(self, retrograde=False):
		"""See docstring of :obj:`decitala.utils.successive_ratio_array`."""
		return utils.successive_ratio_array(self.ql_array(retrograde=retrograde))

	def successive_difference_array(self, retrograde=False):
		"""See docstring of :obj:`decitala.utils.successive_difference_array`."""
		return utils.successive_difference_array(self.ql_array(retrograde=retrograde))

	def cyclic_permutations(self):
		"""
		:return: All cyclic permutations of :obj:`~decitala.fragment.Decitala.ql_array`,
				as in Morris (1998).
		:rtype: numpy.array
		"""
		return np.array([np.roll(self.ql_array(), -i) for i in range(self.num_onsets)])

	@property
	def is_non_retrogradable(self):
		"""
		:return: Whether or not the given fragment is palindromic (i.e. non-retrogradable.)
		:rtype: bool
		"""
		return (self.ql_array(retrograde=False) == self.ql_array(retrograde=True)).all()

	def anga_class_counter(self):
		"""
		:return: A counter of the elements from `:meth:decitala.fragment.ql_array`.
		:rtype: collections.Counter
		"""
		return Counter(self.ql_array())

	def is_sub_fragment(self, other, try_retrograde=True):
		"""
		:param other: A :obj:`~decitala.fragment.GeneralFragment`, :obj:`~decitala.fragment.Decitala`, \
						or :obj:`~decitala.fragment.GreekFoot` object.
		:param bool try_retrograde: Whether to allow searching in retrograde.
		:return: Whether or not self is a sub-fragment of `other`.
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
		:return: The fragment's form of rhythmic symmetry, as defined by Morris in \
				`Sets, Scales and Rhythmic Cycles. A Classification of Talas in Indian \
				Music <http://ecmc.rochester.edu/rdm/pdflib/talapaper.pdf>`_ (1999).
		:rtype: int

		- I. Maximally Trivial:				of the form :math:`X` (one onset, one anga class)
		- II. Trivial Dual Symmetry:  		of the form :math:`XY`
		- III. Trivial Symmetry: 			of the form :math:`XXXXXX`
		- IV. Maximally Trivial Palindrome: of the form :math:`XXX...XYX...XXX`
		- V. Trivial Dual Palindromic:		of the form :math:`XXX...XYYYX...XXX`
		- VI. Palindromic: 					of the form :math:`XY...Z...YX`
		- VII. Stream:						of the form :math:`XYZ...abc...`
		"""
		dseg = list(self.dseg())
		centrish_element = self.ql_array()[self.num_onsets // 2]

		if self.num_onsets == 1:
			return 1
		if self.num_onsets == 2 and self.num_anga_classes == 2:
			return 2
		elif self.num_anga_classes == 1 and self.num_onsets > 1:
			return 3
		elif dseg == dseg[::-1] and self.anga_class_counter()[centrish_element] == 1:
			return 4
		elif dseg == dseg[::-1] and self.anga_class_counter()[centrish_element] > 1:
			return 5
		elif self.is_non_retrogradable:
			return 6
		else:
			return 7

	def std(self):
		"""
		:return: The standard deviation of :func:`~decitala.GeneralFragment.ql_array`.
		:rtype: float
		"""
		return np.std(self.ql_array())

	def c_score(self):
		"""
		:return: The c-score of the fragment, as defined in Povel and Essens (1985).
		:rtype: float
		:raises: NotImplementedError
		"""
		raise NotImplementedError

	def nPVI(self):
		"""
		:return: The nPVI of the fragment (Low, Grabe, & Nolan, 2000).
		:rtype: float
		"""
		assert len(self.ql_array()) > 1

		IOI = self.ql_array()
		summation = 0
		prev = IOI[0]
		for i in range(1, self.num_onsets):
			curr = IOI[i]
			if curr > 0 and prev > 0:
				summation += abs(curr - prev) / ((curr + prev) / 2.0)
			else:
				pass
			prev = curr

		final = summation * 100 / (self.num_onsets - 1)

		return final

	def augment(self, factor=1.0, difference=0.0):
		"""
		This method returns a new :obj:`~decitala.fragment.GeneralFragment` object with a ql_array
		corresponding to the original fragment augmented by a given ratio and difference.

		:param float factor: The factor by which the GeneralFragment will be augmented.
		:param float difference: The difference by which the GeneralFragment will be augmented.
		:rtype: :obj:`~decitala.fragment.GeneralFragment` object.

		>>> pre_augmentation = GeneralFragment([2.0, 2.0], name="Spondee")
		>>> pre_augmentation
		<fragment.GeneralFragment Spondee: [2. 2.]>
		>>> pre_augmentation.augment(factor=2.0, difference=0.75)
		<fragment.GeneralFragment Spondee/r:2.0/d:0.75: [4.75 4.75]>
		"""
		new_ql_array = utils.augment(ql_array=self.ql_array(), factor=factor, difference=difference)
		new_name = self.name + "/r:{}/".format(factor) + "d:{}".format(difference)
		return GeneralFragment(new_ql_array, new_name)

	def show(self):
		if isinstance(self.data, str):
			converted = converter.parse(self.data)
			converted.show()
		else:
			FragmentException(f"Can't show {self.data}.")

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
	'93'
	>>> ragavardhana.num_onsets
	4
	>>> ragavardhana.ql_array()
	array([0.25 , 0.375, 0.25 , 1.5  ])
	>>> ragavardhana.successive_ratio_array()
	array([1.        , 1.5       , 0.66666667, 6.        ])
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
	7
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
	frag_type = "decitala"

	def __init__(self, name, **kwargs):
		if name.endswith(".xml"):
			name = name[:-4]

		matches = session.query(DecitalaData).filter(DecitalaData.name.contains(name)).all()
		matches = [x.name + ".xml" for x in matches]

		if not matches:
			raise DecitalaException(f"No matches were found for name {name}.")

		full_path, name, filename = _process_matches(name, matches, decitala_path)
		self.full_path = full_path
		self.filename = filename

		super().__init__(data=full_path, name=name)

	def __repr__(self):
		return f"<fragment.Decitala {self.name}>"

	@property
	def id_num(self):
		"""
		:return: The ID of the fragment, as given by Lavignac (1921).
		:rtype: int
		"""
		return _decitala_full_id_from_filename(self.filename)

	@classmethod
	def get_by_id(cls, input_id):
		"""
		A class method which retrieves a :obj:`~decitala.fragment.Decitala` object based
		on a given ID number. These numbers are listed in the Lavignac Encyclopédie (1921)
		and Messiaen Traité. Some talas have "sub-talas," meaning that their id is not
		unique.

		:return: A :obj:`~decitala.fragment.Decitala` object
		:param str input_id: The ID number of the tala (in range 1-120).
		:rtype: :obj:`~decitala.fragment.Decitala`
		:raises `~decitala.fragment.DecitalaException`: when there is an issue with the `input_id`.

		>>> Decitala.get_by_id("89")
		<fragment.Decitala 89_Lalitapriya>
		"""
		res = session.query(DecitalaData).filter(DecitalaData.full_id == input_id).all()
		if len(res) > 1:
			raise DecitalaException("Something is wrong. File an issue at https://github.com/Luke-Poeppel/decitala/issues.") # noqa
		return Decitala(res[0].name)

	@property
	def num_matras(self):
		"""
		:return: Returns the number of matras in the tala (here, the number of eighth notes).
		:rtype: int
		"""
		return (self.ql_duration / 0.5)

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
	frag_type = "greek_foot"

	def __init__(self, name, **kwargs):
		if name.endswith(".xml"):
			name = name[:-4]
		matches = session.query(GreekFootData).filter(GreekFootData.name == name).all()
		matches = [x.name + ".xml" for x in matches]

		if not matches:
			raise GreekFootException(f"No matches were found for name {name}.")

		full_path, name, filename = _process_matches(name, matches, greek_path)
		self.full_path = full_path

		super().__init__(data=full_path, name=name)

	def __repr__(self):
		return f"<fragment.GreekFoot {self.name}>"

class Breve(GeneralFragment):
	frag_type = "breve"

	def __init__(self, **kwargs):
		super().__init__(data=[1.0], name="Breve")

class Macron(GeneralFragment):
	frag_type = "macron"

	def __init__(self, **kwargs):
		super().__init__(data=[2.0], name="Macron")

class ProsodicFragment(GeneralFragment):
	"""
	Class that stores prosodic data. The class reads from the fragments_db file in the databases
	directory (see the ProsodicFragments table).

	# >>> asclepiad_m = ProsodicFragment("Asclépiade_Mineur")
	# >>> asclepiad_m
	# <fragment.ProsodicFragment Asclépiade_Mineur>
	"""
	frag_type = "prosodic_fragment"

	def __init__(self, name, **kwargs):
		if name.endswith(".xml"):
			name = name[:-4]

		name = unidecode.unidecode(name)
		match = session.query(ProsodicFragmentData).filter(ProsodicFragmentData.name == name).first()
		if not match:
			raise ProsodicException(f"No matches were found for name {name}.")

		match_name = unidecode.unidecode(match.name) + ".xml"
		full_path = "/".join([prosody_path, match.source, match_name])
		name = match_name[:-4]

		self.source = match.source
		self.full_path = full_path

		super().__init__(data=full_path, name=name)

	def __repr__(self):
		return f"<fragment.ProsodicFragment {self.name}>"

# class TheorieKarnatique(GeneralFragment):
# 	pass

####################################################################################################
# Some simple queries for quick access.
def get_all_greek_feet():
	all_greek_feet = session.query(GreekFootData)
	return [GreekFoot(x.name) for x in all_greek_feet]

def get_all_decitalas():
	all_decitalas = session.query(DecitalaData)
	return [Decitala(x.name) for x in all_decitalas]

def get_all_prosodic_fragments():
	all_prosodic_fragments = session.query(ProsodicFragmentData)
	return [ProsodicFragment(x.name) for x in all_prosodic_fragments]