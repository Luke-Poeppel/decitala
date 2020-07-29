# -*- coding: utf-8 -*-
####################################################################################################
# File:     paths.py
# Purpose:  Data structure for handling paths from sqlite database. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
Stores data for each pareto optimal path.
"""
import numpy as np
import sqlite3 as lite 
import unittest
import warnings

from ast import literal_eval
from collections import Counter
from scipy import stats

from music21 import chord
from music21 import converter
from music21 import note
from music21 import stream

from decitala import Decitala, get_added_values

def get_all_paths_info(db_path):
	"""
	Returns all the path info
	"""
	conn = lite.connect(db_path)
	cur = conn.cursor()
	execute = cur.execute("SELECT * FROM sqlite_master where type='table'")

	all_tables_info = []
	for table in execute.fetchall():
		table_info = []
		if table[1][0:4] in 'Paths':
			paths_table_num = table[1].split('_')[-1]
			path_string = "SELECT * FROM Paths_{}".format(str(paths_table_num))
			cur.execute(path_string)
			count = 0
			rows = cur.fetchall()
			for row in rows:
				count += 1
			
			table_info.append(int(table[1].split('_')[-1]))
			table_info.append(count)

		if table_info:
			all_tables_info.append(table_info)

	return all_tables_info

####################################################################################################
# SubPath(s) and Path(s)

class SubPath(object):
	"""
	Object for storing information about a subpath in a given database. Keeps track of the path onsets, 
	the decitalas within it, and calculates relevant information (e.g. gap_score). Under the right 
	conditions, Subpaths compose a full Path object (defined below).

	NOTE: the individual paths in a sqlite table are 1-indexed. 

	TODO: __add__() method for subpaths (this is a bit more complicated...)

	>>> livre_dorgue0_path = '/Users/lukepoeppel/decitala_v2/livre_dorgue_0.db'
	>>> sp = SubPath(db_path=livre_dorgue0_path, table_num=8, path_num=62)
	>>> sp
	<SubPath_62: [(181.0, 184.75), (184.875, 185.875), (186.375, 187.375), (187.375, 188.25), (188.75, 191.75), (191.75, 195.125)]>
	>>> sp.path
	[(181.0, 184.75), (184.875, 185.875), (186.375, 187.375), (187.375, 188.25), (188.75, 191.75), (191.75, 195.125)]
	>>> for x in sp.pitch_data:
	...     print(x)
	((66,), (77,), (75,))
	((60,), (68,), (71,), (82,), (75,))
	((74,), (79,), (64,), (70,), (81,))
	((75,), (61,), (72,))
	((80,), (67,), (78,), (86,))
	((69,), (77,), (66,))
	>>> for tala in sp.decitalas:
	...     print(tala.name, tala.ql_array())
	21_Tribhinna [0.5 1.  1.5]
	46_Jayacri [1.  0.5 1.  0.5 1. ]
	46_Jayacri [1.  0.5 1.  0.5 1. ]
	118_Rajamartanda [1.   0.5  0.25]
	65_B_Kankala_Khanda [0.25 0.25 1.   1.  ]
	21_Tribhinna [0.5 1.  1.5]

	>>> sp.num_onsets
	23
	>>> sp.start_onset
	181.0
	>>> sp.end_onset
	195.125

	>>> sp.gaps()
	[0.125, 0.5, 0.0, 0.5, 0.0]
	>>> sp.total_gaps()
	1.125

	SubPath().played_total_duration() only returns the total duration of sounded tones, i.e., 
	ignores silent periods. 
	>>> sp.played_total_duration()
	13.0
	
	So, SubPath().total_range() is the played_total_duration() + total_gaps()
	>>> sp.total_range()
	14.125
	>>> sp.is_end_overlapping()
	False

	SubPath().gap_score() returns the percentage of total_range() that is continous, that is, without
	gaps. 
	>>> sp.gap_score()
	92.035398
	>>> sp.non_retrogradable_score()
	33.333333
	>>> sp.recycling_score()
	66.666667

	SubPath().average_num_onsets_per_tala_score() tracks the average number of onsets in a path
	and scores it's percentile in the context of the table.
	>>> sp.average_num_onsets_per_tala_score()
	15.76086956521739
	"""
	def __init__(self, db_path, table_num, path_num, **kwargs):
		assert path_num > 0

		self.db_path = db_path
		self.table_num = table_num
		self.path_num = path_num

		conn = lite.connect(self.db_path)
		cur = conn.cursor()

		path_string = "SELECT * FROM Paths_{}".format(str(table_num))
		cur.execute(path_string)
		rows = cur.fetchall()

		# separate loop, for now. 
		all_averages = []
		for this_row in rows:
			each_tala_num_onsets = []
			for this_data in this_row:
				if this_data[0:3] == '(((':
					evaluated = literal_eval(this_data)
					for this in evaluated:
						each_tala_num_onsets.append(len(this))

			all_averages.append(round(np.mean(each_tala_num_onsets), 6))
		
		self.all_averages = all_averages

		path = []
		pitch_data = []
		for i, this_row in enumerate(rows):
			for this_data in this_row:
				if this_data[0:3] == '(((':
					evaluated = literal_eval(this_data)
					pitch_data.append(evaluated)

			if self.path_num == (i + 1):
				stop_index = 0
				for this_data in this_row:
					if this_data == 'NULL':
						stop_index = this_row.index(this_data)
						break
					elif this_data[0:3] == '(((':
						stop_index = this_row.index(this_data)

				for this_data in this_row[0:stop_index]:
					evaluated = literal_eval(this_data)
					path.append(evaluated)

				pitch_data = literal_eval(this_row[-1])
				break
			else:
				pass
			
		self.path = path
		self.pitch_data = pitch_data

		# Get tala information. (More efficient to do it separately.)
		decitalas = []
		fragment_path_string = "SELECT * FROM Fragment"
		cur.execute(fragment_path_string)
		rows = cur.fetchall()

		for this_range in self.path:
			for this_row in rows:
				if this_range[0] == this_row[0] and this_range[1] == this_row[1]:
					decitalas.append(this_row[2])

		self.decitalas = [Decitala(string) for string in decitalas]

	def __repr__(self):
		return '<SubPath_{0}: {1}>'.format(str(self.path_num), str(self.path))

	@property
	def start_onset(self):
		return self.path[0][0]
	
	@property
	def end_onset(self):
		return self.path[-1][-1]

	@property
	def num_onsets(self):
		count = 0
		for tala_pitches in self.pitch_data:
			for pitches in tala_pitches:
				count += 1
		return count

	def gaps(self):
		gaps = []
		i = 0
		while i < len(self.path) - 1:
			curr_range = self.path[i]
			next_range = self.path[i + 1]
			gaps.append(next_range[0] - curr_range[-1])
			i += 1

		return gaps

	def total_gaps(self):
		return sum(self.gaps())

	def played_total_duration(self):
		total_duration = 0
		i = 0
		while i < len(self.path):
			curr_range = self.path[i]
			total_duration += curr_range[1] - curr_range[0]
			i += 1
		
		return total_duration

	def total_range(self):
		return self.path[-1][-1] - self.path[0][0]
	
	def is_end_overlapping(self):
		return sum(self.gaps()) == 0

	#################### Individual Scores ####################
	def gap_score(self):
		percentage_gap = (self.total_gaps() / self.total_range()) * 100
		return round((100 - percentage_gap), 6)

	def non_retrogradable_score(self):
		num_non_retrogradable = 0
		for this_tala in self.decitalas:
			if this_tala.is_non_retrogradable:
				num_non_retrogradable += 1
			
		return round((num_non_retrogradable / len(self.decitalas)) * 100, 6)

	def recycling_score(self):
		recycled = 0
		counted = Counter(self.decitalas)
		for x in counted.keys():
			if counted[x] > 1:
				recycled += counted[x]
		
		return round((recycled / len(self.decitalas)) * 100, 6)
	
	def average_num_onsets_per_tala_score(self):
		num_onsets_data = [tala.num_onsets for tala in self.decitalas]
		avg_num_onsets = round(np.mean(num_onsets_data), 6)

		return stats.percentileofscore(self.all_averages, avg_num_onsets)

	###################### Visualization ######################
	def show(self):
		"""
		Shows the series of talas with the pitch information normalized to start at onset 0.0. 
		"""
		'''
		first_onset = self.start_onset
		normalized_path = []
		for onset_range in self.path:
			normalized_path.append([onset_range[0] - first_onset, onset_range[1] - first_onset])
		
		#hmmm... we need the tala onsets.
		zipped = []
		for onset_range, pitch_info in zip(normalized_path, self.pitch_data):
			print(onset_range, pitch_info)
		'''
		raise NotImplementedError

	def annotate_score(self, score_path, part):
		"""
		Annotates a given score (matching the score on which the database has been created) 
		with the SubPath data. 
		"""
		raise NotImplementedError

####################################################################################################
# Model 
def model3(subpath, weights):
	components = []
	parameters = [subpath.gap_score(), subpath.average_num_onsets_per_tala_score()]
	for w, constraint in zip(weights, parameters):
		components.append(w * constraint)
	
	return round(sum(components), 6)

def subpath_gap_score(subpath1, subpath2):
	"""
	Takes two SubPath objects and returns the PathGapScore
	"""
	path1_start_onset = subpath1.start_onset
	path1_end_onset = subpath1.end_onset

	path2_start_onset = subpath2.start_onset
	path2_end_onset = subpath2.end_onset

	if path2_start_onset < path1_end_onset:
		raise Exception('Invalid Path Comparison.')
	
	gap = path2_start_onset - path1_end_onset
	total_range = path2_end_onset - path1_start_onset

	percentage = (gap / total_range) * 100
	return round(100 - percentage, 6)

def get_full_model3_path(db_path, first_path_weights = [0.7, 0.3], rest_weights = [0.7, 0.1], path_gap_weight = 0.2):
	all_info = get_all_paths_info(db_path)
	conn = lite.connect(db_path)

	subpaths = []
	i = 0
	while i < len(all_info):
		curr_info = all_info[i]
		if i == 0:
			model_3_scores = []
			for j in range(1, curr_info[1] + 1):
				path = SubPath(db_path = db_path, table_num = curr_info[0], path_num = j)
				model_3_scores.append([path, model3(path, first_path_weights)])
			
			model_3_scores.sort(key = lambda x: x[1], reverse = True)
			best_path = model_3_scores[0][0]
			subpaths.append(best_path)
			i += 1
		else:
			gap_scores = []
			for j in range(1, curr_info[1] + 1):
				path = SubPath(db_path = db_path, table_num = curr_info[0], path_num = j)
				gap_scores.append([path, subpath_gap_score(subpaths[-1], path)])

			new_model_scores = []
			for this_path in gap_scores:
				model4 = model3(this_path[0], rest_weights)
				model4 += path_gap_weight * this_path[1]
				new_model_scores.append([this_path[0], model4])
			
			new_model_scores.sort(key = lambda x: x[1], reverse = True)
			bestp1 = new_model_scores[0][0]
			subpaths.append(bestp1)
			i += 1

	return subpaths	

####################################################################################################
# Testing
haikai0_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_0.db'
haikai1_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_1.db'

liturgie3_database_path = '/Users/lukepoeppel/decitala_v2/liturgie_3.db'
liturgie4_database_path = '/Users/lukepoeppel/decitala_v2/liturgie_4.db'

livre_dorgue_0_path = '/Users/lukepoeppel/decitala_v2/livre_dorgue_0.db'
livre_dorgue_1_path = '/Users/lukepoeppel/decitala_v2/livre_dorgue_1.db'

#print(get_full_model3_path(haikai0_database_path))
#print(get_full_model3_path(haikai1_database_path))

class Path(object):
	"""
	Concatenation of multiple SubPath objects (under the right conditions).
	"""
	def __init__(self, paths = []):
		self.paths = paths
		path_nums = [path.path_num for path in self.paths]
	
	#def __repr__(self):
		#return '<Pa>'

###############################################################################
# Helper function to ignore annoying warnings 
# source: https://www.neuraldump.net/2017/06/how-to-suppress-python-unittest-warnings/

def ignore_warnings(test_func):
	def do_test(self, *args, **kwargs):
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			test_func(self, *args, **kwargs)
	return do_test

class Test(unittest.TestCase):
	def set_up(self):
		warnings.simplefilter('ignore', category=ImportWarning)

	def test_all_num_paths_in_table(self):
		all_found_info = get_all_paths_info('/Users/lukepoeppel/decitala_v2/livre_dorgue_0.db')
		all_num_paths = [x[1] for x in all_found_info]

		real = [24, 46, 24, 12, 10, 128, 10, 108, 92, 24, 12, 4]

		self.assertEqual(all_num_paths, real)
	
	# Do an easier example so I can check by hand.
	'''
	def test_num_onsets_percetile(self):
		test_path = '/Users/lukepoeppel/decitala_v2/livre_dorgue_0.db'
		all_found_info = get_all_paths_info(test_path)
		percentiles = []
		for i in range(1, all_found_info[1][1] + 1):
			path = SubPath(test_path, 1, i)
			percentiles.append(path.average_num_onsets_per_tala_score())

		real = [0.0, 0.0, 0.0, 0.0, 0.0, 2.272727, 4.444444, 6.0, 7.692308, 12.5, 19.047619, 19.230769, 21.212121, 21.428571, 22.222222, 23.076923, 24.074074, 25.0, 26.666667, 33.333333, 35.416667, 36.363636, 40.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 51.219512, 51.25, 51.351351, 52.857143, 52.941176, 52.941176, 53.225806, 55.0, 55.172414, 62.5, 63.888889, 65.625, 67.105263, 75.0, 75.0, 77.777778, 100.0]
		self.assertEqual(real, percentiles)
	'''

if __name__ == '__main__':
	import doctest
	doctest.testmod()
	unittest.main()




