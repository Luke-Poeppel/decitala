####################################################################################################
# File:     utils.py
# Purpose:  Random useful functions. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020 / Frankfurt, DE 2020
####################################################################################################
import copy
import decimal
import numpy as np

from itertools import chain, combinations, groupby
from more_itertools import consecutive_groups, windowed, powerset, groupby_transform
from scipy.linalg import norm

from music21 import chord
from music21 import converter
from music21 import note
from music21 import spanner
from music21 import stream

carnatic_symbols = np.array([
	['Druta', 'o', 0.25],
	['Druta-Virama', 'oc', 0.375],
	['Laghu', '|', 0.5],
	['Laghu-Virama', '|c', 0.75],
	['Guru', 'S', 1.0],
	['Pluta', 'Sc', 1.5],           # Note: Normally a crescent moon superscript. Since it serves the same function as a virâma––we use the same notation. 
	#['kakapadam', '8X', 2.0]       # Decide what the appropriate convention is...
])

greek_diacritics = [
	['breve', '⏑', 1.0],
	['macron', '––', 2.0]
]

multiplicative_augmentations = [
	['Tiers', 4/3],
	['Un quart', 1.25],
	['Du Point', 1.5],
	['Classique', 2], 
	['Double', 3],
	['Triple', 4],
]

####################################################################################################
# Notational Conversion Functions
def carnatic_string_to_ql_array(string_):
	"""
	:param str string_: string of carnatic durations separated by spaces. 
	:return: input string converted to a quarter length array. 
	:rtype: numpy.array. 
	
	>>> carnatic_string_to_ql_array('oc o | | Sc S o o o')
	array([0.375, 0.25 , 0.5  , 0.5  , 1.5  , 1.   , 0.25 , 0.25 , 0.25 ])
	"""
	split_string = string_.split()
	return np.array([float(this_carnatic_val[2]) for this_token in split_string for this_carnatic_val in carnatic_symbols if (this_carnatic_val[1] == this_token)])

def ql_array_to_carnatic_string(ql_array):
	"""
	:param iterable ql_array: quarter length array. 
	:return: quarter length array converted to carnatic notation.
	:rtype: str
	
	>>> ql_array_to_carnatic_string([0.5, 0.25, 0.25, 0.375, 1.0, 1.5, 1.0, 0.5, 1.0])
	'| o o oc S Sc S | S'
	"""
	return ' '.join(np.array([this_carnatic_val[1] for this_val in ql_array for this_carnatic_val in carnatic_symbols if (float(this_carnatic_val[2]) == this_val)]))

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
	ql_array = np.array(ql_array) # Ensures native numpy type.
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

	return ' '.join(greek_string_lst)

####################################################################################################
# Rhythm helpers
def augment(fragment, factor=1.0, difference=0.0):
	"""
	Returns an augmentation in the style of Messiaen. If difference is set to 0.0, then the augmentation
	is multiplicative. If factor is set to 1.0, then augmentation is additive. If factor & difference are
	non-zero, we have a mixed augmentation. 

	:param numpy.array fragment: array defining the rhythmic fragment.
	:param float factor: factor for multiplicative augmentation.
	:param float difference: factor for additive augmentation.

	:return: an augmented fragment.
	:rtype: numpy.array

	>>> augment(fragment=[1.0, 1.0, 0.5, 0.25], factor=2.0, difference=0.25)
	array([2.25, 2.25, 1.25, 0.75])
	"""
	assert factor >= 0.0
	return np.array([(this_val * factor) + difference for this_val in fragment])

def successive_ratio_array(fragment):
	"""
	Returns array defined by the ratio of successive elements. By convention, we set the first value to 1.0.

	:param numpy.array fragment: array defining a rhythmic fragment.
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
	while i < len(fragment) - 1:
		ratio_lst.append(_ratio(fragment, i))
		i += 1

	return np.array(ratio_lst)

def successive_difference_array(fragment):
	"""
	Returns the first order difference of ``fragment`` (contiguous differences). 

	:param numpy.array fragment: array defining a rhythmic fragment.
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
	while i < len(fragment) - 1:
		difference_lst.append(_difference(fragment, i))
		i += 1

	return np.array(difference_lst)

# def contiguous_multiplication(array):
# 	"""
# 	Takes the zeroth value in the array and successively multiplies by the next value. As 
# 	such, the dimension of the output vector is :math:`n + 1` for :math:`n` the original dimension.

# 	:param numpy.array fragment: arbitrary array.
# 	:return: array consisting of the successive product of the elements in the array.
# 	:rtype: numpy.array

