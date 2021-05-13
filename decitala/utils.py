####################################################################################################
# File:     utils.py
# Purpose:  Random useful functions.
#
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020 / Frankfurt, DE 2020 / NYC, 2021
####################################################################################################
import copy
import json
import logging
import numpy as np
import sys

from itertools import groupby
from more_itertools import consecutive_groups, windowed, powerset
from scipy.linalg import norm

from music21 import converter
from music21 import note
from music21 import pitch
from music21 import scale
from music21 import stream
from music21.meter import TimeSignature

from . import fragment

"""
NOTE: Normally a crescent moon superscript is used. Since it serves the same function as viramas, we
use the same notation.
"""
carnatic_symbols = {
	"o": {"value": 0.25, "name": "Druta"},
	"oc": {"value": 0.375, "name": "Druta-Virama"},
	"|": {"value": 0.5, "name": "Laghu"},
	"|c": {"value": 0.75, "name": "Laghu-Virama"},
	"S": {"value": 1.0, "name": "Guru"},
	"Sc": {"value": 1.5, "name": "Pluta"}
	# ['kakapadam', '8X', 2.0]
}

greek_diacritics = [
	['breve', '⏑', 1.0],
	['macron', '––', 2.0]
]

multiplicative_augmentations = [
	['Tiers', 4 / 3],
	['Un quart', 1.25],
	['Du Point', 1.5],
	['Classique', 2],
	['Double', 3],
	['Triple', 4],
]

PRIMES = [
	2, 3, 5, 7, 11,
	13, 17, 19, 23,
	29, 31, 37, 41,
	43, 47, 53, 59,
	61, 67, 71, 73,
	79, 83, 89, 97
]

NEUMES = {
	(1, 0): "Clivis",
	(0, 1): "Podatus",
	(0, 1, 2): "Scandicus",
	(2, 1, 0): "Climacus",
	(0, 1, 0): "Torculus",
	(1, 0, 1): "Porrectus"
}

VALID_DENOMINATORS = [1, 2, 4, 8, 16, 32, 64, 128]

class UtilsException(Exception):
	pass

####################################################################################################
# LOGGING
####################################################################################################
def get_logger(name, print_to_console=True, write_to_file=None):
	logger = logging.getLogger(name)
	if not len(logger.handlers):
		logger.setLevel(logging.INFO)

		if write_to_file is not None:
			file_handler = logging.FileHandler(write_to_file)
			logger.addHandler(file_handler)
		if print_to_console:
			stdout_handler = logging.StreamHandler(sys.stdout)
			logger.addHandler(stdout_handler)

	return logger

####################################################################################################
# NOTATION CONVERSION
####################################################################################################
def carnatic_string_to_ql_array(string_):
	"""
	:param str string_: string of carnatic durations separated by spaces.
	:return: input string converted to a quarter length array.
	:rtype: numpy.array.

	>>> carnatic_string_to_ql_array('oc o | | Sc S o o o')
	array([0.375, 0.25 , 0.5  , 0.5  , 1.5  , 1.   , 0.25 , 0.25 , 0.25 ])
	"""
	split_string = string_.split()
	vals = []
	for token in split_string:
		try:
			if carnatic_symbols[token] is not None:
				vals.append(carnatic_symbols[token]["value"])
		except KeyError:
			pass
	return np.array(vals)

def ql_array_to_carnatic_string(ql_array):
	"""
	:param iterable ql_array: quarter length array.
	:return: quarter length array converted to carnatic notation.
	:rtype: str

	>>> ql_array_to_carnatic_string([0.5, 0.25, 0.25, 0.375, 1.0, 1.5, 1.0, 0.5, 1.0])
	'| o o oc S Sc S | S'
	"""
	tokens = []
	for ql in ql_array:
		for key, val in carnatic_symbols.items():
			if carnatic_symbols[key]["value"] == ql:
				tokens.append(key)
	return " ".join(tokens)

def ql_array_to_greek_diacritics(ql_array):
	"""
	Returns the input ``ql_array`` in greek prosodic notation. This notation only allows
	for two types of rhythmic values (long & short).

	:param iterable ql_array: quarter length array.
	:return: quarter length array converted to greek prosodic notation.
	:rtype: str

	>>> ql_array_to_greek_diacritics(ql_array=[1.0, 0.5, 0.5, 1.0, 1.0, 0.5])
	'–– ⏑ ⏑ –– –– ⏑'
	"""
	ql_array = np.array(ql_array)
	assert len(np.unique(ql_array)) == 2

	long_val = max(ql_array)
	short_val = min(ql_array)
	long_factor = 2.0 / long_val
	short_factor = 1.0 / short_val

	ql_array = np.array([(x * long_factor) if x == long_val else (x * short_factor) for x in ql_array])
	greek_string_lst = []
	for this_val in ql_array:
		for this_diacritic_name, this_diacritic_symbol, this_diacritic_val in greek_diacritics:
			if this_val == this_diacritic_val:
				greek_string_lst.append(this_diacritic_symbol)

	return " ".join(greek_string_lst)

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

####################################################################################################
# RHYTHM
####################################################################################################
def augment(ql_array, factor=1.0, difference=0.0):
	"""
	Returns an augmentation in the style of Messiaen. If difference is set to 0.0, then the
	augmentation is multiplicative. If factor is set to 1.0, then augmentation is additive. If
	factor & difference are non-zero, we have a mixed augmentation.

	:param ql_array: array defining the rhythmic fragment (iterable).
	:param float factor: factor for multiplicative augmentation.
	:param float difference: factor for additive augmentation.

	:return: an augmented fragment.
	:rtype: numpy.array

	>>> augment(ql_array=[1.0, 1.0, 0.5, 0.25], factor=2.0, difference=0.25)
	array([2.25, 2.25, 1.25, 0.75])
	"""
	assert factor > 0.0
	return np.array([(this_val * factor) + difference for this_val in ql_array])

