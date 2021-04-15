####################################################################################################
# File:     search.py
# Purpose:  Search algorithms.
#
# Author:   Luke Poeppel
#
# Location: NYC, 2020-21 / Kent, 2021
####################################################################################################
"""
Search algorithms.
"""
import copy
import numpy as np

from .utils import (
	successive_ratio_array,
	successive_difference_array,
	find_possible_superdivisions,
	get_object_indices,
	roll_window,
	frame_to_ql_array,
	frame_is_spanned_by_slur,
	contiguous_summation,
	frame_to_midi,
)
from .fragment import (
	Decitala,
	GreekFoot,
)
from .hash_table import (
	DecitalaHashTable,
	GreekFootHashTable
)
from .path_finding import floyd_warshall

__all__ = [
	"get_by_ql_array",
	"rolling_search",
	"rolling_hash_search"
]

####################################################################################################
class SearchException(Exception):
	pass

class _SearchConfig():
	"""Helper class for managing relationship between search ql_arrays and search trees."""
	def __init__(self, ql_array, ratio_tree=None, difference_tree=None, modifications=[]):
		self.ql_array = ql_array

		if ratio_tree is None and difference_tree is None:
			raise SearchException("You need to provide at least one tree.")

		self.ratio_tree = ratio_tree
		self.difference_tree = difference_tree

		# Check agreement between provided FragmentTree(s) and provided modifications.
		assert set(modifications).issubset({"r", "rr", "d", "rd", "sr", "rsr"}), SearchException("Current supported searches are r, rr, d, rd, sr, rsr.") # noqa
		assert len(set(modifications)) == len(modifications), SearchException("You have a duplicate element in your allowed modifications.") # noqa
		self.modifications = modifications

		if (len(set(self.modifications).intersection({"r", "rr", "sr", "rsr"})) != 0) and self.ratio_tree is None: # noqa
			raise SearchException("You did not provide a ratio FragmentTree.")
		if (len(set(self.modifications).intersection({"d", "rd"})) != 0) and self.difference_tree is None:
			raise SearchException("You did not provide a difference FragmentTree.")

	def __repr__(self):
		return "<_SearchConfig: {}>".format(self.modifications)

	def __getitem__(self, modification):
		if modification not in self.modifications:
			raise Exception("'{0}' is not in '{1}'".format(modification, self.modifications))

		retrograde = self.ql_array[::-1]

		ratio_array = successive_ratio_array(self.ql_array)
		difference_array = successive_difference_array(self.ql_array)
		retrograde_ratio_array = successive_ratio_array(retrograde)
		retrograde_difference_array = successive_difference_array(retrograde)

		all_superdivisions = find_possible_superdivisions(self.ql_array)
		superdivisions_ratio = [successive_ratio_array(x) for x in all_superdivisions]
		retrograde_superdivisions_pre = [x[::-1] for x in all_superdivisions]
		retrograde_superdivisions_ratio = [successive_ratio_array(x) for x in retrograde_superdivisions_pre] # noqa

		if modification == "r":
			return (self.ratio_tree, ratio_array)
		elif modification == "rr":
			return (self.ratio_tree, retrograde_ratio_array)
		elif modification == "d":
			return (self.difference_tree, difference_array)
		elif modification == "rd":
			return (self.difference_tree, retrograde_difference_array)
		elif modification == "sr":
			return (self.ratio_tree, superdivisions_ratio[1:])  # exclude original
		elif modification == "rsr":
			return (self.ratio_tree, retrograde_superdivisions_ratio[1:])  # exclude original

	def _get_modification_data(self, found_fragment, modification):
		"""Helper function for retrieving the modifier between the input & founds fragments."""
		if modification == "r":
			ratio = abs(self.ql_array[0] / found_fragment.ql_array()[0])
			return (modification, ratio)
		elif modification == "rr":
			flipped = self.ql_array[::-1]
			ratio = abs(flipped[0] / found_fragment.ql_array()[0])
			return (modification, ratio)
		elif modification == "d":
			difference = abs(self.ql_array[0] - found_fragment.ql_array()[0])
			return (modification, difference)
		elif modification == "rd":
			flipped = self.ql_array[::-1]
			difference = abs(flipped[0] - found_fragment.ql_array()[0])
			return (modification, difference)
		elif modification == "sr":
			# How can I get the superdivision information easily...?
			ratio = abs(self.ql_array[0] / found_fragment.ql_array()[0])
			return (modification, ratio)
		elif modification == "rsr":
			# See the above.
			flipped = self.ql_array[::-1]
			ratio = abs(flipped[0] / found_fragment.ql_array()[0])
			return (modification, ratio)

