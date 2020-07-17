# -*- coding: utf-8 -*-
####################################################################################################
# File:     pitch_contour.py
# Purpose:  Tools for analyzing & graphing pitch contour in collections of found-talas. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
Want: given a collection of talas found (in appropriate onset locations!), calculates the pitch contour
and 

Inverse pitch d segs? That could be interesting

TODO:
- rough pitch contour
- elegant pitch normalization functions
- elegant pitch contour function *as* a normalizer
	- find the name of the term used by Marvin
- average pitch contour
- plot by onset_num or by offset indexed at 0?  
- another more discrete method of plotting pitch contour is just Up/Down! 
"""
import copy
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

FONTNAME = 'Times'
FONTSIZE_TITLE = 14
FONTSIZE_LABEL = 12

def pitch_space_contour_from_midi(midi_array, as_str=False):
	"""
	Given an array of midi values, returns the pitch space contour.
	See The Perception of Rhythm in Non-Tonal Music: Rhythmic Contours in the Music of
	Edgard Varèse (Marvin, 1991)

	>>> beethoven = [60, 65, 68, 72]
	>>> pitch_space_contour_from_midi(midi_array=beethoven)
	array([0, 1, 2, 3])
	"""
	dseg_vals = copy.copy(midi_array)
	valueDict = dict()

	for i, thisVal in zip(range(0, len(sorted(set(dseg_vals)))), sorted(set(dseg_vals))):
		valueDict[thisVal] = str(i)

	for i, thisValue in enumerate(dseg_vals):
		for thisKey in valueDict:
			if thisValue == thisKey:
				dseg_vals[i] = valueDict[thisKey]

	if as_str == True:
		return '<' + ' '.join([str(int(val)) for val in dseg_vals]) + '>'
	else:
		return np.array([int(val) for val in dseg_vals])

def transform_om_to_opc(data):
	"""
	Transforms data consisting of onsets midis to onsets and pitch contour values.
	Input data should be a single example, like,
	
	>>> short_data = np.array([[0, 76], [1, 80], [2, 80], [3, 79], [3.5, 84], [4.25, 83]])
	>>> for x in transform_om_to_opc(short_data):
	...     print(x)
	[0. 0.]
	[1. 2.]
	[2. 2.]
	[3. 1.]
	[3.5 4. ]
	[4.25 3.  ]
	"""
	onset_data = [x[0] for x in data]
	pitch_data = [x[1] for x in data]
	pc = pitch_space_contour_from_midi(pitch_data)

	return np.array(list(zip(onset_data, pc)))

def rough_contour(midi_array):
	"""
	TODO implementation of "rough" contour based only on up, down, and same pitch motions. 
	"""
	raise NotImplementedError

def cosine_similarity(vector_a, vector_b):
	numerator = np.dot(vector_a, vector_b)
	denominator = np.linalg.norm(vector_a) * np.linalg.norm(vector_b)
	return (numerator / denominator)

def graphPitchContour(all_data, as_pitch_space_contour=True):
	"""
	TODO docs, as_pitch_space_contour = True
	"""
	mpl.style.use('seaborn')
	if not(as_pitch_space_contour):
		for this_tala in all_data:
			x_coords = [x[0] for x in this_tala]
			y_coords = [x[1] for x in this_tala]
			plt.plot(x_coords, y_coords, '-o', markersize=4)
	else:
		for this_tala in all_data:
			new = transform_om_to_opc(this_tala)
			x_coords = [x[0] for x in new]
			y_coords = [x[1] for x in new]
			plt.plot(x_coords, y_coords, '-o', markersize=4)

	plt.title('Râgavardhana normalized MIDI (n=10)', fontname=FONTNAME, fontsize=FONTSIZE_TITLE)
	plt.xlabel('Offset', fontname=FONTNAME, fontsize=FONTSIZE_LABEL)
	plt.ylabel('Normalized MIDI', fontname=FONTNAME, fontsize=FONTSIZE_LABEL)
	plt.xticks(np.arange(0, 5.0, 0.5))

	#plt.savefig('ragavardhana_pitch_contour_liturgie.png', dpi=800, transparent = True)#, format='eps')
	#plt.close()
	plt.show()

################################### TESTING ###################################

all_data = np.array([
	[[0, 76],
	[1, 74],
	[2, 74],
	[3, 72],
	[3.5, 72],
	[4.25, 72]],

	[[0, 76],
	[1, 73],
	[2, 69],
	[3, 73],
	[3.5, 72],
	[4.25, 71]],

	[[0, 76],
	[1, 82],
	[2, 80],
	[3, 80],
	[3.5, 83],
	[4.25, 83]],

	[[0, 76],
	[1, 71],
	[2, 73],
	[3, 74],
	[3.5, 67],
	[4.25, 64]],

	[[0, 76],
	[1, 80],
	[2, 80],
	[3, 79],
	[3.5, 84],
	[4.25, 83]],

	[[0, 76],
	[1, 74],
	[2, 85],
	[3, 83],
	[3.5, 81],
	[4.25, 81]],

	####
	[[0, 76],
	[1, 75],
	[2, 72],
	[3, 68],
	[3.5, 72],
	[4.25, 71]],

	[[0, 76],
	[1, 76],
	[2, 82],
	[3, 80],
	[3.5, 80],
	[4.25, 83]],

	[[0, 76],
	[1, 75],
	[2, 70],
	[3, 72],
	[3.5, 73],
	[4.25, 66]],

	[[0, 76],
	[1, 76],
	[2, 80],
	[3, 80],
	[3.5, 79],
	[4.25, 84]]
])

down = np.array([
	[[0, 76],
	[1, 74],
	[2, 74],
	[3, 72],
	[3.5, 72],
	[4.25, 72]],

	[[0, 76],
	[1, 73],
	[2, 69],
	[3, 73],
	[3.5, 72],
	[4.25, 71]],
	
	[[0, 76],
	[1, 71],
	[2, 73],
	[3, 74],
	[3.5, 67],
	[4.25, 64]],

	####
	[[0, 76],
	[1, 75],
	[2, 72],
	[3, 68],
	[3.5, 72],
	[4.25, 71]],

	[[0, 76],
	[1, 75],
	[2, 70],
	[3, 72],
	[3.5, 73],
	[4.25, 66]],
])

up = np.array([
	[[0, 76],
	[1, 82],
	[2, 80],
	[3, 80],
	[3.5, 83],
	[4.25, 83]],

	[[0, 76],
	[1, 80],
	[2, 80],
	[3, 79],
	[3.5, 84],
	[4.25, 83]],

	[[0, 76],
	[1, 74],
	[2, 85],
	[3, 83],
	[3.5, 81],
	[4.25, 81]],

	####

	[[0, 76],
	[1, 76],
	[2, 82],
	[3, 80],
	[3.5, 80],
	[4.25, 83]],

	[[0, 76],
	[1, 76],
	[2, 80],
	[3, 80],
	[3.5, 79],
	[4.25, 84]]
])

#print(all_data[0:2])
graphPitchContour(all_data, as_pitch_space_contour=False)

'''
look at other ones that are six notes long.
'''

if __name__ == '__main__':
	import doctest
	doctest.testmod()


