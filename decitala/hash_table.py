####################################################################################################
# File:     hash_table.py
# Purpose:  Hash table lookup algorithm for rhythmic search.
#
# Author:   Luke Poeppel
#
# Location: NYC, 2021.
####################################################################################################
import os
import json

from .fragment import (
	Decitala,
	GreekFoot,
	GeneralFragment
)
from .utils import (
	augment,
	get_logger
)
from .corpora_models import (
	get_engine,
	get_session,
	GreekFootData,
	DecitalaData
)

here = os.path.abspath(os.path.dirname(__file__))
fragment_db = os.path.dirname(here) + "/databases/fragment_database.db"

engine = get_engine(fragment_db)
session = get_session(engine=engine)

logger = get_logger(name=__file__, print_to_console=True)

MODIFICATION_HIERARCHY = {
	"ratio": 1,
	"retrograde-ratio": 2,
	"difference": 3,
	"retrograde-difference": 4,
	"subdivision-ratio": 5,
	"retrograde-subdivision-ratio": 6,
	"mixed": 7,
	"retrograde-mixed": 8
}

FACTORS = [0.125, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
DIFFERENCES = [-0.375, -0.25, -0.125, 0.0, 0.125, 0.25, 0.375, 0.5, 0.75, 0.875, 1.75, 2.625, 3.5, 4.375] # noqa
TRY_RETROGRADE = True
ALLOW_MIXED_AUGMENTATION = False
CUSTOM_OVERRIDES_DATASETS = False

class HashTableException(Exception):
	pass

def generate_all_modifications(
		dict_in,
		fragment,
		factors,
		differences,
		try_retrograde,
		allow_mixed_augmentation,
		force_override
	):
	"""
	Helper function for generating and storing all possible modifications of an input fragment.

	:param dict dict_in: Dictionary storing all the results. 
	:param `decitala.fragment.GeneralFragment` fragment:
	"""
	if allow_mixed_augmentation or force_override:
		raise HashTableException("That is not yet supported. Coming soon.")

	qls = fragment.ql_array()

	# First we form multiplicative augmentations
	for this_factor in factors:
		searches = [qls]
		if try_retrograde is True:
			searches.append(qls[::-1])
		
		for i, search in enumerate(searches):
			augmentation = tuple(augment(fragment=search, factor=this_factor, difference=0.0))

			if i == 0:
				retrograde = False
			else:
				retrograde = True

			elem_dict = {
				"fragment": fragment,
				"frag_type": fragment.frag_type,
				"retrograde": retrograde,
				"factor": this_factor,
				"difference": 0,
				"mod_hierarchy_val": 1 if retrograde is False else 2
			}
			if str(augmentation) in dict_in:
				existing = dict_in[str(augmentation)]
				# Lower number -> More likely. 
				if existing["mod_hierarchy_val"] < elem_dict["mod_hierarchy_val"]:
					continue
				else:
					dict_in[augmentation] = elem_dict
			else:
				dict_in[augmentation] = elem_dict

	# Next we form additive augmentations
	for this_difference in differences:
		searches = [qls]
		if retrograde is True:
			searches.append(qls[::-1])
		for i, search in enumerate(searches):
			augmentation = tuple(augment(fragment=search, factor=1.0, difference=this_difference))
			if any(x <= 0 for x in augmentation):
				continue

			if i == 0:
				retrograde = False
			else:
				retrograde = True

			elem_dict = {
				"fragment": fragment,
				"frag_type": fragment.frag_type,
				"retrograde": retrograde,
				"factor": this_difference,
				"difference": 0,
				"mod_hierarchy_val": 3 if retrograde is False else 4
			}
			# Lower number -> More likely. 
			if augmentation in dict_in:
				existing = dict_in[augmentation]
				if existing["mod_hierarchy_val"] < elem_dict["mod_hierarchy_val"]:
					continue
			else:
				dict_in[augmentation] = elem_dict

class FragmentHashTable:
	"""
	This class holds all (relevant) modifications of a set of fragments. This, used in conjunction with
	the input table to rolling_hash_search, allows the user to make more complicated queries. 
	>>> fht = FragmentHashTable(
	... 	datasets=["greek_foot"],
	... 	custom_fragments=[Decitala("Ragavardhana")]
	... )
	>>> # The object doesn't store anything until it is loaded. 
	>>> fht
	<decitala.hash_table.FragmentHashTable 0 fragments>
	>>> fht.load()
	>>> fht
	<decitala.hash_table.FragmentHashTable 731 fragments>
	>>> fht.datasets
	['greek_foot']
	>>> fht.custom_fragments
	[<fragment.Decitala 93_Ragavardhana>]
	"""
	factors = FACTORS
	differences = DIFFERENCES
	try_retrograde = TRY_RETROGRADE
	allow_mixed_augmentation = ALLOW_MIXED_AUGMENTATION
	modification_hierarchy = MODIFICATION_HIERARCHY
	custom_overrides_datasets = CUSTOM_OVERRIDES_DATASETS

	def __init__(self, datasets = [], custom_fragments = []):
		"""
		General object for storing all modifications of rhythmic datasets. Does not load the 
		modifications by default. 

		:param list datasets: optional elements from `decitala`'s built-in datasets. Currently 
							includes `decitala` and `greek_foot`. 
		:param list custom_fragment: optional list of extra fragments to be included in the
									datasets. If you wish for the custom fragments to override
									the dataset fragments, you must create a new class inheriting
									from `FragmentHashTable` that sets the class attribute 
									`custom_overrides_datasets=True`. 
		"""
		self.datasets = datasets
		self.custom_fragments = custom_fragments
		self.loaded = False
		self.data = dict() # All the data will be stored here. 

	def __repr__(self):
		return f"<decitala.hash_table.FragmentHashTable {len(self.data)} fragments>"

	def load(
			self,
			factors=FACTORS,
			differences=DIFFERENCES,
			try_retrograde=TRY_RETROGRADE,
			allow_mixed_augmentation=ALLOW_MIXED_AUGMENTATION,
			modification_hierarchy=MODIFICATION_HIERARCHY,
			force_override=CUSTOM_OVERRIDES_DATASETS
		):
		for this_fragment in self.custom_fragments:
			generate_all_modifications(
				dict_in=self.data,
				fragment=this_fragment,
				factors=factors,
				differences=differences,
				try_retrograde=try_retrograde,
				allow_mixed_augmentation=allow_mixed_augmentation,
				force_override=force_override
			)
		
		for this_dataset in self.datasets:
			if this_dataset == "greek_foot":
				data = session.query(GreekFootData).all()
				fragments = [GreekFoot(x.name) for x in data]

			if this_dataset == "decitala":
				data = session.query(DecitalaData).all()
				fragments = [Decitala(x.name) for x in data]

			for this_fragment in fragments:
				generate_all_modifications(
					dict_in=self.data,
					fragment=this_fragment,
					factors=factors,
					differences=differences,
					try_retrograde=try_retrograde,
					allow_mixed_augmentation=allow_mixed_augmentation,
					force_override=force_override
				)

		self.loaded = True

	def data(self):
		if not self.data:
			self.load_modifications()
			return self.data
		else:
			return self.data

class DecitalaHashTable(FragmentHashTable):
	def __init__(self):
		super().__init__(datasets=["decitala"])
		self.load()

class GreekFootHashTable(FragmentHashTable):
	def __init__(self):
		super().__init__(datasets=["greek_foot"])
		self.load()