def get_by_ql_array(
		ql_array,
		ratio_tree=None,
		difference_tree=None,
		allowed_modifications=[
			"r",
			"rr",
			"d",
			"rd",
			"sr",
			"rsr"
		],
		allow_unnamed=False
	):
	"""
	Searches a given ratio and/or difference tree for a given fragment. Allows grace notes.

	:param numpy.array ql_array: fragment to be searched.
	:param `~decitala.trees.FragmentTree` ratio_tree: tree storing ratio representations.
	:param `~decitala.trees.FragmentTree` difference_tree: tree storing difference representations.
	:param list allowed_modifications: possible ways for a fragment to be modified.
									Current possibilities are ``r``, ``rr``, ``d``, ``rd``, ``sr``, and ``rsr``.
									*NOTE*: the order of ``allowed_modifications`` is the order of the search.
	:param bool allow_unnamed: whether or not to allow the retrieval of unnamed paths. The
								default is ``False``.

	>>> from decitala.trees import FragmentTree
	>>> fragment = np.array([3.0, 1.5, 1.5, 3.0])
	>>> ratio_tree = FragmentTree.from_frag_type(frag_type='greek_foot', rep_type='ratio')
	>>> difference_tree = FragmentTree.from_frag_type(frag_type='greek_foot', rep_type='difference')
	>>> allowed_modifications = ["r", "rr"]
	>>> get_by_ql_array(fragment, ratio_tree, difference_tree, allowed_modifications)
	(<fragment.GreekFoot Choriamb>, ('r', 1.5))
	"""
	assert type(allowed_modifications) == list

	# Remove any grace notes.
	ql_array = [val for val in ql_array if val != 0]

	fragment = None
	config = _SearchConfig(
		ql_array=ql_array,
		ratio_tree=ratio_tree,
		difference_tree=difference_tree,
		modifications=allowed_modifications
	)
	i = 0
	while i < len(allowed_modifications):
		curr_modification = allowed_modifications[i]
		search_tree, search_ql_array = config[curr_modification]

		if curr_modification in {"sr", "rsr"}:
			for this_array in search_ql_array:
				if len(this_array) < 2:
					pass
				else:
					search = search_tree.search_for_path(this_array, allow_unnamed)

				if search is not None:
					break
		else:
			search = search_tree.search_for_path(search_ql_array, allow_unnamed)

		if search is not None:
			fragment = search
			change = config._get_modification_data(fragment, curr_modification)
			break
		else:
			i += 1

	if fragment:
		return (fragment, change)
	else:
		return None

