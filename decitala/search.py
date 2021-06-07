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
import json
import numpy as np

from dataclasses import dataclass

from .utils import (
	successive_ratio_array,
	successive_difference_array,
	find_possible_superdivisions,
	get_object_indices,
	roll_window,
	contiguous_summation,
	get_logger
)
from .fragment import (
	FragmentEncoder,
	GeneralFragment
)
from .hash_table import (
	FragmentHashTable
)
from .path_finding import (
	floyd_warshall,
	dijkstra,
	path_finding_utils
)

logger = get_logger(name=__file__, print_to_console=True)

####################################################################################################
class SearchException(Exception):
	pass

####################################################################################################
# Hash table lookup.
@dataclass
class Extraction:
	fragment: GeneralFragment
	frag_type: str
	onset_range: tuple

	retrograde: bool
	factor: float
	difference: float
	mod_hierarchy_val: int

	pitch_content: list
	is_spanned_by_slur: bool
	id_: int

	contiguous_summation: bool = False

	def __repr__(self):
		return f"<search.Extraction {self.id_}>"

	def show(self):
		pass

def frame_to_ql_array(frame):
	"""
	:param list frame: Frame of data from :obj:`~decitala.utils.get_object_indices`.
	:return: A numpy array holding the associated quarter length of a given window.
	:rtype: numpy.array

	>>> from music21 import note
	>>> my_frame = [
	...     (note.Note("B-", quarterLength=0.125), (4.125, 4.25)),
	...		(note.Note("A", quarterLength=0.25), (4.25, 4.5)),
	...		(note.Note("B", quarterLength=0.125), (4.5, 4.625)),
	...		(note.Note("B-", quarterLength=0.125), (4.625, 4.75)),
	...		(note.Note("A", quarterLength=0.25), (4.75, 5.0)),
	...		(note.Note("G", quarterLength=0.25), (5.0, 5.25)),
	...		(note.Note("G", quarterLength=0.25), (5.25, 5.5)),
	...	]
	>>> frame_to_ql_array(my_frame)
	array([0.125, 0.25 , 0.125, 0.125, 0.25 , 0.25 , 0.25 ])
	"""
	qls = []
	for this_obj, this_range in frame:
		qls.append(this_obj.quarterLength)

	return np.array([x for x in qls if x != 0])

def frame_to_midi(frame, ignore_graces=True):
	"""
	:param list frame: Frame of data from :obj:`~decitala.utils.get_object_indices`.
	:return: A numpy array holding the pitches within the frame.
	:rtype: numpy.array

	>>> from music21 import note
	>>> my_frame = [
	...     (note.Note("B-", quarterLength=0.125), (4.125, 4.25)),
	...		(note.Note("A", quarterLength=0.25), (4.25, 4.5)),
	...		(note.Note("B", quarterLength=0.125), (4.5, 4.625)),
	...		(note.Note("B-", quarterLength=0.125), (4.625, 4.75)),
	...		(note.Note("A", quarterLength=0.25), (4.75, 5.0)),
	...		(note.Note("G", quarterLength=0.25), (5.0, 5.25)),
	...		(note.Note("G", quarterLength=0.25), (5.25, 5.5)),
	...	]
	>>> frame_to_midi(my_frame)
	[(70,), (69,), (71,), (70,), (69,), (67,), (67,)]
	"""
	midi_out = []
	for this_obj, this_range in frame:
		if not(ignore_graces):
			fpitches = this_obj.pitches
			midi_out.append(tuple([x.midi for x in fpitches]))
		else:
			if this_obj.quarterLength == 0.0:
				pass
			else:
				fpitches = this_obj.pitches
				midi_out.append(tuple([x.midi for x in fpitches]))

	return midi_out

def frame_is_spanned_by_slur(frame):
	"""
	:param list frame: Frame from :obj:`~decitala.utils.get_object_indices`.
	:return: Whether or not the frame is spanned by a music21.spanner.Slur object.
	:rtype: bool
	"""
	is_spanned_by_slur = False
	first_obj = frame[0][0]
	last_obj = frame[-1][0]
	spanners = first_obj.getSpannerSites()
	if spanners:
		for this_spanner in spanners:
			if type(this_spanner).__name__ == "Slur":
				if this_spanner.isFirst(first_obj) and this_spanner.isLast(last_obj):
					is_spanned_by_slur = True

	return is_spanned_by_slur

