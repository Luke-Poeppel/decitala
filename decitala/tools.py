# -*- coding: utf-8 -*-
####################################################################################################
# File:     tools.py
# Purpose:  Random useful functions for Messiaen. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
TODO: use numpy/scipy norm function, obviously. 
"""
import decimal
import numpy as np

from music21 import converter

####################################################################################################
# Rhythm helpers

def augment_multiplicatively(array, factor):
	pass

def augment_additively(array, difference):
	pass

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