####################################################################################################
def rolling_search(
		filepath,
		part_num,
		ratio_tree=None,
		difference_tree=None,
		allowed_modifications=[
			"r",
			"rr",
			"d",
			"rd",
			"sr",
			"rsr"
		],
		try_contiguous_summation=True,
		windows=list(range(2, 20)),
		allow_unnamed=False,
		logger=None
	):
	"""
	Rolling rhythmic search on a music21-readable file on a given part. For search types, see 
	documentation for :func:`~decitala.trees.get_by_ql_array`. The default window lengths 
	are the lengths of fragments in the decitala dataset.

	:param str filepath: path to file to be searched.
	:param int part_num: part in the file to be searched (0-indexed).
	:param `~decitala.trees.FragmentTree` ratio_tree: tree storing ratio representations.
	:param `~decitala.trees.FragmentTree` difference_tree: tree storing difference representations.
	:param list allowed_modifications: see :obj:`~decitala.trees.get_by_ql_array`.
	:param bool try_contiguous_summation: ties together all elements of equal pitch and duration 
										and searches. See :obj:`~decitala.utils.contiguous_summation`.
	:param list windows: possible lengths of the search frames. 
	:param bool allow_unnamed: whether or not to include unnamed fragments (in the fragment tree(s)) 
								in the return.
	:param bool logger: logger object (see :obj:`~decitala.utils.get_logger`).  

	:return: list holding dictionaries, each of which holds fragment, modifiation, onset-range, and 
			spanning data.
	:rtype: list

	>>> from decitala.trees import FragmentTree
	>>> ratio_tree = FragmentTree.from_frag_type(frag_type='greek_foot', rep_type='ratio')
	>>> difference_tree = FragmentTree.from_frag_type(frag_type='greek_foot', rep_type='difference') # noqa
	>>> ex = "./tests/static/Shuffled_Transcription_2.xml"
	>>> for tala_data in rolling_search(ex, 0, ratio_tree, difference_tree, allowed_modifications=["r"])[0:5]:
	... 	print(tala_data)
	{'fragment': <fragment.GreekFoot Trochee>, 'mod': ('r', 0.125), 'onset_range': (0.0, 0.375), 'is_spanned_by_slur': False, 'pitch_content': [(72,), (87,)], 'id': 1}
	{'fragment': <fragment.GreekFoot Dactyl>, 'mod': ('r', 0.125), 'onset_range': (0.0, 0.5), 'is_spanned_by_slur': False, 'pitch_content': [(72,), (87,), (79,)], 'id': 39}
	{'fragment': <fragment.GreekFoot Spondee>, 'mod': ('r', 0.0625), 'onset_range': (0.25, 0.5), 'is_spanned_by_slur': False, 'pitch_content': [(87,), (79,)], 'id': 2}
	{'fragment': <fragment.GreekFoot Trochee>, 'mod': ('r', 0.125), 'onset_range': (1.25, 1.625), 'is_spanned_by_slur': False, 'pitch_content': [(85,), (80,)], 'id': 3}
	{'fragment': <fragment.GreekFoot Dactyl>, 'mod': ('r', 0.125), 'onset_range': (1.25, 1.75), 'is_spanned_by_slur': False, 'pitch_content': [(85,), (80,), (80,)], 'id': 40}
	"""
	try:
		assert ratio_tree.rep_type == "ratio"
		assert difference_tree.rep_type == "difference"
	except AttributeError:
		pass

	depths = []
	if ratio_tree is not None:
		depths.append(ratio_tree.depth)
	if difference_tree is not None:
		depths.append(difference_tree.depth)

	object_list = get_object_indices(filepath=filepath, part_num=part_num)
	object_list = [x for x in object_list if x[1][1] - x[1][0] != 0]

	max_window_size = min(max(depths), len(object_list))
	closest_window = min(windows, key=lambda x: abs(x - max_window_size))
	index_of_closest = windows.index(closest_window)
	windows = windows[0:index_of_closest + 1]

	fragment_id = 0
	fragments_found = []
	for this_win in windows:
		# logger.info("Searching window of size {}.".format(this_win))

		frames = roll_window(array=object_list, window_length=this_win)
		for this_frame in frames:
			objects = [x[0] for x in this_frame]
			if any(x.isRest for x in objects):  # Skip any window that has a rest in it.
				continue
			else:
				ql_array = frame_to_ql_array(this_frame)
				if len(ql_array) < 2:
					continue

				searched = get_by_ql_array(
					ql_array,
					ratio_tree,
					difference_tree,
					allowed_modifications,
					allow_unnamed
				)
				if searched is not None:
					search_dict = dict()

					fragment_id += 1

					offset_1 = this_frame[0][0]
					offset_2 = this_frame[-1][0]
					is_spanned_by_slur = frame_is_spanned_by_slur(this_frame)
					pitch_content = frame_to_midi(this_frame)

					search_dict["fragment"] = searched[0]
					search_dict["mod"] = searched[1]
					search_dict["onset_range"] = (offset_1.offset, offset_2.offset + offset_2.quarterLength)
					search_dict["is_spanned_by_slur"] = is_spanned_by_slur
					search_dict["pitch_content"] = pitch_content
					search_dict["id"] = fragment_id

					fragments_found.append(search_dict)
					# logger.info("({0}, {1}), ({2}), {3}".format(search_dict["fragment"], search_dict["mod"], search_dict["onset_range"], search_dict["is_spanned_by_slur"])) # noqa

				if try_contiguous_summation:
					copied_frame = copy.copy(this_frame)
					new_frame = contiguous_summation(copied_frame)
					contiguous_summation_ql_array = frame_to_ql_array(new_frame)

					if len(contiguous_summation_ql_array) < 2 or np.array_equal(ql_array, contiguous_summation_ql_array): # noqa
						continue

					contiguous_summation_search = get_by_ql_array(
						contiguous_summation_ql_array,
						ratio_tree, difference_tree,
						allowed_modifications,
						allow_unnamed
					)
					if contiguous_summation_search is not None:
						rewritten_search = [contiguous_summation_search[0]] + [list(x) for x in contiguous_summation_search[1:]] # fragment + modification data # noqa
						rewritten_search[1][0] = rewritten_search[1][0] + "-cs"
						frag = rewritten_search[0]
						mod = rewritten_search[1]

						cs_search_dict = dict()

						fragment_id += 1

						offset_1 = new_frame[0][0].offset
						offset_2 = new_frame[-1][0].offset + new_frame[-1][0].quarterLength

						is_spanned_by_slur = frame_is_spanned_by_slur(this_frame)
						cs_pitch_content = frame_to_midi(this_frame)

						cs_search_dict["fragment"] = frag
						cs_search_dict["mod"] = mod
						cs_search_dict["onset_range"] = (offset_1, offset_2)
						cs_search_dict["is_spanned_by_slur"] = is_spanned_by_slur
						cs_search_dict["pitch_content"] = cs_pitch_content
						cs_search_dict["id"] = fragment_id

						fragments_found.append(cs_search_dict)
						# logger.info("({0}, {1}), ({2}), {3}".format(cs_search_dict["fragment"], cs_search_dict["mod"], cs_search_dict["onset_range"], cs_search_dict["is_spanned_by_slur"])) # noqa

	return sorted(fragments_found, key=lambda x: x["onset_range"][0])