def stretch_augment(ql_array, factor, stretch_factor):
	"""
	A special kind of rhythmic augmentation catered toward the Greek metrics. The "short" is
	kept as is and the "long" is modified by the given difference. The new long must still be
	longer than the short value.

	:param ql_array: array defining the rhythmic fragment (iterable)

	>>> stretch_augment(ql_array=[1.0, 2.0], factor=0.125, stretch_factor=0.25)
	array([0.125, 0.5  ])
	"""
	assert len(np.unique(ql_array)) <= 2

	stretch_augmentation = []
	breve = min(ql_array)
	for this_val in ql_array:
		if this_val == breve:
			stretch_augmentation.append(factor * breve)
		else:
			stretch_augmentation.append(this_val * stretch_factor)

	return np.array(stretch_augmentation)

def successive_ratio_array(ql_array):
	"""
	Returns array defined by the ratio of successive elements. By convention,
	we set the first value to 1.0.

	:param ql_array: array defining a rhythmic fragment.
	:return: array consisting of successive ratios of the input elements.
	:rtype: numpy.array

	>>> successive_ratio_array([1.0, 1.0, 2.0, 0.5, 0.5, 0.25, 1.0])
	array([1.  , 1.  , 2.  , 0.25, 1.  , 0.5 , 4.  ])
	"""
	def _ratio(array, start_index):
		"""Returns the ratio of an element in an array at index i to the value at index i + 1."""
		if not (0 <= start_index and start_index <= len(array) - 1):
			raise IndexError('Input ``start_index`` not in appropriate range!')
		try:
			ratio = array[start_index + 1] / array[start_index]
			return round(ratio, 5)
		except ZeroDivisionError:
			raise Exception("There is a 0 at some point in the input array.")

	ratio_lst = [1.0]
	i = 0
	while i < len(ql_array) - 1:
		ratio_lst.append(_ratio(ql_array, i))
		i += 1

	return np.array(ratio_lst)

def successive_difference_array(ql_array):
	"""
	Returns the first order difference of ``ql_array`` (contiguous differences).

	:param ql_array: array defining a rhythmic fragment (iterable).
	:return: array consisting of successive differences of the input elements.
	:rtype: numpy.array

	>>> successive_difference_array([0.25, 0.25, 0.75, 0.75, 0.5, 1.0, 1.5])
	array([ 0.  ,  0.  ,  0.5 ,  0.  , -0.25,  0.5 ,  0.5 ])
	"""
	def _difference(array, start_index):
		"""Returns the difference between two elements."""
		try:
			difference = array[start_index + 1] - array[start_index]
			return difference
		except IndexError:
			pass

	difference_lst = [0.0]
	i = 0
	while i < len(ql_array) - 1:
		difference_lst.append(_difference(ql_array, i))
		i += 1

	return np.array(difference_lst)

def _remove_adjacent_equal_elements(array):
	as_lst = list(array)
	filtered = [a for a, b in zip(as_lst, as_lst[1:] + [not as_lst[-1]]) if a != b]
	return np.array(filtered)

def dseg(ql_array, reduced=False, as_str=False):
	dseg_vals = copy.copy(ql_array)
	value_dict = dict()

	for i, this_val in zip(range(0, len(sorted(set(dseg_vals)))), sorted(set(dseg_vals))):
		value_dict[this_val] = str(i)

	for i, this_val in enumerate(dseg_vals):
		for key in value_dict:
			if this_val == key:
				dseg_vals[i] = value_dict[key]
	
	dseg = np.array([int(val) for val in dseg_vals])
	if reduced:
		dseg = _remove_adjacent_equal_elements(array=dseg)

	if not(as_str):
		return dseg
	else:
		return "<" + " ".join([str(val) for val in dseg]) + ">"

# La Valeur Ajoutee
def get_added_values(ql_array, print_type=True):
	"""
	Given a quarter length list, returns all indices and types of added values found, according to
	the examples dicussed in Technique de Mon Langage Musical (1944).

	:param ql_array: Array defining a rhythmic fragment (iterable).
	:param bool print_type: Whether to print the Valéur Ajoutée types, along with the locations.
	:return: Location of extracted added values (along with their type if ``print_type=True``)
	:rtype: list

	>>> get_added_values([0.25, 0.5, 0.5, 0.75, 0.25])
	[(0, 'du Note'), (4, 'du Note')]
	>>> get_added_values([0.5, 0.25, 0.5, 0.25, 1.0])
	[(1, 'du Note'), (3, 'du Note')]
	>>> get_added_values([0.75, 0.75, 0.75, 0.25, 0.5])
	[(3, 'du Note')]
	>>> get_added_values([0.75, 0.75, 0.75, 0.75, 0.25, 0.25])

	>>> get_added_values([0.5, 0.25, 0.5, 0.75, 1.25, 1.5])
	[(1, 'du Note'), (3, 'du Point'), (4, 'du Tie')]

	>>> l = [1.0, 0.5, 0.25, 1.0, 0.5, 0.75, 0.5]
	>>> get_added_values(l)
	[(2, 'du Note'), (5, 'du Point')]

	?????
	>>> get_added_values([0.5, 0.5, 0.75, 1.25, 0.75])
	[(2, 'du Point'), (3, 'du Tie')]

	>>> get_added_values([1.0, 0.25, 0.5], print_type = False)
	[1]

	>>> get_added_values([0.25, 0.25, 0.75, 2.0])
	[(2, 'du Point')]
	>>> get_added_values([0.5, 0.25, 0.75, 0.25, 0.5])
	[(1, 'du Note'), (2, 'du Point'), (3, 'du Note')]
	"""
	if len(ql_array) < 3:
		raise Exception('List must be of length 3 or greater.')

	addedVals = []
	if ql_array[0] == 0.25 and ql_array[1] != 0.25:
		addedVals.append((0, 'du Note'))
	if ql_array[-1] == 0.25 and ql_array[-2] != 0.25:
		addedVals.append((len(ql_array) - 1, 'du Note'))
	if ql_array[-1] == 0.75 and ql_array[-2] % 0.5 == 0:
		addedVals.append((len(ql_array) - 1, 'du Point'))

	for currIndex in range(1, len(ql_array) - 1):
		prevVal = ql_array[currIndex - 1]
		currVal = ql_array[currIndex]
		nextVal = ql_array[currIndex + 1]

		x = currVal - 0.25
		if x >= 1.0 and x.is_integer():
			addedVals.append((currIndex, 'du Tie'))

		if currVal == 0.25:
			if prevVal != currVal != nextVal:
				if prevVal % 0.5 == 0 and nextVal % 0.5 == 0:
					addedVals.append((currIndex, 'du Note'))
				elif prevVal % 0.75 == 0:
					addedVals.append((currIndex, 'du Note'))
				elif nextVal % 0.75 == 0:
					addedVals.append((currIndex, 'du Note'))
		elif currVal == 0.75:
			if prevVal % 0.5 == 0 and nextVal % 0.5 == 0:
				addedVals.append((currIndex, 'du Point'))
			elif prevVal < currVal and nextVal > currVal:
				addedVals.append((currIndex, 'du Point'))
			elif prevVal == 0.25:
				addedVals.append((currIndex, 'du Point'))

	if len(addedVals) == 0:
		return None

	if print_type is False:
		return [a[0] for a in addedVals]
	else:
		return addedVals

