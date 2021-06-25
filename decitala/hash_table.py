####################################################################################################
# File:     hash_table.py
# Purpose:  Hash table lookup algorithm for rhythmic search.
#
# Author:   Luke Poeppel
#
# Location: NYC, 2021.
####################################################################################################
from .fragment import (
	get_all_decitalas,
	get_all_greek_feet,
	get_all_prosodic_fragments
)
from .utils import (
	augment,
	stretch_augment,
	get_logger
)

logger = get_logger(name=__file__, print_to_console=True)

MODIFICATION_HIERARCHY = {
	"ratio": 1,
	"retrograde-ratio": 2,
	"difference": 3,
	"retrograde-difference": 4,
	"subdivision-ratio": 5,
	"retrograde-subdivision-ratio": 6,
	"stretch": 7,
	"retrograde-stretch": 8,
	"mixed": 9,
	"retrograde-mixed": 10
}

# Defaults
FACTORS = [0.125, 0.1875, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
DIFFERENCES = [-0.375, -0.25, -0.125, 0.0, 0.125, 0.25, 0.375, 0.5, 0.75, 0.875, 1.75, 2.625, 3.5, 4.375] # noqa
TRY_RETROGRADE = True
ALLOW_MIXED_AUGMENTATION = False
ALLOW_STRETCH_AUGMENTATION = True
CUSTOM_OVERRIDES_DATASETS = False

class HashTableException(Exception):
	pass

def _is_proper_stretch_augmentation(ql_array, factor, other_factor):
	"""Checks if a stretch augmentation is 'valid'"""
	return (max(ql_array) * other_factor) > (min(ql_array) * factor)

def _single_factor_or_difference_augmentation(
		fragment,
		factor,
		stretch_factor,
		difference,
		try_retrograde,
		dict_in,
		mode
	):
	ql_array = fragment.ql_array()
	ql_arrays = [ql_array]
	if try_retrograde is True:
		ql_arrays.append(ql_array[::-1])

	for i, ql_array in enumerate(ql_arrays):
		retrograde = False if i == 0 else True
		elem_dict = {
			"fragment": fragment,
			"retrograde": retrograde,
		}
		if mode == "multiplicative":
			augmentation = tuple(augment(ql_array=ql_array, factor=factor, difference=difference))
			elem_dict["factor"] = factor
			elem_dict["difference"] = difference
			elem_dict["mod_hierarchy_val"] = 1 if retrograde is False else 2
		elif mode == "additive":
			augmentation = tuple(augment(ql_array=ql_array, factor=factor, difference=difference))
			elem_dict["factor"] = factor
			elem_dict["difference"] = difference
			elem_dict["mod_hierarchy_val"] = 3 if retrograde is False else 4
		elif mode == "stretch":
			stretch_augmentation = stretch_augment(
				ql_array=ql_array,
				factor=factor,
				stretch_factor=stretch_factor
			)
			augmentation = tuple(stretch_augmentation)
			elem_dict["factor"] = factor
			elem_dict["stretch_factor"] = stretch_factor
			elem_dict["difference"] = difference
			elem_dict["mod_hierarchy_val"] = 7 if retrograde is False else 8

		# No ql-arrays should have quarter lengths of 0.
		if any(x <= 0 for x in augmentation):
			continue

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
		allow_stretch_augmentation,
		allow_mixed_augmentation,
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

	for this_factor in factors:
		_single_factor_or_difference_augmentation(
			fragment=fragment,
			factor=this_factor,
			difference=0.0,
			stretch_factor=1,
			try_retrograde=try_retrograde,
			dict_in=dict_in,
			mode="multiplicative"
		)

	for this_difference in differences:
		_single_factor_or_difference_augmentation(
			fragment=fragment,
			factor=1.0,
			difference=this_difference,
			stretch_factor=1,
			try_retrograde=try_retrograde,
			dict_in=dict_in,
			mode="additive"
		)

	# Stretch Augmentation (this should be cleaned up somehow...)
	if allow_stretch_augmentation:
		if fragment.frag_type == "greek_foot":
			for this_factor in factors:
				for this_other_factor in factors:
					if not(_is_proper_stretch_augmentation(fragment.ql_array(), this_factor, this_other_factor)):
						continue
					_single_factor_or_difference_augmentation(
						fragment=fragment,
						factor=this_factor,
						difference=0,
						stretch_factor=this_other_factor,
						try_retrograde=try_retrograde,
						dict_in=dict_in,
						mode="stretch"
					)

class FragmentHashTable:
	"""
	This class holds all (relevant) modifications of a set of fragments. Currently the only
	supported input types to ``datasets`` are ``"decitala"`` and ``"greek_foot"``. The
	``custom_fragments`` parameter allows the addition of any desired fragments; for a search
	on a particular set of fragments, use this latter parameter. The factors, differences,
	and other modification parameters are instance attributes with defaults set in the module.
	To change them, just re-run the ``load`` method with the desired inputs; this will clear the
	data and set reload it with the new desired modification techniques.

	>>> from decitala.fragment import Decitala
	>>> fht = FragmentHashTable(
	... 	datasets=["greek_foot"],
	... 	custom_fragments=[Decitala("Ragavardhana")]
	... )
	>>> # The object doesn't store anything until it is loaded.
	>>> fht
	<decitala.hash_table.FragmentHashTable 0 fragments>
	>>> fht.load()
	>>> fht
	<decitala.hash_table.FragmentHashTable 2899 fragments>
	>>> fht.datasets
	['greek_foot']
	>>> fht.custom_fragments
	[<fragment.Decitala 93_Ragavardhana>]
	>>> fht.data[(3.0, 0.5, 0.75, 0.5)]["fragment"]
	<fragment.Decitala 93_Ragavardhana>
	>>> peon_check = fht.data[(2.0, 2.0, 2.0, 4.0)]
	>>> peon_check["fragment"].name == "Peon_IV"
	True
	"""
	factors = FACTORS
	differences = DIFFERENCES
	try_retrograde = TRY_RETROGRADE
	allow_mixed_augmentation = ALLOW_MIXED_AUGMENTATION
	allow_stretch_augmentation = ALLOW_STRETCH_AUGMENTATION
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
			allow_stretch_augmentation=ALLOW_STRETCH_AUGMENTATION,
			allow_mixed_augmentation=ALLOW_MIXED_AUGMENTATION,
			modification_hierarchy=MODIFICATION_HIERARCHY,
			force_override=CUSTOM_OVERRIDES_DATASETS
		):
		"""
		Function for loading the modifications. Allows the user to override the default attributes.
		"""
		self.data.clear()  # Clears the data first in case it is reloaded with new parameters.
		for this_fragment in self.custom_fragments:
			generate_all_modifications(
				dict_in=self.data,
				fragment=this_fragment,
				factors=factors,
				differences=differences,
				try_retrograde=try_retrograde,
				allow_stretch_augmentation=allow_stretch_augmentation,
				allow_mixed_augmentation=allow_mixed_augmentation,
				force_override=force_override
			)

		# Process datasets
		for this_dataset in self.datasets:
			if this_dataset == "greek_foot":
				fragments = get_all_greek_feet()
			elif this_dataset == "decitala":
				fragments = get_all_decitalas()
			elif this_dataset == "prosodic_fragment":
				fragments = get_all_prosodic_fragments()

			for this_fragment in fragments:
				generate_all_modifications(
					dict_in=self.data,
					fragment=this_fragment,
					factors=factors,
					differences=differences,
					try_retrograde=try_retrograde,
					allow_stretch_augmentation=allow_stretch_augmentation,
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
	parameter set to ``["greek_foot"]`` and automatically loads. If you want to reload it
	with default modification techniques changed, simply run ``load`` with the desired
	parameters.

	>>> ght = GreekFootHashTable()
	>>> ght
	<decitala.hash_table.FragmentHashTable 2855 fragments>
	>>> ght.load(try_retrograde=False, allow_stretch_augmentation=False)
	>>> ght
	<decitala.hash_table.FragmentHashTable 737 fragments>
	"""
	def __init__(self):
		super().__init__(datasets=["greek_foot"])
		self.load()

class ProsodicFragmentHashTable(FragmentHashTable):
	"""
	This class subclasses :obj:`decitala.hash_table.FragmentHashTable` with the ``datasets``
	parameter set to ``["prosodic_fragment"]`` and automatically loads.
	"""
	def __init__(self):
		super().__init__(datasets=["prosodic_fragment"])
		self.load()

class AllCorporaHashTable(FragmentHashTable):
	"""
	This class subclasses :obj:`decitala.hash_table.FragmentHashTable` with the ``datasets``
	parameter set to all available datasets in the ``corpora`` directory and automatically loads.
	"""
	def __init__(self):
		super().__init__(datasets=["greek_foot", "decitala", "prosodic_fragment"])
		self.load()