# def rolling_search_on_array(
# 		ql_array,
# 		ratio_tree=None,
# 		difference_tree=None,
# 		allowed_modifications=[
# 			"r",
# 			"rr",
# 			"d",
# 			"rd",
# 			"sr",
# 			"rsr"
# 		],
# 		windows=[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19],
# 		allow_unnamed=False,
# 	):
# 	"""
# 	Rolling search on an array (useful for quick checks in a score). For search types,
# 	see documentation for :func:`~decitala.trees.get_by_ql_array`.

# 	:param numpy.array ql_array: fragment to be searched.
# 	:param `~decitala.trees.FragmentTree` ratio_tree: tree storing ratio representations.
# 	:param `~decitala.trees.FragmentTree` difference_tree: tree storing difference representations.
# 	:param list windows: possible length of the search frame.
# 	:return: list holding fragments in the array present in the trees.
# 	:rtype: list

# 	>>> greek_ratio_tree = FragmentTree(frag_type='greek_foot', rep_type='ratio')
# 	>>> greek_difference_tree = FragmentTree(frag_type='greek_foot', rep_type='difference')
# 	>>> example_fragment = np.array([0.25, 0.5, 0.25, 0.5])
# 	>>> for x in rolling_search_on_array(ql_array=example_fragment, ratio_tree=greek_ratio_tree, difference_tree=greek_difference_tree): # noqa
# 	...     print(x)
# 	(<fragment.GreekFoot Iamb>, ('r', 0.25))
# 	(<fragment.GreekFoot Trochee>, ('r', 0.25))
# 	(<fragment.GreekFoot Iamb>, ('r', 0.25))
# 	(<fragment.GreekFoot Amphibrach>, ('r', 0.25))
# 	(<fragment.GreekFoot Amphimacer>, ('r', 0.25))
# 	"""
# 	assert ratio_tree.rep_type == "ratio"
# 	assert difference_tree.rep_type == "difference"

# 	fragments_found = []
# 	max_window_size = min(windows, key = lambda x: abs(x - len(ql_array)))
# 	max_index = windows.index(max_window_size)
# 	windows = windows[0:max_index + 1]
# 	for this_window in windows:
# 		for this_frame in roll_window(array = ql_array, window_length = this_window):
# 			searched = get_by_ql_array(this_frame, ratio_tree, difference_tree, allowed_modifications, allow_unnamed) # noqa
# 			if searched is not None:
# 				fragments_found.append(searched)

# 	return fragments_found

####################################################################################################
# Hash table search method.
def _get_mod_info(data):
	if data["factor"] != 1.0 and data["difference"] == 0.0:
		mod_type = "r"
		mod_val = data["factor"]
	elif data["factor"] == 1.0 and data["difference"] != 0.0:
		mod_type = "d"
		mod_val = data["difference"]

	if data["retrograde"] is True:
		mod_type = "r" + mod_type

	return (mod_type, mod_val)

def _make_search_dict(data, frame):
	offset_1 = frame[0][0]
	offset_2 = frame[-1][0]

	pitch_content = frame_to_midi(frame)

	# I can't explain this inheritance issue. Stupid hotfix has been added to rolling_hash_search.
	# d = GeneralFragment([1.0, 1.0, 2.0])
	# d = Decitala("Gajalila")
	# if data["frag_type"] == "decitala":
	# 	fragment = Decitala(data["fragment"])
	# elif data["frag_type"] == "greek_foot":
	# 	print(GreekFoot(data["fragment"]))
	# else:
	# 	raise SearchException("{} is an invalid frag_type".format(frag_type))

	search_dict = {
		"fragment": data["fragment"],
		"frag_type": data["frag_type"],
		"mod": _get_mod_info(data),
		"onset_range": (offset_1.offset, offset_2.offset + offset_2.quarterLength),
		"pitch_content": pitch_content,
	}
	return search_dict