def removeAddedValuesFromList(lst):
	added_val_indices = get_added_values(ql_lst=lst, print_type=False)
	for i in added_val_indices:
		del lst[i]
	return

def non_retrogradable_measures(filepath, part_num):
	"""
	Function for retrieving all non-retrogradable measures in a given filepath and part number.
	"""
	converted = converter.parse(filepath)
	p = converted.parts[part_num]
	non_retrogradable_measures = []
	for this_measure in p.getElementsByClass(stream.Measure):
		ql_array = []
		for this_note in this_measure.flat.stripTies().getElementsByClass(note.Note):
			ql_array.append(this_note.quarterLength)

		if ql_array == ql_array[::-1]:
			non_retrogradable_measures.append(this_measure.number)

	return non_retrogradable_measures

####################################################################################################
# SUBDIVISION
####################################################################################################
def find_clusters(input_, data_mode=False):
	"""
	Finds the regions with consecutive equal elements.

	:param iterable input_: either a list/array (representing
							:obj:`~decitala.fragment.GeneralFragment.ql_array`) or data from
							:obj:`~decitala.utils.get_object_indices`.
	:param bool data_mode: whether or not the input data is a quarter length array or data from
							:obj:`~decitala.utils.get_object_indices`.
	:return: a list of cluster indices; if not in data mode, regions with equal quarter length values;
			if ``data_mode=True``, then regions where the quarter lengths and pitch content are equal.

	>>> varied_ragavardhana = np.array([1, 1, 1, 0.5, 0.75, 0.75, 0.5, 0.25, 0.25, 0.25])
	>>> clusters = find_clusters(varied_ragavardhana)
	>>> clusters
	[[0, 2], [4, 5], [7, 9]]
	>>> varied_ragavardhana[clusters[0][0]:clusters[0][1]+1]
	array([1., 1., 1.])
	>>> varied_ragavardhana[clusters[1][0]:clusters[1][1]+1]
	array([0.75, 0.75])
	>>> varied_ragavardhana[clusters[2][0]:clusters[2][1]+1]
	array([0.25, 0.25, 0.25])
	>>> # We can also find clusters of pitch and rhythmic information for data from get_object_indices.
	>>> from music21 import note, chord
	>>> example_data = [
	...		(note.Note("F#"), (6.5, 6.75)),
	...     (note.Note("G"), (6.75, 7.0)),
	...     (note.Note("G"), (7.0, 7.25)),
	...     (note.Note("C#"), (7.25, 7.5)),
	...     (note.Note("G"), (7.5, 7.75)),
	...     (note.Note("G"), (7.75, 8.0)),
	...     (note.Note("A-"), (8.0, 8.125)),
	... ]
	>>> find_clusters(example_data, data_mode=True)
	[[1, 2], [4, 5]]
	>>> example_data2 = [
	... 	(chord.Chord(["F#2", "F3"], quarterLength=0.125), (0.0, 0.125)),
	... 	(chord.Chord(["F#2", "F3"], quarterLength=0.125), (0.125, 0.25)),
	... 	(chord.Chord(["F#2", "F3"], quarterLength=0.125), (0.25, 0.375)),
	... 	(chord.Chord(["E-3", "D4"], quarterLength=0.125), (0.375, 0.5)),
	... 	(chord.Chord(["A2", "A-3"], quarterLength=0.25), (0.5, 0.75)),
	... ]
	>>> find_clusters(example_data2, data_mode=True)
	[[0, 2]]
	"""
	if not(data_mode):
		ranges = [list(this_range) for _, this_range in groupby(range(len(input_)), lambda i: input_[i])]
	else:
		regions_property = lambda i: (input_[i][1][1] - input_[i][1][0] and [x.midi for x in input_[i][0].pitches])  # noqa: E501
		ranges = [list(this_range) for _, this_range in groupby(range(len(input_)), regions_property)]

	cluster_index_ranges = [[this_range[0], this_range[-1]] for this_range in ranges if len(this_range) > 1]  # noqa: E501

	return cluster_index_ranges

