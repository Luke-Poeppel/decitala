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

from music21 import converter
from music21 import stream

from decitala import Decitala, get_added_values

def decitala_from_string(tala_string):
	"""
	Sqlite3 databases store this info in string form. 

	>>> decitala_from_string('<decitala.Decitala 51_Vijaya>')
	<decitala.Decitala 51_Vijaya>
	"""
	new_str = tala_string.split()[1][:-1]
	return Decitala(new_str)

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

class SubPath(object):
	"""
	Object for storing information about a subpath in a given database. Keeps track of the path onsets, 
	the decitalas within it, and calculates relevant information (e.g. gap_score). Under the right 
	conditions, Subpaths compose a full Path object (defined below).
	
	TODO: ABILITY TO COMBINE SUBPATHS! 

	NOTE: the individual paths in a sqlite table are 1-indexed. 

	>>> haikai_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_0.db'
	>>> p1 = SubPath(db_path=haikai_database_path, table='Paths_2', path_num=6)
	>>> p1
	<SubPath_6: [(38.125, 40.0), (40.0, 41.75), (41.75, 45.75), (45.75, 47.625), (47.625, 48.875), (49.375, 56.875)]>
	>>> p1.path
	[(38.125, 40.0), (40.0, 41.75), (41.75, 45.75), (45.75, 47.625), (47.625, 48.875), (49.375, 56.875)]

	>>> p1.is_end_overlapping
	False
	>>> 
	>>> p1.total_duration
	18.25
	>>> p1.gaps()
	[0.0, 0.0, 0.0, 0.0, 0.5]
	>>> p1.total_gaps
	0.5
	>>> p1.decitalas
	[<decitala.Decitala 77_Gajajhampa>, <decitala.Decitala 53_Sama>, <decitala.Decitala 51_Vijaya>, <decitala.Decitala 77_Gajajhampa>, <decitala.Decitala 76_Jhampa>, <decitala.Decitala 8_Simhavikrama>]
	
	>>> p1.nPVI()
	[53.333333, 9.52381, 40.0, 53.333333, 14.285714, 41.111111]
	>>> p1.average_nPVI()
	35.26455

	Gap score returns the proportion of the 
	>>> p1.gap_score()
	97.33333333333333


	Using the preference rules.
	p1.score()
	51.26984
	"""
	def __init__(self, db_path, table, path_num, **kwargs):
		assert path_num > 0

		self.db_path = db_path
		self.table = table
		self.path_num = path_num

		conn = lite.connect(self.db_path)
		cur = conn.cursor()

		path_string = "SELECT * FROM {}".format(table)
		cur.execute(path_string)
		rows = cur.fetchall()

		#really stupid, but this is the only thing working right now.
		#not sure how to fetch by column name; really stupid. 
		all_pitch_data = []
		for this_row in rows:
			for this_elem in this_row:
				if this_elem[0:2] == '((':
					all_pitch_data.append(literal_eval(this_elem))
		
		lengths = []
		for x in all_pitch_data:
			count = 0
			for this_range in x:
				count += len(this_range)
			lengths.append(count)
		
		self.all_num_onset_data = sorted(lengths)

		all_averages = []
		for this_row in rows:
			each_tala_num_onsets = []
			for this_elem in this_row:
				if this_elem[0:2] == '((':
					pitch_content = literal_eval(this_elem)
					for this in pitch_content:
						each_tala_num_onsets.append(len(this))
			all_averages.append(round(np.mean(each_tala_num_onsets), 6))

		self.all_averages = sorted(all_averages)

		path = []
		pitch_data = []
		all_pitch_data = []
		for i, this_row in enumerate(rows):
			############ get onset data
			for this_elem in this_row:
				if this_elem[0:2] == '((':
					all_pitch_data.append(literal_eval(this_elem))
			if self.path_num == (i + 1):
				######### GET DATA
				stop_index = 0
				for this_elem in this_row:
					if this_elem == 'NULL':
						stop_index = this_row.index(this_elem)
						break
					elif this_elem[0:2] == '((':
						stop_index = this_row.index(this_elem)

				for this_elem in this_row[0:stop_index]:
					path.append(literal_eval(this_elem))

				pitch_data = literal_eval(this_row[-1])
				##########
				break
			else:
				pass
		
		self.path = path
		self.pitch_data = pitch_data

		#get tala data
		fragment_path_string = "SELECT * FROM Fragment"
		cur.execute(fragment_path_string)
		rows = cur.fetchall()

		#all_average_num_onsets = []
		decitalas = []
		for this_range in self.path:
			for this_row in rows:
				#tala = this_row[2]
				#as_real_tala = decitala_from_string(tala)

				# get list that holds the average num onset for each row. 
				if this_range[0] == this_row[0] and this_range[1] == this_row[1]:
					decitalas.append(this_row[2])
		
		self.decitalas = [decitala_from_string(string) for string in decitalas]
		#self.all_average_num_onsets = all_average_num_onsets

	def __repr__(self):
		return '<SubPath_{0}: {1}>'.format(str(self.path_num), str(self.path))

	def gaps(self):
		gaps = []
		i = 0
		while i < len(self.path) - 1:
			curr_range = self.path[i]
			next_range = self.path[i + 1]
			gaps.append(next_range[0] - curr_range[-1])
			i += 1

		return gaps

	@property
	def start_onset(self):
		return self.path[0][0]
	
	@property
	def end_onset(self):
		return self.path[-1][-1]
	
	@property
	def total_gaps(self):
		return sum(self.gaps())

	@property
	def is_end_overlapping(self):
		return sum(self.gaps()) == 0

	@property
	def total_duration(self):
		total_duration = 0
		i = 0
		while i < len(self.path):
			curr_range = self.path[i]
			total_duration += curr_range[1] - curr_range[0]
			i += 1
		
		return total_duration

	@property
	def num_onsets(self):
		count = 0
		for x in self.pitch_data:
			count += len(x)
		return count

	def nPVI(self):
		nPVI_vals = []
		for this_tala in self.decitalas:
			nPVI_vals.append(this_tala.nPVI())
		
		return nPVI_vals
		
	def average_nPVI(self):
		return round(np.mean(self.nPVI()), 6)

	def average_num_onsets(self):
		return np.mean([x.num_onsets for x in self.decitalas])

	def all_pitch_content(self):
		flattened = lambda l: [item for sublist in l for item in sublist]
		return flattened(self.pitch_data)

	###################### Individual Scores ######################
	def gap_score(self):
		initial_val = self.path[0][0]
		end_val = self.path[-1][-1]
		total_range = end_val - initial_val

		percentage_gap = (self.total_gaps / total_range) * 100
		
		return (100 - percentage_gap)

	def non_retrogradable_score(self):
		"""
		TODO: figure out why tala.is_non_retrogradable() is behaving strangely here.
		"""
		num_non_retrogradable = 0
		for this_tala in self.decitalas:
			if np.array_equal(this_tala.ql_array(), this_tala.ql_array(retrograde = True)):
				num_non_retrogradable += 1
		
		return (num_non_retrogradable / len(self.path)) * 100

	def recycling_score(self):
		"""
		Proportion of decitalas in a path that repeat.

		TODO: Counter works now, fix!
		"""
		names = []
		for this_tala in self.decitalas:
			names.append(this_tala.name)

		#print(Counter(names))
		total = 0
		for x in Counter(names):
			if Counter(names)[x] > 1:
				total += Counter(names)[x]

		return (total / len(self.decitalas)) * 100
	
	def average_num_onsets_per_tala_score(self):
		"""
		Gets the percentile of a path by the average num_onsets for the talas within it.
		Want: average num onsets for all talas in the table. 
		"""
		all_data = [len(tala.ql_array()) for tala in self.decitalas]
		avg = round(np.mean(all_data), 6) #added round -- seems to fix the problem...

		return stats.percentileofscore(self.all_averages, avg)#, avg)

	def num_onsets_score(self):
		"""
		This is actually pretty cool! :-) 
		Method: get a list that is simply the sorted total number of onsets (from pitch content)
		for each path. Use stats.percentileofscore(data, this_path.total_num_onsets)
		"""
		return stats.percentileofscore(self.all_num_onset_data, self.num_onsets())
	
	###################### Visualization ######################
	def show(self):
		"""
		TODO
		"""
		raise NotImplementedError

	def annotate_score(self, score_path, part):
		"""
		Annotates a given score (matching the score on which the database has been created)
		with the Path data. 
		"""
		raise NotImplementedError