# 	>>> ex = np.array([-1, 0.5, -3])
# 	>>> contiguous_multiplication(ex)
# 	array([-1. ,  1. ,  0.5, -1.5])
# 	"""
# 	out = [array[0]]
# 	i = 0
# 	while i < len(array) - 1:
# 		if i == 0:
# 			first_elem_squared = array[i]**2
# 			out.append(first_elem_squared)
# 			out.append(first_elem_squared * array[i + 1])
# 		else:
# 			out.append(array[i] * array[i + 1])
# 		i += 1 
# 	return np.array(out)

####################################################################################################
# Subdivision
def find_clusters(input_, data_mode=False):
	"""
	Finds the regions with consecutive equal elements.

	:param iterable input_: either a list/array (representing :obj:`~decitala.fragment.GeneralFragment.ql_array`) 
							or data from :obj:`~decitala.utils.get_object_indices`.
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
	>>> # We can also find clusters of pitch and rhythmic information for data from :obj:`~decitala.utils.get_object_indices`. 
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
		regions_property = lambda i: (input_[i][1][1] - input_[i][1][0] and [x.midi for x in input_[i][0].pitches])
		ranges = [list(this_range) for _, this_range in groupby(range(len(input_)), regions_property)]

	cluster_index_ranges = [[this_range[0], this_range[-1]] for this_range in ranges if len(this_range) > 1]

	return cluster_index_ranges

def _compliment_of_index_ranges(array, clusters):
	"""
	TODO: if the compliment range has only one val, it should just be one val, not two (otherwise can't distinguish). 

	>>> varied_ragavardhana = np.array([1, 1, 1, 0.5, 0.75, 0.5])
	>>> _compliment_of_index_ranges(varied_ragavardhana, [find_clusters(varied_ragavardhana)[0]]) 
	[[3, 5]]
	>>> varied_ragavardhana_2 = np.array([1, 1, 1, 0.5, 0.75, 0.75, 0.5, 0.25, 0.25, 0.25])
	>>> _compliment_of_index_ranges(varied_ragavardhana_2, find_clusters(varied_ragavardhana_2))
	[[3], [6]]
	>>> 
	"""
	flattened_cluster_ranges = []
	for this_range in clusters:
		index_range = list(range(this_range[0], this_range[1]+1))
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
			superdivision[x[0]:x[1]+1] = array[x[0]:x[1]+1]

	for this_cluster in clusters:
		region = array[this_cluster[0]:this_cluster[1]+1] # this is good too! 
		summed = sum(region)
		superdivision[this_cluster[0]] = summed # this is the problem. 
		
	return np.array([x for x in superdivision if x != 0])
	
def find_possible_superdivisions(array):
	"""
	There is a more general approach to the subdivision problem, but we note that Messiaen's subdivision
	of tala components tends to be even. 

	>>> varied_ragavardhana = np.array([1, 1, 1, 0.5, 0.75, 0.5])
	>>> for x in find_possible_superdivisions(varied_ragavardhana):
	...     print(x)
	[1.   1.   1.   0.5  0.75 0.5 ]
	[3.   0.5  0.75 0.5 ]
	
	>>> varied_ragavardhana_2 = np.array([1, 1, 1, 0.5, 0.75, 0.75, 0.5, 0.25, 0.25, 0.25])
	>>> for x in find_possible_superdivisions(varied_ragavardhana_2):
	...     print(x)
	[1.   1.   1.   0.5  0.75 0.75 0.5  0.25 0.25 0.25]
	[3.   0.5  0.75 0.75 0.5  0.25 0.25 0.25]
	[1.   1.   1.   0.5  1.5  0.5  0.25 0.25 0.25]
	[1.   1.   1.   0.5  0.75 0.75 0.5  0.75]
	[3.   0.5  1.5  0.5  0.25 0.25 0.25]
	[3.   0.5  0.75 0.75 0.5  0.75]
	[1.   1.   1.   0.5  1.5  0.5  0.75]
	[3.   0.5  1.5  0.5  0.75]
	"""
	possible_super_divisions = [np.array(array)]
	clusters = find_clusters(array)
	possible_combinations = power_list(clusters)
	for this_combination in possible_combinations:
		superdivision = _make_one_superdivision(array, this_combination)
		possible_super_divisions.append(superdivision)
	
	return possible_super_divisions

####################################################################################################
# La Valeur Ajoutee
def get_added_values(ql_lst, print_type = True):
	"""
	Given a quarter length list, returns all indices and types of added values found, according to 
	the examples dicussed in Technique de Mon Langage Musical (1944). 

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
	if len(ql_lst) < 3:
		raise Exception('List must be of length 3 or greater.')

	addedVals = []
	if ql_lst[0] == 0.25 and ql_lst[1] != 0.25:
		addedVals.append((0, 'du Note'))
	if ql_lst[-1] == 0.25 and ql_lst[-2] != 0.25:
		addedVals.append((len(ql_lst) - 1, 'du Note'))
	if ql_lst[-1] == 0.75 and ql_lst[-2] % 0.5 == 0:
		addedVals.append((len(ql_lst) - 1, 'du Point'))

	for currIndex in range(1, len(ql_lst) - 1):
		prevVal = ql_lst[currIndex - 1]
		currVal = ql_lst[currIndex]
		nextVal = ql_lst[currIndex + 1]

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

	if print_type == False:
		return [a[0] for a in addedVals]
	else:
		return addedVals

#NOTE: Double check this works.
def removeAddedValuesFromList(lst):
	added_val_indices = get_added_values(ql_lst=lst, print_type=False)
	for i in added_val_indices:
		del lst[i]

	return lst

####################################################################################################
# Windowing
def roll_window(array, window_length):
	"""
	Takes in a list and returns a numpy vstack holding rolling windows of length ``window_length``.

	:param numpy.array array: an iterable
	:return: rolling windows of array, each of length `window_length`. 
	:rtype: numpy.vstack

	>>> composers = np.array(['Mozart', 'Monteverdi', 'Messiaen', 'Mahler', 'MacDowell', 'Massenet'])
	>>> for window in roll_window(array=composers, window_length=3):
	...     print(window)
	('Mozart', 'Monteverdi', 'Messiaen')
	('Monteverdi', 'Messiaen', 'Mahler')
	('Messiaen', 'Mahler', 'MacDowell')
	('Mahler', 'MacDowell', 'Massenet')
	"""
	assert type(window_length) == int
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
# Math helpers
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
	return abs(np.dot(vector1, vector2)) <  (norm(vector1) * norm(vector2))

####################################################################################################
# Score helpers
def get_object_indices(filepath, part_num):
	"""
	Returns data of the form [(object, (start, end)), ...] for a given file path and part number. 
	(Supports rests and grace notes.)
	"""
	score = converter.parse(filepath)
	part = score.parts[part_num]
	data_out = []
	stripped = part.stripTies(retainContainers = True)
	for this_obj in stripped.recurse().iter.notesAndRests:
		data_out.append((this_obj, (this_obj.offset, this_obj.offset + this_obj.quarterLength)))

	return data_out

def contiguous_summation(data):
	"""
	Given some ``data`` from :obj:`~decitala.utils.get_object_indices`, finds every location where the pitch and 
	rhythmic material are contiguously equal and sums these regions. 
	
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
	new_data = []
	regions_property = lambda i: ((copied_data[i][1][1] - copied_data[i][1][0]), [x.midi for x in copied_data[i][0].pitches])
	ranges = [list(this_range) for _, this_range in groupby(range(len(copied_data)), regions_property)]
		
	cluster_index_ranges = [[this_range[0], this_range[-1]] for this_range in ranges if len(this_range) > 1]
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
			new_objects[x[0]:x[1]+1] = copied_data[x[0]:x[1]+1]
	
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
	# TODO: make midi
	midi_out = []
	for this_obj, this_range in frame:
		if not(ignore_graces): # add everything
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
		if "Slur" in spanners[0].classes:
			slur_spanner = spanners[0]
			if slur_spanner.isFirst(first_obj) and slur_spanner.isLast(last_obj):
				is_spanned_by_slur = True

	return is_spanned_by_slur

def filter_single_anga_class_fragments(data):
	"""
	:param list data: data from :obj:`~decitala.trees.rolling_search`.
	:return: data from the input with all single-anga-class talas removed. For information on anga-class, see: 
			:obj:`decitala.fragment.Decitala.num_anga_classes`.
	:rtype: list

	>>> from decitala.fragment import GreekFoot
	>>> data = [
	... 	{'fragment': GreekFoot("Spondee"), 'mod': ('r', 0.125), 'onset_range': (0.0, 0.5), 'is_spanned_by_slur': False, 'pitch_content': [(80,), (91,)]},
	... 	{'fragment': GreekFoot("Trochee"), 'mod': ('r', 0.125), 'onset_range': (0.25, 0.625), 'is_spanned_by_slur': False, 'pitch_content': [(91,), (78,)]},
	... 	{'fragment': GreekFoot("Spondee"), 'mod': ('r', 0.0625), 'onset_range': (0.5, 0.75), 'is_spanned_by_slur': False, 'pitch_content': [(78,), (85,)]},
	... 	{'fragment': GreekFoot("Iamb"), 'mod': ('r', 0.125), 'onset_range': (0.625, 1.0), 'is_spanned_by_slur': False, 'pitch_content': [(85,), (93,)]},
	... 	{'fragment': GreekFoot("Spondee"), 'mod': ('r', 0.125), 'onset_range': (0.75, 1.25), 'is_spanned_by_slur': False, 'pitch_content': [(93,), (91,)]}
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