def _compliment_of_index_ranges(array, clusters):
	"""
	TODO: if the compliment range has only one val, it should just be one val, not two
	(otherwise can't distinguish).

	>>> varied_ragavardhana = np.array([1, 1, 1, 0.5, 0.75, 0.5])
	>>> _compliment_of_index_ranges(varied_ragavardhana, [find_clusters(varied_ragavardhana)[0]])
	[[3, 5]]
	>>> varied_ragavardhana_2 = np.array([1, 1, 1, 0.5, 0.75, 0.75, 0.5, 0.25, 0.25, 0.25])
	>>> _compliment_of_index_ranges(varied_ragavardhana_2, find_clusters(varied_ragavardhana_2))
	[[3], [6]]
	"""
	flattened_cluster_ranges = []
	for this_range in clusters:
		index_range = list(range(this_range[0], this_range[1] + 1))
		flattened_cluster_ranges.extend(index_range)

	total_range = list(range(0, len(array)))
	diff = sorted(list(set(total_range) - set(flattened_cluster_ranges)))

	compliments = []
	for elem in consecutive_groups(diff):
		elem_list = list(elem)
		if len(elem_list) == 1:
			compliments.append(elem_list)
		else:
			compliments.append([elem_list[0], elem_list[-1]])

	return compliments

def _make_one_superdivision(array, clusters):
	"""
	>>> varied_ragavardhana_2 = np.array([1, 1, 1, 0.5, 0.75, 0.75, 0.5, 0.25, 0.25, 0.25])
	>>> c = find_clusters(varied_ragavardhana_2)
	>>> # one combination of the clusters is [[0, 2], [7, 9]]
	>>> _make_one_superdivision(varied_ragavardhana_2, [[0, 2], [7, 9]])
	array([3.  , 0.5 , 0.75, 0.75, 0.5 , 0.75])
	"""
	superdivision = [0] * len(array)
	compliment_ranges = _compliment_of_index_ranges(array, clusters)
	for x in compliment_ranges:
		if len(x) == 1:
			superdivision[x[0]] = array[x[0]]
		else:
			superdivision[x[0]:x[1] + 1] = array[x[0]:x[1] + 1]

	for this_cluster in clusters:
		region = array[this_cluster[0]:this_cluster[1] + 1]
		summed = sum(region)
		superdivision[this_cluster[0]] = summed

	return np.array([x for x in superdivision if x != 0])

def find_possible_superdivisions(array, include_self=True):
	"""
	There is a more general approach to the subdivision problem, but we note that Messiaen's
	subdivision of tala components tends to be even.

	>>> long_fragment = np.array([1, 1, 1, 0.5, 0.75, 0.75, 0.5, 0.25, 0.25, 0.25])
	>>> for x in find_possible_superdivisions(long_fragment):
	...     print(x)
	[1.   1.   1.   0.5  0.75 0.75 0.5  0.25 0.25 0.25]
	[3.   0.5  0.75 0.75 0.5  0.25 0.25 0.25]
	[1.   1.   1.   0.5  1.5  0.5  0.25 0.25 0.25]
	[1.   1.   1.   0.5  0.75 0.75 0.5  0.75]
	[3.   0.5  1.5  0.5  0.25 0.25 0.25]
	[3.   0.5  0.75 0.75 0.5  0.75]
	[1.   1.   1.   0.5  1.5  0.5  0.75]
	[3.   0.5  1.5  0.5  0.75]

	>>> varied_ragavardhana = np.array([1, 1, 1, 0.5, 0.75, 0.5])
	>>> for x in find_possible_superdivisions(varied_ragavardhana, include_self=False):
	...     print(x)
	[3.   0.5  0.75 0.5 ]
	"""
	if include_self:
		possible_super_divisions = [np.array(array)]
	else:
		possible_super_divisions = []
	clusters = find_clusters(array)
	possible_combinations = power_list(clusters)
	for this_combination in possible_combinations:
		superdivision = _make_one_superdivision(array, this_combination)
		possible_super_divisions.append(superdivision)

	return possible_super_divisions

def net_ql_array(filepath, part_num, include_rests=False, ignore_grace_notes=True):
	"""
	Function for retrieving all quarter lengths from a part number in a filepath.
	"""
	converted = converter.parse(filepath)
	stripped = converted.parts[part_num].flat.stripTies()
	qls = []
	if not(include_rests):
		for obj in stripped.iter.notes:
			qls.append(obj.quarterLength)
	else:
		for obj in stripped.iter.notesAndRests:
			qls.append(obj.quarterLength)

	if ignore_grace_notes is True:
		qls = [x for x in qls if x != 0]

	return np.array(qls)

def transform_to_time_scale(ql_array):
	"""
	Transforms a quarter length array to time-scale (binary) notation.

	>>> udikshana = fragment.Decitala("Udikshana")
	>>> udikshana.ql_array()
	array([0.5, 0.5, 1. ])
	>>> transform_to_time_scale(ql_array=udikshana.ql_array())
	array([1, 1, 1, 0])
	"""
	total_durations = []
	shortest_value = min(ql_array)
	if all(map(lambda x: x % shortest_value == 0, ql_array)):
		total_durations = np.array([(x / shortest_value) for x in ql_array])
	else:
		i = 2
		# This upper bound is arbitrary; something between 4 and 10 should suffice.
		while i < 6:
			if all(map(lambda x: (x % (shortest_value / i)).is_integer(), ql_array)):
				total_durations = np.array([(x / (shortest_value / i)) for x in ql_array])
				break
			else:
				i += 1

	if len(total_durations) == 0:
		raise Exception("Something is wrong with the input quarter lengths!")

	result_out = []
	for this_elem in total_durations:
		if this_elem == 1.0:
			result_out.extend([1])
		else:
			result_out.extend([1])
			result_out.extend([0] * (int(this_elem) - 1))

	return np.array(result_out)

