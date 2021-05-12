####################################################################################################
# File:     hash_table.py
# Purpose:  Hash table lookup algorithm for rhythmic search.
#
# Author:   Luke Poeppel
#
# Location: NYC, 2021.
####################################################################################################
import os

from .fragment import (
	Decitala,
	GreekFoot,
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

def _single_factor_or_difference_augmentation(
		fragment,
		ql_array,
		factor,
		difference,
		try_retrograde,
		dict_in,
		mode
	):
	searches = [ql_array]
	if try_retrograde is True:
		searches.append(ql_array[::-1])

	for i, search in enumerate(searches):
		retrograde = (i == 0)
		if mode == "multiplicative":
			augmentation = tuple(augment(ql_array=search, factor=factor, difference=0.0))
			elem_dict = {
				"fragment": fragment,
				"frag_type": fragment.frag_type,
				"retrograde": retrograde,
				"factor": factor,
				"difference": 0,
				"mod_hierarchy_val": 1 if retrograde is False else 2
			}
		elif mode == "additive":
			augmentation = tuple(augment(ql_array=search, factor=1.0, difference=difference))
			elem_dict = {
				"fragment": fragment,
				"frag_type": fragment.frag_type,
				"retrograde": retrograde,
				"factor": 1.0,
				"difference": difference,
				"mod_hierarchy_val": 3 if retrograde is False else 4
			}
		
		if augmentation in dict_in:
			existing = dict_in[augmentation]
			# Lower number -> More likely.
			if existing["mod_hierarchy_val"] < elem_dict["mod_hierarchy_val"]:
				continue
			else:
				dict_in[augmentation] = elem_dict
		else:
			dict_in[augmentation] = elem_dict

def generate_all_modifications(
		dict_in,
		fragment,
		factors,
		differences,
		try_retrograde,
		allow_mixed_augmentation=False,
		force_override=False
	):
	"""
	Helper function for generating and storing all possible modifications of an input fragment.

	:param dict dict_in: Dictionary storing all the results.
	:param `decitala.fragment.GeneralFragment` fragment: Fragment input.
	:param list factors: Possible factors for multiplicative augmentation.
	:param list differences: Possible differences for additive augmentation.
	:param bool try_retrograde: Whether to also generate modifications for the retrograde of
								the fragment.
	:param bool allow_mixed_augmentation: Whether to allow mixed augmentation as a
										modification type. Not yet supported.
	:param bool force_override: Whether to force the given fragment to override the
								existing fragment in the table (if it exists).
								Not yet supported.
	"""
	if allow_mixed_augmentation or force_override:
		raise HashTableException("These options are not yet supported. Coming soon.")

	ql_array = fragment.ql_array()
	for this_factor in factors:
		_single_factor_or_difference_augmentation(
			fragment=fragment,
			ql_array=ql_array,
			factor=this_factor,
			difference=0.0,
			try_retrograde=try_retrograde,
			dict_in=dict_in,
			mode="multiplicative"
		)

	# Next we form additive augmentations
	for this_difference in differences:
		_single_factor_or_difference_augmentation(
			fragment=fragment,
			ql_array=ql_array,
			factor=1.0,
			difference=this_difference,
			try_retrograde=try_retrograde,
			dict_in=dict_in,
			mode="additive"
		)

class FragmentHashTable:
	"""
	This class holds all (relevant) modifications of a set of fragments. Currently the only
	supported input types to ``datasets`` are ``"decitala"`` and ``"greek_foot"``. The
	``custom_fragments`` parameter allows the addition of any desired fragments; for a search
	on a particular set of fragments, use this latter parameter. The factors, differences,
	and other modification parameters are class attributes. To change them, subclass
	``FragmentHashTable`` with your own attributes.

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

	def __init__(self, datasets=[], custom_fragments=[]):
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
		self.data = dict()  # All the data will be stored here.

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
	
class DecitalaHashTable(FragmentHashTable):
	"""
	This class subclasses :obj:`decitala.hash_table.FragmentHashTable` with the ``datasets``
	parameter set to ``["decitala"]`` and automatically loads.
	"""
	def __init__(self):
		super().__init__(datasets=["decitala"])
		self.load()

class GreekFootHashTable(FragmentHashTable):
	"""
	This class subclasses :obj:`decitala.hash_table.FragmentHashTable` with the ``datasets``
	parameter set to ``["greek_foot"]`` and automatically loads.
	"""
	def __init__(self):
		super().__init__(datasets=["greek_foot"])
		self.load()

class AllCorporaHashTable(FragmentHashTable):
	"""
	This class subclasses :obj:`decitala.hash_table.FragmentHashTable` with the ``datasets``
	parameter set to all available datasets in the ``corpora`` directory and automatically loads.
	"""
	def __init__(self):
		super().__init__(datasets=["greek_foot", "decitala"])
		self.load()