def frame_lookup(frame, ql_array, curr_fragment_id, table, windows):
	objects = [x[0] for x in frame]
	if any(x.isRest for x in objects):
		return None

	try:
		searched = table.data[tuple(ql_array)]
		if searched is not None:
			offset_1 = frame[0][0]
			offset_2 = frame[-1][0]
			return Extraction(
				fragment=searched["fragment"],
				frag_type=searched["fragment"].frag_type,
				onset_range=(offset_1.offset, offset_2.offset + offset_2.quarterLength),
				retrograde=searched["retrograde"],
				factor=searched["factor"],
				difference=searched["difference"],
				mod_hierarchy_val=searched["mod_hierarchy_val"],
				pitch_content=frame_to_midi(frame),
				is_spanned_by_slur=frame_is_spanned_by_slur(frame),
				id_=curr_fragment_id
			)
	except KeyError:
		return None

def rolling_hash_search(
		filepath,
		part_num,
		table,
		windows=list(range(2, 19)),
		allow_subdivision=False,
		allow_contiguous_summation=False
	):
	"""
	Function for searching a score for rhythmic fragments and modifications of rhythmic fragments.
	This function is faster and simpler than :meth:`decitala.search.rolling_tree_search`. 

	:param str filepath: Path to file to be searched.
	:param int part_num: Part in the file to be searched (0-indexed).
	:param `decitala.hash_table.FragmentHashTable` table: A :obj:`decitala.hash_table.FragmentHashTable` # noqa
	 													object or one of its subclasses.
	:param list windows: The allowed window sizes for search. Default is all integers in range 2-19.
	:param bool allow_subdivision: Whether to check for subdivisions of a frame in the search.
	"""
	object_list = get_object_indices(filepath=filepath, part_num=part_num, ignore_grace=True)

	if type(table) == FragmentHashTable:
		table.load()

	max_dataset_length = len(max(table.data, key=lambda x: len(x)))
	max_window_size = min(max_dataset_length, len(object_list))
	closest_window = min(windows, key=lambda x: abs(x - max_window_size))
	index_of_closest = windows.index(closest_window)
	windows = windows[0:index_of_closest + 1]

	fragment_id = 0
	fragments_found = []
	for this_win in windows:
		frames = roll_window(array=object_list, window_length=this_win)
		for this_frame in frames:
			frame_ql_array = frame_to_ql_array(this_frame)
			if len(frame_ql_array) < 2:
				continue

			lookup = frame_lookup(
				frame=this_frame,
				ql_array=frame_ql_array,
				curr_fragment_id=fragment_id,
				table=table,
				windows=windows
			)
			if lookup:
				fragments_found.append(lookup)
				fragment_id += 1

			if allow_subdivision:
				all_superdivisions = find_possible_superdivisions(
					ql_array=frame_ql_array,
					include_self=False
				)
				for this_superdivision in all_superdivisions:
					this_superdivision_retrograde = this_superdivision[::-1]
					if len(this_superdivision) < min(windows):
						continue

					searches = [tuple(this_superdivision), tuple(this_superdivision_retrograde)]
					subdivision_results = []
					for i, this_search in enumerate(searches):
						lookup = frame_lookup(
							frame=this_frame,
							ql_array=this_search,
							curr_fragment_id=fragment_id,
							table=table,
							windows=windows,
						)
						if lookup:
							if i == 0:
								lookup.mod_hierarchy_val = 5
							else:
								lookup.mod_hierarchy_val = 6

							subdivision_results.append(lookup)
							fragment_id += 1

					if subdivision_results:
						fragments_found.append(min(subdivision_results, key=lambda x: x.mod_hierarchy_val))

			if allow_contiguous_summation:
				if any(type(x[0]).__name__ == "Rest" for x in this_frame):
					continue

				cs_frame = tuple(contiguous_summation(this_frame))
				if cs_frame == this_frame:
					continue

				cs_ql_array = frame_to_ql_array(cs_frame)
				if len(cs_ql_array) < min(windows):
					continue
				else:
					cs_lookup = frame_lookup(
						frame=cs_frame,
						ql_array=cs_ql_array,
						curr_fragment_id=fragment_id,
						table=table,
						windows=windows
					)
					if cs_lookup:
						cs_lookup.contiguous_summation = True
						fragments_found.append(cs_lookup)
						fragment_id += 1

	return sorted(fragments_found, key=lambda x: x.onset_range[0])