####################################################################################################
# models
def model2(x, weights):
	"""
	Two constrains: gap_size and onset_percentile.
	(Input is Path object.)
	Try different percentages.
	"""
	sums = []
	constraints = [x.gap_score(), x.num_onsets_score()]
	for w, constraint in zip(weights, constraints):
		sums.append(w * constraint)
	
	return round(sum(sums), 6)

def model3(x, weights):
	"""
	Two constrains: gap_size and average_onset
	"""
	sums = []
	constraints = [x.gap_score(), x.average_num_onsets_per_tala_score()]
	for w, constraint in zip(weights, constraints):
		sums.append(w * constraint)
	
	return round(sum(sums), 6)

'''
def sort_table_by_model3_score(db_path, path_table_num, weights):
	conn = lite.connect(db_path)
	cur = conn.cursor()
	path_string = "SELECT * FROM Paths_{}".format(str(path_table_num))
	cur.execute(path_string)
	rows = cur.fetchall()

	paths = []
	for i in range(1, number_of_paths_by_table(db_path, path_table_num) + 1):        
		path = SubPath(table = 'Paths_{}'.format(str(path_table_num)), path_num = i, db_path = db_path)
		paths.append(path)
	
	return sorted(paths, key = lambda x: model3(x, weights), reverse=True)

def model3_highest_score(db_path, path_table_num, weights):
	return sort_table_by_model3_score(db_path, path_table_num, weights)[0]

def get_full_model3_path(db_path, weights):
	continuous_paths = []
	for i in range(0, number_of_tables(db_path)):
		curr_path = []
		for j in range(1, number_of_paths_by_table(db_path, i) + 1):
			p = SubPath(db_path, 'Paths_{}'.format(str(i)), j)
			curr_path.append(p)
		
		sorted_paths = sorted(curr_path, key = lambda x: model3(x, weights), reverse=True)

		continuous_paths.append(sorted_paths[0])

	return continuous_paths

def path_gap_score(db_path, path_table_num, curr_path_num):
	curr_path = SubPath(db_path, 'Paths_{}'.format(str(path_table_num)), curr_path_num)
	if path_table_num == 0:
		return model3(curr_path, [0.7, 0.3])
	else:
		prev_path = model3_highest_score(db_path, path_table_num - 1, [0.7, 0.3])
		gap = curr_path.start_onset - prev_path.end_onset
		total_range = curr_path.end_onset - prev_path.start_onset

		path_gap_score = 100 - ((gap / total_range) * 100)
		return path_gap_score

def sort_by_path_gap_score(db_path, path_table_num):
	all_paths = []
	for i in range(0, number_of_paths_by_table('Paths_{}'.format(str(path_table_num)), path_table_num)):
		all_paths.append(SubPath(db_path, 'Paths_{}'.format(str(path_table_num))))

	return sorted(all_paths, key = lambda x: path_gap_score(db_path, path_table_num, x.path_num))

class Path(object):
	"""
	A Path object is composed of several SubPath objects. 
	"""
	def __init__(self, paths=[]):
		self.paths = paths

	def tala_counter(self):
		"""
		Returns a Counter of all the talas found in the path.
		"""
		raise NotImplementedError
'''