####################################################################################################
# WINDOWING / PARTITIONING
####################################################################################################
def roll_window(array, window_length, fn=None):
	"""
	Takes in a list and returns a numpy vstack holding rolling windows of length ``window_length``.

	:param numpy.array array: an iterable
	:param int window_length: size of the window
	:param lambda fn: function evaluating a bool.
	:return: rolling windows of array, each of length `window_length`.
	:rtype: numpy.vstack

	>>> composers = np.array(['Mozart', 'Monteverdi', 'Messiaen', 'Mahler', 'MacDowell', 'Massenet'])
	>>> for window in roll_window(array=composers, window_length=3):
	...     print(window)
	('Mozart', 'Monteverdi', 'Messiaen')
	('Monteverdi', 'Messiaen', 'Mahler')
	('Messiaen', 'Mahler', 'MacDowell')
	('Mahler', 'MacDowell', 'Massenet')
	>>> # This function also allows the use of a function input for filtering.
	>>> # Say we wanted to iterate over the elements of the following collection that have
	>>> # 1s in the set.
	>>> cseg_data = [[0, {1, -1}], [4, {1}], [2, {-1}], [5, {1}], [5, {1}], [1, {1, -1}]]
	>>> fn = lambda x: 1 in x[1]
	>>> for this_frame in roll_window(cseg_data, 3, fn):
	... 	print(this_frame)
	([0, {1, -1}], [4, {1}], [5, {1}])
	([4, {1}], [5, {1}], [5, {1}])
	([5, {1}], [5, {1}], [1, {1, -1}])
	"""
	if fn is not None:
		array = [x for x in array if fn(x) is True]

	assert type(window_length) == int
	# if len(array) >= window_length:
	# 	return [array]
	windows = list(windowed(seq=array, n=window_length, step=1))
	return windows

def power_list(data):
	"""
	:param data: an iterable
	:return: power set of the data as a list (excluding the empty list).
	:rtype: list

	>>> l = [1, 2, 3]
	>>> power_list(l)
	[(1,), (2,), (3,), (1, 2), (1, 3), (2, 3), (1, 2, 3)]

	>>> for x in power_list([(0.0, 2.0), (4.0, 5.5), (6.0, 7.25)]):
	...     print(x)
	((0.0, 2.0),)
	((4.0, 5.5),)
	((6.0, 7.25),)
	((0.0, 2.0), (4.0, 5.5))
	((0.0, 2.0), (6.0, 7.25))
	((4.0, 5.5), (6.0, 7.25))
	((0.0, 2.0), (4.0, 5.5), (6.0, 7.25))
	"""
	assert type(data) == list
	power_list = powerset(data)
	return [x for x in power_list if len(x) != 0]

####################################################################################################
# SCORE HELPERS
####################################################################################################
def get_object_indices(
		filepath,
		part_num,
		measure_divider_mode=None,
		ignore_grace=False
	):
	"""
	Returns data of the form [(object, (start, end)), ...] for a given file path and part number.
	(Supports rests and grace notes.)

	:param str filepath: Path to file to be analyzed.
	:param int part_num: Part number to be analyzed.
	:param str measure_divider_mode: Tool used for dividing the data into measures. If
									``measure_divider_mode="str"``, the data is returned with
									``"B"`` used as the measure marker. If instead
									``measure_divider_mode="list"``, the data is returned
									partitioned by measure. The default is ``None``, so no
									measure divisions are present.
	:param bool ignore_grace: Whether to ignore grace notes in the output. ``False`` by default.
	"""
	score = converter.parse(filepath)
	part = score.parts[part_num]
	stripped = part.stripTies(retainContainers=True)
	if not measure_divider_mode:
		data_out = []
		for this_obj in stripped.recurse().stream().iter.notesAndRests:
			start = this_obj.offset
			stop = this_obj.offset + this_obj.quarterLength
			data_out.append((this_obj, (start, stop)))
		if ignore_grace:
			data_out = [x for x in data_out if x[1][0] != x[1][1]]

		return data_out
	else:
		ms = stripped.getElementsByClass(stream.Measure)
		if measure_divider_mode == "list":
			data_out = []
			for this_measure in ms:
				measure_objects = []
				for this_obj in this_measure.recurse().stream().iter.notesAndRests:
					start = this_obj.offset
					stop = this_obj.offset + this_obj.quarterLength
					if ignore_grace:
						if start == stop:
							continue
					measure_objects.append((this_obj, (start, stop)))
				data_out.append(measure_objects)
		if measure_divider_mode == "str":
			data_out = []
			for this_measure in ms:
				for this_obj in this_measure.recurse().stream().iter.notesAndRests:
					start = this_obj.offset
					stop = this_obj.offset + this_obj.quarterLength
					if ignore_grace:
						if start == stop:
							continue
					data_out.append((this_obj, (start, stop)))

				if not(this_measure.number == ms[-1].number):
					data_out.append("B")
		else:
			raise Exception("Only allowed modes are `str` and `list`.")

		return data_out

def phrase_divider(
		filepath,
		part_num
	):
	"""
	This is an oversimplified but useful tool for phrase analysis (particularly for the birdsongs).
	It returns the same output as :obj:`decitala.utils.get_object_indices` but divides the output
	by "phrases," **only** as defined by the appearance of rests and fermatas. Ignores all dividers.

	:param str filepath: Path to file to be analyzed.
	:param int part_num: Part number to be analyzed.
	"""
	all_objects = get_object_indices(
		filepath,
		part_num
	)
	all_phrases = []
	for _, phrase in groupby(all_objects, lambda x: x[0].isRest):
		all_phrases.append(list(phrase))

	desired_phrases = []
	for phrase in all_phrases:
		if phrase[0][0].isRest:
			continue
		else:
			desired_phrases.append(phrase)

	return desired_phrases

def reframe_ts(ts, new_denominator=None):
	"""
	Function for reducing a `music21.meter.TimeSignature` object (lowest denominator of 1) to
	a given denominiator.

	:param ts: a music21.meter.TimeSignature object.
	:return: a new time signature that is fully reduced by removing all possible powers of 2.
	:rtype: music21.meter.TimeSignature

	>>> from music21.meter import TimeSignature
	>>> reframe_ts(TimeSignature("4/16"))
	<music21.meter.TimeSignature 1/4>
	>>> reframe_ts(TimeSignature("4/4"), new_denominator=2)
	<music21.meter.TimeSignature 2/2>
	"""
	numerator = ts.numerator
	denominator = ts.denominator
	if new_denominator is None:
		new_denominator = VALID_DENOMINATORS[0]
	else:
		assert new_denominator in set(VALID_DENOMINATORS)

	if new_denominator <= ts.numerator:
		while numerator % 2 == 0 and denominator > new_denominator:
			numerator = numerator / 2
			denominator = denominator / 2
	else:
		while denominator < new_denominator:
			numerator = numerator * 2
			denominator = denominator * 2

	reduced_ts_str = f"{int(numerator)}/{int(denominator)}"
	return TimeSignature(reduced_ts_str)