def path_finder(
		filepath,
		part_num,
		table,
		windows=list(range(2, 19)),
		allow_subdivision=False,
		allow_contiguous_summation=False,
		algorithm="dijkstra",
		cost_function_class=path_finding_utils.CostFunction(),
		slur_constraint=False,
		save_filepath=None,
		verbose=False
	):
	"""
	This function combines a number of tools for effectively finding a path of fragments
	through a provided composition and part number. It first runs
	:obj:`decitala.search.rolling_hash_search` to extract all fragments from the provided
	table and then runs the Floyd-Warshall algorithm to get the best path.

	:param str filepath: Path to file to be searched.
	:param int part_num: Part in the file to be searched (0-indexed).
	:param `decitala.hash_table.FragmentHashTable` table: A :obj:`decitala.hash_table.FragmentHashTable` # noqa
	 													object or one of its subclasses.
	:param list windows: The allowed window sizes for search. Default is all integers in range 2-19.
	:param bool allow_subdivision: Whether to check for subdivisions of a frame in the search.
	:param str algorithm: Path-finding algorithm used. Options are ``"floyd_warshall"`` and ``"dijkstra"``.
						Default is ``"dijkstra"``.
	:param bool slur_constraint: Whether to force slurred fragments to appear in the final path.
								Only possible if `algorithm="floyd-warshall"`.
	:param str save_filepath: An optional path to a JSON file for saving search results. This file
							can then be loaded with the :meth:`decitala.utils.loader`.
	:param bool verbose: Whether to log messages (only used with `algorithm="floyd-warshall"`).
						Default is ``False``.
	"""
	fragments = rolling_hash_search(
		filepath=filepath,
		part_num=part_num,
		table=table,
		windows=windows,
		allow_subdivision=allow_subdivision,
		allow_contiguous_summation=allow_contiguous_summation
	)
	if not fragments:
		return None

	if algorithm.lower() == "dijkstra":
		if slur_constraint:
			raise SearchException("This is not yet supported. Coming soon.")
		source, target, best_pred = dijkstra.dijkstra_best_source_and_sink(data=fragments) # noqa
		best_path = dijkstra.generate_path(
			best_pred,
			source,
			target
		)
		best_path = sorted([x for x in fragments if x.id_ in best_path], key=lambda x: x.onset_range[0]) # noqa
	elif algorithm.lower() == "floyd-warshall":
		best_source, best_sink = path_finding_utils.best_source_and_sink(fragments)
		distance_matrix, next_matrix = floyd_warshall.floyd_warshall(
			fragments,
			verbose=verbose
		)
		best_path = floyd_warshall.get_path(
			start=best_source,
			end=best_sink,
			next_matrix=next_matrix,
			data=fragments,
			slur_constraint=slur_constraint
		)
	else:
		raise SearchException("The only available options are 'dijkstra' and 'floyd-warshall'.")

	if save_filepath:
		with open(save_filepath, "w") as output:
			json.dump(obj=best_path, fp=output, cls=FragmentEncoder, indent=4)
		logger.info(f"Result saved in: {save_filepath}")

	return best_path

def rolling_search_on_array(
		ql_array,
		table,
		windows=list(range(2, 19)),
	):
	"""
	A very light function for rhythmic search on an array. This is primarily useful
	for quick checks in a score. It does not support all possible modification types, etc... 

	:param numpy.array ql_array: A quarter length array.
	:param `decitala.hash_table.FragmentHashTable` table: A :obj:`decitala.hash_table.FragmentHashTable` # noqa
	 													object or one of its subclasses.
	:param list windows: The allowed window sizes for search. Default is all integers in range 2-19.
	:return: A list holding fragments in the array that were detected in the table.
	:rtype: list
 
	>>> ght = FragmentHashTable(
	... 	datasets=["greek_foot"]
	... )
	>>> ght.load()
	>>> example_fragment = np.array([0.25, 0.5, 0.25, 0.5])
	>>> for x in rolling_search_on_array(ql_array=example_fragment, table=ght):
	... 	print(x["fragment"])
	<fragment.GreekFoot Iamb>
	<fragment.GreekFoot Trochee>
	<fragment.GreekFoot Iamb>
	<fragment.GreekFoot Amphibrach>
	<fragment.GreekFoot Amphimacer>
	"""
	max_dataset_length = len(max(table.data, key=lambda x: len(x)))
	max_window_size = min(max_dataset_length, len(ql_array))
	closest_window = min(windows, key=lambda x: abs(x - max_window_size))
	index_of_closest = windows.index(closest_window)
	windows = windows[0:index_of_closest + 1]

	fragments_found = []
	for this_window in windows:
		for this_frame in roll_window(array=ql_array, window_length=this_window):
			try:
				searched = table.data[tuple(this_frame)]
				if searched:
					fragments_found.append(searched)
			except KeyError:
				continue

	return fragments_found

####################################################################################################
# Tree search method.
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
def rolling_tree_search(
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
		try_contiguous_summation=False,
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
	>>> for tala_data in rolling_tree_search(ex, 0, ratio_tree, difference_tree, allowed_modifications=["r"])[0:5]:
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