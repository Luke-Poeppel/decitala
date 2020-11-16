# -*- coding: utf-8 -*-
####################################################################################################
# File:     tools.py
# Purpose:  Random useful functions. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020 / Frankfurt, DE 2020
####################################################################################################
import decimal
import numpy as np

from itertools import chain, combinations

from music21 import converter

carnatic_symbols = np.array([
	['Druta', 'o', 0.25],
	['Druta-Virama', 'oc', 0.375],
	['Laghu', '|', 0.5],
	['Laghu-Virama', '|c', 0.75],
	['Guru', 'S', 1.0],
	['Pluta', 'Sc', 1.5],           #Note: Normally a crescent moon superscript. Since it serves the same function as a virâma––we use the same notation. 
	#['kakapadam', '8X', 2.0]       #Decide what the appropriate convention is...
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
	assert factor >= 1.0
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
			raise Exception('Something is off...')

	ratio_lst = [1.0]
	i = 0
	while i < len(fragment) - 1:
		ratio_lst.append(_ratio(fragment, i))
		i += 1

	return np.array(ratio_lst)

def successive_difference_array(fragment):
	"""
	Returns array defined by the difference of successive elements. By convention, we set the first value to 0.0.

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

def contiguous_multiplication(array):
	"""
	Takes the zeroth value in the array and successively multiplies by the next value. As 
	such, the dimension of the output vector is :math:`n + 1` for :math:`n` the original dimension.

	:param numpy.array fragment: arbitrary array.
	:return: array consisting of the successive product of the elements in the array.
	:rtype: numpy.array

	>>> ex = np.array([-1, 0.5, -3])
	>>> contiguous_multiplication(ex)
	array([-1. ,  1. ,  0.5, -1.5])
	"""
	out = [array[0]]
	i = 0
	while i < len(array) - 1:
		if i == 0:
			first_elem_squared = array[i]**2
			out.append(first_elem_squared)
			out.append(first_elem_squared * array[i + 1])
		else:
			out.append(array[i] * array[i + 1])
		i += 1 
	return np.array(out)

####################################################################################################
# Notational Conversion Functions
def carnatic_string_to_ql_array(string):
	"""
	:return: a string of carnatic values converted to a standard ql array. 
	:rtype: numpy.array. 
	
	NOTE: The carnatic symbols must have spaces between them or there will be conversion issues. 

	>>> carnatic_string_to_ql_array(string = 'oc o | | Sc S o o o')
	array([0.375, 0.25 , 0.5  , 0.5  , 1.5  , 1.   , 0.25 , 0.25 , 0.25 ])
	"""
	split_string = string.split()
	return np.array([float(this_carnatic_val[2]) for this_token in split_string for this_carnatic_val in carnatic_symbols if (this_carnatic_val[1] == this_token)])

def ql_array_to_carnatic_string(ql_array):
	"""
	:return: a list of quarter length values converted to carnatic rhythmic notation.
	:rtype: str
	
	>>> ql_array_to_carnatic_string([0.5, 0.25, 0.25, 0.375, 1.0, 1.5, 1.0, 0.5, 1.0])
	'| o o oc S Sc S | S'
	"""
	return ' '.join(np.array([this_carnatic_val[1] for this_val in ql_array for this_carnatic_val in carnatic_symbols if (float(this_carnatic_val[2]) == this_val)]))

def ql_array_to_greek_diacritics(ql_array):
	"""
	Returns the input ``ql_array`` in greek prosodic notation. This notation only allows
	for two types of rhythmic values (long & short). 

	:param numpy.array 
	:return: a list of quarter length values converted to greek prosodic notation.
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
# Windowing
def roll_window(lst, window_length):
	'''
	Takes in a list and returns a list of lists that holds rolling windows of length window_length.

	>>> l = ['Mozart', 'Monteverdi', 'Messiaen', 'Mahler', 'MacDowell', 'Massenet']
	>>> for this in roll_window(lst=l, window_length=3):
	...     print(this)
	['Mozart', 'Monteverdi', 'Messiaen']
	['Monteverdi', 'Messiaen', 'Mahler']
	['Messiaen', 'Mahler', 'MacDowell']
	['Mahler', 'MacDowell', 'Massenet']
	'''
	assert type(window_length) == int

	l = []
	iterable = iter(lst)
	win = []
	for _ in range(0, window_length):
		win.append(next(iterable))
	
	l.append(win)

	for thisElem in iterable:
		win = win[1:] + [thisElem]
		l.append(win)

	return l

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
# Score helpers
def get_stripped_object_list(filepath, part_num):
	'''
	Returns the quarter length list of an input stream (with ties removed), but also includes 
	spaces for rests.

	NOTE: this used to be .iter.notesAndRest, but I took it away, for now, to avoid complications.
	'''
	score = converter.parse(filepath)
	part = score.parts[part_num]
	object_list = []

	stripped = part.stripTies(retainContainers = True)
	for this_obj in stripped.recurse().iter.notes: 
		object_list.append(this_obj)

	return object_list
	
def get_indices_of_object_occurrence(filepath, part_num):
	'''
	Given a file path and part number, returns a list containing tuples of the form [(OBJ, (start, end))].

	>>> bach_path = '/Users/lukepoeppel/Documents/GitHub/music21/music21/corpus/bach/bwv66.6.mxl'
	>>> for data in get_indices_of_object_occurrence(bach_path, 0)[0:12]:
	...     print(data)
	(<music21.note.Note C#>, (0.0, 0.5))
	(<music21.note.Note B>, (0.5, 1.0))
	(<music21.note.Note A>, (1.0, 2.0))
	(<music21.note.Note B>, (2.0, 3.0))
	(<music21.note.Note C#>, (3.0, 4.0))
	(<music21.note.Note E>, (4.0, 5.0))
	(<music21.note.Note C#>, (5.0, 6.0))
	(<music21.note.Note B>, (6.0, 7.0))
	(<music21.note.Note A>, (7.0, 8.0))
	(<music21.note.Note C#>, (8.0, 9.0))
	(<music21.note.Note A>, (9.0, 9.5))
	(<music21.note.Note B>, (9.5, 10.0))
	'''
	data_out = []
	stripped_object_list = get_stripped_object_list(filepath, part_num)
	for this_obj in stripped_object_list:
		data_out.append((this_obj, (this_obj.offset, this_obj.offset + this_obj.quarterLength)))

	return data_out

def powerList(lst):
	"""
	Given a list, returns it's 'power set' (excluding, of course, the empty list). 

	>>> l = [1, 2, 3]
	>>> powerList(l)
	array([(1,), (2,), (3,), (1, 2), (1, 3), (2, 3), (1, 2, 3)], dtype=object)

	>>> for x in powerList([(0.0, 2.0), (4.0, 5.5), (6.0, 7.25)]):
	...     print(x)
	((0.0, 2.0),)
	((4.0, 5.5),)
	((6.0, 7.25),)
	((0.0, 2.0), (4.0, 5.5))
	((0.0, 2.0), (6.0, 7.25))
	((4.0, 5.5), (6.0, 7.25))
	((0.0, 2.0), (4.0, 5.5), (6.0, 7.25))
	"""
	s = list(lst)
	preList = list(chain.from_iterable(combinations(s, r) for r in range(len(s) + 1)))

	for x in preList:
		if len(x) == 0:
			preList.remove(x)

	return np.array(preList)

def _euclidian_norm(vector):
	'''
	Returns the euclidian norm of a vector (the square root of the inner product of a vector 
	with itself) rounded to 5 decimal places. 

	>>> _euclidian_norm(np.array([1.0, 1.0, 1.0]))
	Decimal('1.73205')
	>>> _euclidian_norm(np.array([1, 2, 3, 4]))
	Decimal('5.47722')
	'''
	norm_squared = np.dot(vector, vector)
	norm = decimal.Decimal(str(np.sqrt(norm_squared)))

	return norm.quantize(decimal.Decimal('0.00001'), decimal.ROUND_DOWN)

def cauchy_schwartz(vector1, vector2):
	'''
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
	'''
	assert len(vector1) == len(vector2)
	if abs(np.dot(vector1, vector2)) <  (_euclidian_norm(vector1) * _euclidian_norm(vector2)):
		return True
	else:
		return False

if __name__ == '__main__':
	import doctest
	doctest.testmod()