def rolling_hash_search(
		filepath,
		part_num,
		table,
		windows=list(range(2, 19)),
		allow_subdivision=False,
		allow_contiguous_summation=False,
		ignore_single_anga_class_fragments=False
	):
	"""
	A different (faster) paradigm than the tree approaches above. Searches a large dictionary of
	all possible modifications of the rhythmic datasets.

	:param str filepath: path to file to be searched.
	:param int part_num: part in the file to be searched (0-indexed).
	:param dict table: TBD
	:param bool ignore_single_anga_class_fragments: whether to ignore single-anga class fragments
												in the search.
	"""
	object_list = get_object_indices(filepath=filepath, part_num=part_num)
	object_list = [x for x in object_list if x[1][1] - x[1][0] != 0]
	fragment_id = 0 # noqa TODO
	fragments_found = []

	max_dataset_length = len(max(table, key=len))
	max_window_size = min(max_dataset_length, len(object_list))
	closest_window = min(windows, key=lambda x: abs(x - max_window_size))
	index_of_closest = windows.index(closest_window)
	windows = windows[0:index_of_closest + 1]

	for this_win in windows:
		frames = roll_window(array=object_list, window_length=this_win)
		for this_frame in frames:
			# If having trouble finding a fragment, uncomment the code below and check table[str(tuple(ql_array))]. # noqa
			# if this_win == ??? and this_frame[0][1][0] == ???: # starting onset
			# 	import pdb; pdb.set_trace()
			objects = [x[0] for x in this_frame]
			if any(x.isRest for x in objects):
				continue
			else:
				ql_array = frame_to_ql_array(this_frame)
				if len(ql_array) < 2:
					continue
				elif ignore_single_anga_class_fragments is True:
					if len(set(ql_array)) == 1:
						continue

				try:
					searched = table[str(tuple(ql_array))]
					if searched is not None:
						search_dict = _make_search_dict(
							data=searched,
							frame=this_frame,
						)
						is_spanned_by_slur = frame_is_spanned_by_slur(this_frame)
						search_dict["is_spanned_by_slur"] = is_spanned_by_slur
						search_dict["id"] = fragment_id
						fragment_id += 1
						fragments_found.append(search_dict)
				except KeyError:
					pass

				# TODO: Need to check appearance since this isn't done in preprocessing.
				# Otherwise get duplicates!
				if allow_subdivision is True:
					all_superdivisions = find_possible_superdivisions(ql_array)
					for i, this_superdivision in enumerate(all_superdivisions):
						if i == 0:
							continue
						this_superdivision_retrograde = this_superdivision[::-1]
						if len(this_superdivision) < 2:
							continue

						try:
							searches = [tuple(this_superdivision), tuple(this_superdivision_retrograde)]
							for i, this_search in enumerate(searches):
								searched = table[str(this_search)]
								if searched is not None:
									search_dict = _make_search_dict(data=searched, frame=this_frame)
									search_dict["id"] = fragment_id
									if i == 0:
										search_dict["sr"] = True
									else:
										search_dict["rsr"] = True
									fragment_id += 1
									fragments_found.append(search_dict)
						except KeyError:
							pass

	for this_search_dict in fragments_found:
		if this_search_dict["frag_type"] == "greek_foot":
			this_search_dict["fragment"] = GreekFoot(this_search_dict["fragment"])
		elif this_search_dict["frag_type"] == "decitala":
			this_search_dict["fragment"] = Decitala(this_search_dict["fragment"])

	return sorted(fragments_found, key=lambda x: x["onset_range"][0])

def path_finder(
		filepath,
		part_num,
		frag_type,
		windows=list(range(2, 19)),
		slur_constraint=False,
		ignore_single_anga_class_fragments=False,
		verbose=False
	):
	if frag_type == "decitala":
		ht = DecitalaHashTable()
	elif frag_type == "greek_foot":
		ht = GreekFootHashTable()
	else:
		raise Exception("{} is not a valid frag_type.".format(frag_type))

	fragments = rolling_hash_search(
		filepath=filepath,
		part_num=part_num,
		table=ht,
		ignore_single_anga_class_fragments=ignore_single_anga_class_fragments
	)
	if not fragments:
		return None

	distance_matrix, next_matrix = floyd_warshall.floyd_warshall(
		fragments,
		weights={
			"gap": 0.75,
			"onsets": 0.25
		},
		verbose=verbose
	)
	best_source, best_sink = floyd_warshall.best_source_and_sink(fragments)
	best_path = floyd_warshall.get_path(
		start=best_source,
		end=best_sink,
		next_matrix=next_matrix,
		data=fragments,
		slur_constraint=slur_constraint
	)
	return best_path