def contiguous_summation(data):
	"""
	Given some ``data`` from :obj:`~decitala.utils.get_object_indices`, finds every location
	where the pitch and rhythmic material are contiguously equal and sums these regions.

	>>> from music21 import note, chord
	>>> example_data = [
	...		(note.Note("F#"), (6.5, 6.75)),
	...     (note.Note("G"), (6.75, 7.0)),
	...     (note.Note("G"), (7.0, 7.25)),
	...     (note.Note("C#"), (7.25, 7.5)),
	...     (note.Note("G"), (7.5, 7.75)),
	...     (note.Note("G"), (7.75, 8.0)),
	...     (note.Note("A-"), (8.0, 8.125)),
	... ]
	>>> for this_object in contiguous_summation(example_data):
	...     print(this_object)
	(<music21.note.Note F#>, (6.5, 6.75))
	(<music21.note.Note G>, (6.75, 7.25))
	(<music21.note.Note C#>, (7.25, 7.5))
	(<music21.note.Note G>, (7.5, 8.0))
	(<music21.note.Note A->, (8.0, 8.125))
	>>> # Also works with chords.
	>>> example_data2 = [
	... 	(chord.Chord(["F#2", "F3"], quarterLength=0.125), (0.0, 0.125)),
	... 	(chord.Chord(["F#2", "F3"], quarterLength=0.125), (0.125, 0.25)),
	... 	(chord.Chord(["F#2", "F3"], quarterLength=0.125), (0.25, 0.375)),
	... 	(chord.Chord(["E-3", "D4"], quarterLength=0.125), (0.375, 0.5)),
	... 	(chord.Chord(["A2", "A-3"], quarterLength=0.25), (0.5, 0.75)),
	... ]
	>>> sum_search = contiguous_summation(example_data2)
	>>> for this_object in sum_search:
	...     print(this_object)
	(<music21.chord.Chord F#2 F3>, (0.0, 0.375))
	(<music21.chord.Chord E-3 D4>, (0.375, 0.5))
	(<music21.chord.Chord A2 A-3>, (0.5, 0.75))
	>>> # The quarter lengths of the objects change according to the new summation.
	>>> for this_object in sum_search:
	... 	print(this_object[0].quarterLength)
	0.375
	0.125
	0.25
	"""
	copied_data = copy.deepcopy(data)
	copied_data = [x for x in copied_data if not(type(x[0]).__name__ == "Rest")]
	regions_property = lambda i: ((copied_data[i][1][1] - copied_data[i][1][0]), [x.midi for x in copied_data[i][0].pitches])  # noqa: E501
	ranges = [list(this_range) for _, this_range in groupby(range(len(copied_data)), regions_property)]

	cluster_index_ranges = [[this_range[0], this_range[-1]] for this_range in ranges if len(this_range) > 1]  # noqa: E501
	compliment_ranges = _compliment_of_index_ranges(copied_data, cluster_index_ranges)

	new_objects = [0] * len(copied_data)

	for this_index_range in cluster_index_ranges:
		start, stop = this_index_range[0], this_index_range[1]
		start_offset = copied_data[start][1][0]
		stop_offset = copied_data[stop][1][-1]

		pitch_data = copied_data[start][0]
		summed_data = (pitch_data, (start_offset, stop_offset))

		new_objects[this_index_range[0]] = summed_data

	for x in compliment_ranges:
		if len(x) == 1:
			new_objects[x[0]] = copied_data[x[0]]
		else:
			new_objects[x[0]:x[1] + 1] = copied_data[x[0]:x[1] + 1]

	new_objects = [x for x in new_objects if x != 0]

	for this_data in new_objects:
		new_ql = this_data[1][1] - this_data[1][0]
		this_data[0].quarterLength = new_ql

	return new_objects