####################################################################################################
haikai0_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_0.db'
haikai1_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_1.db'

liturgie3_database_path = '/Users/lukepoeppel/decitala_v2/liturgie_3.db'
liturgie4_database_path = '/Users/lukepoeppel/decitala_v2/liturgie_4.db'

livre_dorgue_0_path = '/Users/lukepoeppel/decitala_v2/livre_dorgue_0.db'
livre_dorgue_1_path = '/Users/lukepoeppel/decitala_v2/livre_dorgue_1.db'

#print(path_gap_score(haikai0_database_path, 2, 1))

# it's slow because it's recalculating the highest score each time. 
#for i in range(1, 16):
	#print(path_gap_score(haikai0_database_path, 2, i))

'''
#print(path_gap_score(haikai0_database_path, 2, 5))
for x in sort_by_path_gap_score(haikai0_database_path, 2):
	print(x)
	print()
'''
'''
for x in sort_table_by_model3_score(livre_dorgue_0_path, path_table_num=2):
	print(x)
	print(x.decitalas)
	print(model3(x, [0.9, 0.1]))
	print()
'''


'''
full = get_full_model3_path(livre_dorgue_0_path, weights = [0.7, 0.3])
for x in full:
	print(x)
	print(x.decitalas)
	print()
'''
'''
num onsets is not the problem
print([len(tala.ql_array()) for tala in correct.decitalas]) is not the problem...
'''

'''
correct = SubPath(haikai0_database_path, 'Paths_3', 4)
print('CORRECT')
print(correct.decitalas)
#print(correct.decitalas)
#print([len(tala.ql_array()) for tala in correct.decitalas])
#print(correct.num_onsets)
print(correct.gap_score())
print(correct.average_num_onsets_per_tala_score())
print('')

print('NOT CORRECT')
print(full[-1].decitalas)
#print([len(tala.ql_array()) for tala in full[-1].decitalas])
#print(full[-1].num_onsets)
print(full[-1].gap_score())
print(full[-1].average_num_onsets_per_tala_score())
'''

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
	def setUp(self):
		warnings.simplefilter('ignore', category=ImportWarning)

	def test_all_num_paths_in_table(self):
		all_found_info = get_all_paths_info('/Users/lukepoeppel/decitala_v2/livre_dorgue_0.db')
		all_num_paths = [x[1] for x in all_found_info]

		real = [24, 46, 24, 12, 10, 128, 10, 108, 92, 24, 12, 4]

		self.assertEqual(all_num_paths, real)
	
if __name__ == '__main__':
	import doctest
	doctest.testmod()
	unittest.main()




