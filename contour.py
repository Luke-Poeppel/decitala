# -*- coding: utf-8 -*-
####################################################################################################
# File:     contour.py
# Purpose:  Tools for analyzing & graphing pitch contour in collections of found-talas. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
NOTE:
TODO:
- function that normalizes a sequence of midi tones to the same starting value.
"""
import copy
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from music21 import chord
from music21 import pitch
from music21 import stream

from decitala import Decitala
from paths import (
	SubPath, 
	Path,
	get_full_model3_path
)

FONTNAME = 'Times'
FONTSIZE_TITLE = 14
FONTSIZE_LABEL = 12

####################################################################################################
# Helpers
def pitch_space_contour_from_midi(midi_array, as_str=False):
	"""
	Given an array of midi values, returns the pitch space contour.
	See The Perception of Rhythm in Non-Tonal Music: Rhythmic Contours in the Music of
	Edgard Varèse (Marvin, 1991)

	>>> frag = np.array([60, 65, 68, 72])
	>>> pitch_space_contour_from_midi(midi_array=frag)
	array([0, 1, 2, 3])
	>>> pitch_space_contour_from_midi(midi_array=frag, as_str=True)
	'<0 1 2 3>'
	"""
	dseg_vals = copy.copy(midi_array)
	value_dict = dict()

	for i, this_val in zip(range(0, len(sorted(set(dseg_vals)))), sorted(set(dseg_vals))):
		value_dict[this_val] = str(i)

	for i, this_val in enumerate(dseg_vals):
		for this_key in value_dict:
			if this_val == this_key:
				dseg_vals[i] = value_dict[this_key]

	if not(as_str):
		return np.array([int(val) for val in dseg_vals])
	else:
		return '<' + ' '.join([str(int(val)) for val in dseg_vals]) + '>'

def normalize_pitch_content(data, midi_start):
	"""
	Given an array of midi content, returns the same material transposed according to the midi_start
	value (i.e. intervals are maintained)

	>>> frag = np.array([61, 65, 68, 60, 51])
	>>> normalize_pitch_content(frag, 42)
	array([42, 46, 49, 41, 32])
	"""
	diff = data[0] - midi_start	
	return np.array([x - diff for x in data])

def uds_contour(data):
	"""
	Stands for "up-down-stay" as a measure of pitch contour. Normalized to start at 0. 

	>>> frag = np.array([47, 42, 45, 51, 51, 61, 58])
	>>> uds_contour(frag)
	array([ 0, -1,  1,  1,  0,  1, -1])
	"""
	out = [0]
	i = 1
	while i < len(data):
		prev = data[i - 1]
		curr = data[i]

		if curr > prev:
			out.append(1)
		if curr < prev:
			out.append(-1)
		if curr == prev:
			out.append(0)

		i += 1
	
	return np.array(out)

def single_tuples_to_array(data):
	"""
	>>> frag = ((62,), (25,), (52,), (31,))
	>>> single_tuples_to_array(frag)
	array([62, 25, 52, 31])
	"""
	flattened = lambda l: [item for sublist in l for item in sublist]
	return np.array(flattened(data))

def format_pitch_data(data):
	"""
	The data format for pitch content in Paths is somewhat messy. This makes it easier to use.
	"""
	pass

def cosine_similarity(vector_a, vector_b):
	numerator = np.dot(vector_a, vector_b)
	denominator = np.linalg.norm(vector_a) * np.linalg.norm(vector_b)
	return (numerator / denominator)

####################################################################################################
# Graphers

def plot_uds(data):
	mpl.style.use('seaborn')
	pitches = [x[2] for x in data] 

	print(pitches)

	'''
	plt.yticks([-1, 0, 1])
	for info in pitches:
		top_line = [y[-1] for y in info]
		uds = uds_contour(top_line)
		if uds[1] == -1:
			plt.plot(np.array(uds))

	plt.show()
	'''

def plot_normalized_pitches(data, use_highest_line = False):
	mpl.style.use('seaborn')
	tala = data[0][1]
	pitch_data = [x[2] for x in data]

	# get median start point

	if use_highest_line:
		new_data = []
		for this_data in pitch_data:
			this = []
			for this_pitch_content in this_data:
				if len(this_pitch_content) > 1:
					this.append(this_pitch_content[-1])
			new_data.append(this)

	normalized_data = [normalize_pitch_content(x, 72) for x in new_data]

	for x in normalized_data:
		plt.plot(x)
	
	plt.show()

####################################################################################################
# Testing
haikai0_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_0.db'
haikai1_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_1.db'

liturgie3_database_path = '/Users/lukepoeppel/decitala_v2/liturgie_3.db'
liturgie4_database_path = '/Users/lukepoeppel/decitala_v2/liturgie_4.db'

livre_dorgue_0_path = '/Users/lukepoeppel/decitala_v2/livre_dorgue_0.db'
livre_dorgue_1_path = '/Users/lukepoeppel/decitala_v2/livre_dorgue_1.db'


#subpaths = get_full_model3_path(livre_dorgue_0_path)
#path = Path(subpaths)

#x = path.filter_by_tala(Decitala('Rangapradipaka'))
#print(x)

rangapradipaka_livre = [
	[(24.5, 30.75), Decitala('Rangapradipaka'), ((69,), (65,), (58,), (79,), (60,))], 
	[(35.5, 41.125), Decitala('Rangapradipaka'), ((60,), (76,), (86,), (83,), (74,))], 
	[(56.625, 61.625), Decitala('Rangapradipaka'), ((68,), (77,), (67,), (61,), (75,))], 
	[(70.625, 75.0), Decitala('Rangapradipaka'), ((87,), (77,), (73,), (64,), (48,))], 
	[(89.5, 93.25), Decitala('Rangapradipaka'), ((77,), (80,), (72,), (74,), (76,))], 
	[(95.0, 98.125), Decitala('Rangapradipaka'), ((67,), (69,), (67,), (65,), (71,))], 
	[(111.125, 114.25), Decitala('Rangapradipaka'), ((80,), (71,), (58,), (64,), (73,))], 
	[(116.0, 119.75), Decitala('Rangapradipaka'), ((69,), (77,), (86,), (78,), (80,))], 
	[(134.25, 138.625), Decitala('Rangapradipaka'), ((72,), (81,), (73,), (64,), (68,))], 
	[(147.625, 152.625), Decitala('Rangapradipaka'), ((79,), (71,), (66,), (57,), (44,))], 
	[(168.125, 173.75), Decitala('Rangapradipaka'), ((79,), (61,), (71,), (68,), (66,))], 
	[(178.5, 184.75), Decitala('Rangapradipaka'), ((61,), (80,), (66,), (77,), (75,))], 
	[(189.5, 195.125), Decitala('Rangapradipaka'), ((78,), (86,), (69,), (77,), (66,))], 
	[(210.625, 215.625), Decitala('Rangapradipaka'), ((71,), (68,), (63,), (77,), (73,))],
	[(224.625, 229.0), Decitala('Rangapradipaka'), ((55,), (58,), (42,), (65,), (63,))]
]

#for x in rangapradipaka_livre:
print(Decitala('Rangapradipaka').ql_array())	


'''
pitches = [y[2] for y in x]
for data in pitches:
	new = single_tuples_to_array(data)
	plt.plot(normalize_pitch_content(new, 60), '-o', markersize=4)

plt.show()
'''
#plot_normalized_pitches(x, use_highest_line = True)

if __name__ == '__main__':
	import doctest
	doctest.testmod()