def frame_to_ql_array(frame):
	"""
	:param list frame: frame of data from :obj:`~decitala.utils.get_object_indices`.
	:return: numpy array holding the associated quarter length of a given window.
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
	:param list frame: frame of data from :obj:`~decitala.utils.get_object_indices`.
	:return: numpy array holding the pitches within the frame.
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
	:param list frame: frame from :obj:`~decitala.utils.get_object_indices`.
	:return: whether or not the frame is spanned by a music21.spanner.Slur object.
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

def filter_single_anga_class_fragments(data):
	"""
	:param list data: data from :obj:`~decitala.trees.rolling_search`.
	:return: data from the input with all single-anga-class talas removed. For information on anga-class, see:
			:obj:`~decitala.fragment.Decitala.num_anga_classes`.
	:rtype: list

	>>> from decitala.fragment import GreekFoot
	>>> data = [
	... {'fragment': GreekFoot("Spondee"), 'mod': ('r', 0.125), 'onset_range': (0.0, 0.5), 'is_spanned_by_slur': False, 'pitch_content': [(80,), (91,)]},  # noqa: E501
	... {'fragment': GreekFoot("Trochee"), 'mod': ('r', 0.125), 'onset_range': (0.25, 0.625), 'is_spanned_by_slur': False, 'pitch_content': [(91,), (78,)]},
	... {'fragment': GreekFoot("Spondee"), 'mod': ('r', 0.0625), 'onset_range': (0.5, 0.75), 'is_spanned_by_slur': False, 'pitch_content': [(78,), (85,)]},
	... {'fragment': GreekFoot("Iamb"), 'mod': ('r', 0.125), 'onset_range': (0.625, 1.0), 'is_spanned_by_slur': False, 'pitch_content': [(85,), (93,)]},
	... {'fragment': GreekFoot("Spondee"), 'mod': ('r', 0.125), 'onset_range': (0.75, 1.25), 'is_spanned_by_slur': False, 'pitch_content': [(93,), (91,)]}
	... ]
	>>> filtered = filter_single_anga_class_fragments(data)
	>>> for x in filtered:
	... 	print(x)
	{'fragment': <fragment.GreekFoot Trochee>, 'mod': ('r', 0.125), 'onset_range': (0.25, 0.625), 'is_spanned_by_slur': False, 'pitch_content': [(91,), (78,)]}
	{'fragment': <fragment.GreekFoot Iamb>, 'mod': ('r', 0.125), 'onset_range': (0.625, 1.0), 'is_spanned_by_slur': False, 'pitch_content': [(85,), (93,)]}
	"""
	return list(filter(lambda x: x["fragment"].num_anga_classes != 1, data))

def filter_sub_fragments(data, filter_in_retrograde=True):
	"""
	:param list data: data from :obj:`~decitala.trees.rolling_search`.
	:return: data from the input with all sub-talas removed; that is, talas that sit inside of another.
	:rtype: list
	"""
	just_fragments = list(set([x["fragment"] for x in data]))

	def _check_all(x):
		check = False
		for this_fragment in just_fragments:
			if np.array_equal(this_fragment.ql_array(), x.ql_array()):
				pass
			else:
				if x.is_sub_fragment(this_fragment, filter_in_retrograde):
					check = True
		return check

	filtered_names = [x.name for x in just_fragments if not(_check_all(x))]
	return [x for x in data if x["fragment"].name in filtered_names]

def measure_by_measure_time_signatures(filepath):
	"""
	Returns list of meter.TimeSignature objects from music21 for each measure of an input
	stream.
	"""
	converted = converter.parse(filepath)
	p = converted.parts[0]
	ts = []
	for i, this_measure in enumerate(p.getElementsByClass(stream.Measure), start=1):
		for this_obj in this_measure.recurse().iter:
			if type(this_obj) == TimeSignature:
				ts.append(this_obj)
		if i == len(ts):
			pass
		else:
			ts.append(ts[-1])
	return ts

####################################################################################################
# PITCH CONTOUR
####################################################################################################
def pitch_content_to_contour(pitch_content, as_str=False):
	"""
	This function calculates the pitch contour information from data out of rolling_search.
	This function assumes the data is monophonic.

	:param list pitch_content: pitch content from the output of rolling_search."

	>>> pc = [(80,), (91,), (78,), (85,)]
	>>> pitch_content_to_contour(pc)
	array([1, 3, 0, 2])
	>>> pc2 = [(80,), (84,), (84,)]
	>>> pitch_content_to_contour(pc2)
	array([0, 1, 1])
	"""
	if type(pitch_content[0]) == tuple:
		to_mono = [x[0] for x in pitch_content]
	else:
		to_mono = pitch_content
	seg_vals = copy.copy(to_mono)
	value_dict = dict()

	for i, this_val in zip(range(0, len(sorted(set(seg_vals)))), sorted(set(seg_vals))):
		value_dict[this_val] = str(i)

	for i, this_val in enumerate(seg_vals):
		for this_key in value_dict:
			if this_val == this_key:
				seg_vals[i] = value_dict[this_key]

	if not(as_str):
		return np.array([int(val) for val in seg_vals])
	else:
		return "<" + " ".join([str(int(val)) for val in seg_vals]) + ">"

def contour_to_neume(contour):
	"""
	Function for checking the associated neume for a given contour. Only two and three onset
	contour are supported.

	:param contour: A pitch contour (iterable).
	:return: The associated neume or ``None``.
	:rtype: str or None
	"""
	assert len(contour) <= 3, UtilsException("Contour input must be of length three!")
	try:
		return NEUMES[tuple(contour)]
	except KeyError:
		return None

def _has_extremum(window, mode):
	"""
	>>> min_check = ([0, {1, -1}], [2, {-1}], [1, {1, -1}])
	>>> _has_extremum(min_check, "min")
	False
	>>> _has_extremum(min_check, "max")
	True
	"""
	assert len(window) == 3
	middle_val = window[1][0]
	if mode == "max":
		if middle_val >= window[0][0] and middle_val >= window[2][0]:
			return True
		else:
			return False
	elif mode == "min":
		if middle_val <= window[0][0] and middle_val <= window[2][0]:
			return True
		else:
			return False

def _initial_extremas(contour):
	"""
	First iteration, get extrema.

	>>> contour = [0, 4, 3, 2, 5, 5, 1]
	>>> _initial_extremas(contour)
	[[0, {1, -1}], [4, {1}], [3, set()], [2, {-1}], [5, {1}], [5, {1}], [1, {1, -1}]]
	"""
	out = [[contour[0], {-1, 1}]]
	for this_frame in roll_window(contour, 3):
		elem_set = set()
		middle_val = this_frame[1]
		if middle_val >= this_frame[0] and middle_val >= this_frame[2]:
			elem_set.add(1)
		if middle_val <= this_frame[0] and middle_val <= this_frame[2]:
			elem_set.add(-1)

		out.append([middle_val, elem_set])

	out.append([contour[-1], {-1, 1}])

	return out

def _make_level(contour):
	"""
	Runs one iteration of the reduction.

	>>> data = [[1, {1, -1}], [3, {1}], [1, set()], [2, set()], [0, {-1}], [1, set()], [4, {1, -1}]]
	>>> new = _make_level(data)
	>>> new
	[[1, {1, -1}], [3, set()], [1, set()], [2, set()], [0, {-1}], [1, set()], [4, {1, -1}]]
	>>> _make_level(new) == new
	True
	>>> # remove clusters
	>>> initial_extremas = [
	...		[0, {1, -1}],
	... 	[4, {1}],
	... 	[3, set()],
	... 	[2, {-1}],
	... 	[5, {1}],
	... 	[5, {1}],
	... 	[1, {1, -1}]
	...	]
	"""
	fnmax = lambda x: 1 in x[1]
	fnmin = lambda x: -1 in x[1]

	for i, this_window in enumerate(roll_window(contour, 3, fnmax)):
		elem_set = this_window[1][1]
		if len(elem_set) == 0:
			continue
		elif None in this_window:
			continue
		else:
			if _has_extremum(this_window, "max"):
				pass
			else:
				elem_set.remove(1)

	for i, this_window in enumerate(roll_window(contour, 3, fnmin)):
		elem_set = this_window[1][1]
		if len(elem_set) == 0:
			continue
		elif None in this_window:
			continue
		else:
			if _has_extremum(this_window, "min"):
				pass
			else:
				elem_set.remove(-1)

	ranges = []
	for _, this_range in groupby(range(len(contour)), lambda i: (contour[i][0], contour[i][1])):
		ranges.append(list(this_range))
	del_clusters = []

	for this_cluster in ranges:
		if len(this_cluster) > 1:
			del_clusters.extend(this_cluster[1:])

	if len(del_clusters) != 0:
		for index in sorted(del_clusters, reverse=True):
			del contour[index]

	return contour

def contour_to_prime_contour(contour, include_depth=False):
	"""
	Implementation of Morris' 1993 Contour-Reduction algorithm. "The algorithm prunes pitches
	from a contour until it is reduced to a prime." The loop runs until all elements
	are flagged as maxima or minima.

	:param np.array contour: contour input

	>>> contour_a = [0, 1]
	>>> contour_to_prime_contour(contour_a)
	array([0, 1])
	>>> contour_b = [0, 4, 3, 2, 5, 5, 1]
	>>> contour_to_prime_contour(contour_b, include_depth=False)
	array([0, 2, 1])
	>>> contour_c = [1, 3, 1, 2, 0, 1, 4]
	>>> contour_to_prime_contour(contour_c, include_depth=False)
	array([1, 0, 2])
	>>> contour_d = [0, 1, 1]
	>>> contour_to_prime_contour(contour_d, include_depth=False)
	array([0, 1, 1])
	"""
	depth = 0
	if len(contour) <= 2:
		if not(include_depth):
			return pitch_content_to_contour(contour)
		else:
			return (pitch_content_to_contour(contour), depth)

	prime_contour = _initial_extremas(contour)
	if all([len(x[1]) != 0 for x in prime_contour]):
		if not(include_depth):
			return pitch_content_to_contour(contour)
		else:
			return (pitch_content_to_contour(contour), depth)

	still_unflagged_values = True
	while still_unflagged_values is True:
		_make_level(prime_contour)
		depth += 1
		if _make_level(prime_contour[:]) == prime_contour:  # Check next iteration...
			still_unflagged_values = False
		else:
			continue

	prime_contour = [x[0] for x in prime_contour if len(x[1]) != 0]
	depth += 1

	if not(include_depth):
		return pitch_content_to_contour(prime_contour)
	else:
		return (pitch_content_to_contour(prime_contour), depth)

def is_octatonic_collection(pitch_content):
	"""
	Function for checking if pitch content belongs to one of the two octatonic collections.

	>>> is_octatonic_collection([60, 62, 64, 66, 68])
	False
	>>> is_octatonic_collection([60, 61, 63, 64, 66])
	True
	"""
	o1 = set([x.pitchClass for x in scale.OctatonicScale(tonic=pitch.Pitch(pitch_content[0]), mode=1).getPitches()]) # noqa 
	o2 = set([x.pitchClass for x in scale.OctatonicScale(tonic=pitch.Pitch(pitch_content[0]), mode=2).getPitches()]) # noqa

	pc_set = set([pitch.Pitch(x).pitchClass for x in pitch_content])
	if pc_set.issubset(o1):
		return True
	elif pc_set.issubset(o2):
		return True
	else:
		return False

####################################################################################################
# MATH HELPERS
####################################################################################################
def cauchy_schwartz(vector1, vector2):
	"""
	Tests the Cauchy-Schwartz inequality on two vectors. Namely, if the absolute value of
	the dot product of the two vectors is less than the product of the norms, the vectors are
	linearly independant (and the function returns True); if they are equal, they are dependant
	(and the function returns False).

	Linear Independence:
	>>> li_vec1 = np.array([0.375, 1.0, 0.25])
	>>> li_vec2 = np.array([1.0, 0.0, 0.5])
	>>> cauchy_schwartz(li_vec1, li_vec2)
	True

	>>> cauchy_schwartz(np.array([0.75, 0.5]), np.array([1.5, 1.0]))
	False

	Linear Dependance:
	>>> ld_vec1 = np.array([1.0, 2.0, 4.0, 8.0])
	>>> ld_vec2 = np.array([0.5, 1.0, 2.0, 4.0])
	>>> cauchy_schwartz(ld_vec1, ld_vec2)
	False

	Equal:
	>>> e_vec1 = np.array([0.25, 0.25, 0.25, 0.25])
	>>> e_vec2 = np.array([0.25, 0.25, 0.25, 0.25])
	>>> cauchy_schwartz(e_vec1, e_vec2)
	False
	"""
	assert len(vector1) == len(vector2)
	return abs(np.dot(vector1, vector2)) < (norm(vector1) * norm(vector2))

####################################################################################################
# JSON WRITING / LOADING
####################################################################################################
def loader(filepath):
	"""
	Useful function for loading analyses into native python format (from a json).

	:param str filepath: path to analysis file in the databases/analyses directory.
	:return: analysis in native python types. Fragments and their associated onset range.
	:rtype: list
	"""
	with open(filepath) as file_json:
		data = json.load(file_json, cls=fragment.FragmentDecoder)
		return data

def write_analysis(data, filepath):
	"""
	Function for writing an `analysis` to JSON.
	"""
	with open(filepath, "w") as output:
		json.dump(obj=data, fp=output, cls=fragment.FragmentEncoder, ensure_ascii=False, indent=4)