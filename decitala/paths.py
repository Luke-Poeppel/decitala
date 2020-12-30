# -*- coding: utf-8 -*-
####################################################################################################
# File:     paths.py
# Purpose:  Extraction and analysis of path data. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
Tools for analyzing the data extracted in :obj:`~decitala.database.create_database`.
"""
import numpy as np
import os
import re
import sqlite3 as lite 
import unittest

from ast import literal_eval
from collections import Counter
from scipy import stats

from music21 import (
	chord,
	converter,
	note,
	stream
)

from decitala.fragment import (
	Decitala,
	GreekFoot
)

############### EXCEPTIONS ###############
class PathsException(Exception):
	pass

class SubPath(object):
	"""
	Object for storing information about a subpath in a given database. Keeps track of the path onsets, 
	the decitalas within it, and calculates relevant information (e.g. `gap_score`). Under the right 
	conditions, :obj:`~decitala.paths.SubPath`s compose a full :obj:`decitala.paths.Path` object. 

	:param str db_path: path leading to .db file (made from :obj:`~decitala.database.create_database`).
	:param int table_num: path table number (denoted `Path_i` in the file).
	:param int path_num: path number (enumerated by row in the file).
	:raises `~decitala.paths.PathsException`: when an invalid table/path are provided. 

	>>> livre_dorgue_0_path = "/Users/lukepoeppel/decitala/databases/livre_dorgue_0_new.db"
	>>> sub_path = SubPath(db_path=livre_dorgue_0_path, table_num=17, path_num=11)
	>>> sub_path
	<paths.SubPath_11: [(151.125, 153.125), (153.125, 154.375), (154.375, 161.375)]>
	>>> sub_path.path
	[(151.125, 153.125), (153.125, 154.375), (154.375, 161.375)]
	>>> for region_pitches in sub_path.pitch_data:
	... 	print(region_pitches)
	((44,), (63,))
	((76,), (82,), (89,))
	((78,), (69,), (75,), (64,), (71,), (82,), (56,), (59,), (61,), (50,), (43,), (68,), (71,), (67,), (64,), (58,))
	>>> for fragment in sub_path.fragments:
	... 	print(fragment.name, fragment.ql_array())
	97_Utsava [0.5 1.5]
	76_Jhampa [0.375 0.375 0.5  ]
	15_Caccari [0.25  0.375 0.25  0.375 0.25  0.375 0.25  0.375 0.25  0.375 0.25  0.375
	 0.25  0.375 0.25  0.375]
	>>> sub_path.num_onsets
	21
	>>> sub_path.start_onset
	151.125
	>>> sub_path.end_onset
	161.375
	>>> sub_path.gaps()
	[0.0, 0.0]
	>>> sub_path.total_gaps()
	0.0
	>>> # SubPath.played_total_duration() only returns the total duration of sounded tones, i.e. ignores silent periods. 
	>>> sub_path.played_total_duration()
	10.25
	>>> # SubPath.total_range() is the played_total_duration() + total_gaps()
	>>> sub_path.total_range()
	10.25
	>>> sub_path.is_end_overlapping()
	True
	>>> # SubPath.gap_score() returns the percentage of total_range() that is continous, i.e. without gaps. 
	>>> sub_path.gap_score()
	100.0
	>>> sub_path.non_retrogradable_score()
	0.0
	>>> sub_path.recycling_score()
	0.0
	>>> # SubPath.average_num_onsets_per_tala_score() tracks the average number of onsets in a path
	# and scores it's percentile in the context of the table.
	>>> # sub_path.average_num_onsets_per_tala_score()
	# 15.76086956521739
	"""
	def __init__(self, db_path, table_num, path_num, **kwargs):
		assert os.path.isfile(db_path), PathsException("The database path provided is invalid.")

		self.db_path = db_path
		self.table_num = table_num
		self.path_num = path_num

		conn = lite.connect(self.db_path)
		cur = conn.cursor()

		path_string = "SELECT * FROM Paths_{}".format(str(table_num))
		cur.execute(path_string)
		rows = cur.fetchall()

		path = []
		pitch_data = []
		all_averages = []
		for i, this_row in enumerate(rows):
			each_tala_num_onsets = []
			for this_data in this_row:
				if this_data[0:3] == "(((":
					evaluated = literal_eval(this_data)
					pitch_data.append(evaluated)
					for this_eval in evaluated:
						each_tala_num_onsets.append(len(this_eval))

			if self.path_num == (i + 1):
				stop_index = 0
				for this_data in this_row:
					if this_data == "NULL":
						stop_index = this_row.index(this_data)
						break
					elif this_data[0:3] == "(((":
						stop_index = this_row.index(this_data)

				for this_data in this_row[0:stop_index]:
					evaluated = literal_eval(this_data)
					path.append(evaluated)

				pitch_data = literal_eval(this_row[-1])
				break
			else:
				pass

			all_averages.append(np.mean(each_tala_num_onsets))
			
		self.path = path
		self.pitch_data = pitch_data
		self.all_averages = all_averages

		fragment_path_string = "SELECT * FROM Fragments"
		cur.execute(fragment_path_string)
		fragment_rows = cur.fetchall()
		fragments = []
		for this_range in self.path:
			for this_row in fragment_rows:
				if this_range[0] == this_row[0] and this_range[1] == this_row[1]:
					fragment_str = this_row[2]
					fragment_name = fragment_str.split()[-1][:-1] # Remove the final `>`.
					fragment_abbrev = fragment_str[10:12]
					if fragment_abbrev == "De": # Decitala
						fragments.append(Decitala(fragment_name))
					elif fragment_abbrev == "Gr": # GreekFoot
						fragments.append(GreekFoot(fragment_name))

		self.fragments = fragments

	def __repr__(self):
		return '<paths.SubPath_{0}: {1}>'.format(str(self.path_num), str(self.path))

	@property
	def start_onset(self):
		"""
		:return: the starting onset of the path.
		:rtype: float
		"""
		return self.path[0][0]
	
	@property
	def end_onset(self):
		"""
		:return: the ending onset of the path.
		:rtype: float
		"""
		return self.path[-1][-1]

	@property
	def num_onsets(self):
		"""
		:return: the total number of onsets in the path,
		:rtype: int
		"""
		count = 0
		for tala_pitches in self.pitch_data:
			for pitches in tala_pitches:
				count += 1
		return count

	def gaps(self):
		"""
		:return: list holding the onset gap between the fragments.
		:rtype: list
		"""
		gaps = []
		i = 0
		while i < len(self.path) - 1:
			curr_range = self.path[i]
			next_range = self.path[i + 1]
			gaps.append(next_range[0] - curr_range[-1])
			i += 1

		return gaps

	def total_gaps(self):
		"""
		:return: sum of all gaps between the fragments.
		:rtype: float
		"""
		return sum(self.gaps())

	def played_total_duration(self):
		"""
		:return: total played duration of the subpath (i.e. overall onset range minus total gaps.)
		:rtype: float
		"""
		total_duration = 0
		i = 0
		while i < len(self.path):
			curr_range = self.path[i]
			total_duration += curr_range[1] - curr_range[0]
			i += 1
		
		return total_duration

	def total_range(self):
		"""
		:return: overall range of the subpath.
		:rtype: float
		"""
		return self.path[-1][-1] - self.path[0][0]
	
	def is_end_overlapping(self):
		"""
		:return: whether or not all onset ranges in the subpath are end-overlapping. 
		:rtype: bool
		"""
		return sum(self.gaps()) == 0

	def gap_score(self):
		"""
		"""
		percentage_gap = (self.total_gaps() / self.total_range()) * 100
		return (100 - percentage_gap)

	def non_retrogradable_score(self):
		"""
		:return: proportion of the fragments in the subpath that are non-retrogradable.
		:rtype: float
		"""
		num_non_retrogradable = 0
		for this_fragment in self.fragments:
			if this_fragment.is_non_retrogradable:
				num_non_retrogradable += 1
			
		return (num_non_retrogradable / len(self.fragments)) * 100

	def recycling_score(self):
		"""
		:return: proportion of the fragments in the subpath that are recycled.
		:rtype: float
		"""
		recycled = 0
		counted = Counter(self.fragments)
		for key in counted.keys():
			if counted[key] > 1:
				recycled += counted[key]
		
		return (recycled / len(self.fragments)) * 100
	
	def average_num_onsets_per_tala_score(self):
		"""
		:rtype: float
		"""
		num_onsets_data = [this_fragment.num_onsets for this_fragment in self.fragments]
		avg_num_onsets = round(np.mean(num_onsets_data), 6)

		return stats.percentileofscore(self.all_averages, avg_num_onsets)

	# Comparison
	def inter_gap_score(self, other):
		"""
		Takes two :obj:`~decitala.paths.SubPath` objects and returns the path gap score, i.e. 
		proportion of the gap between them to the total range. 

		:param `~decitala.paths.SubPath` other: other subpath to compare to.
		:return: proportion of the gap between the two subpaths w.r.t. the total range.
		:rtype: float
		"""
		assert type(other.__name__) == "SubPath"
		if other.start_onset < self.end_onset:
			raise PathsException("The start of the second SubPath overlaps with the end of this SubPath.")
		
		gap = other.start_onset - self.end_onset
		total_range = other.end_onset - self.start_onset

		percentage = (gap / total_range) * 100
		return 100 - percentage

class Path(object):
	"""Concatenation of multiple :obj:`~decitala.paths.SubPath` objects."""
	def __init__(self, subpaths = []):
		self.subpaths = subpaths
		self.subpath_nums = [subpath.path_num for subpath in self.subpaths]

		data = []
		for subpath in self.subpaths:
			for onset_range, fragment, pitch_content in zip(subpath.path, subpath.fragments, subpath.pitch_data):
				data.append([onset_range, fragment, pitch_content])
			
		self.data = data
		self.fragments = [data[1] for data in self.data]
	
	def __repr__(self):
		return '<Paths_' + '/'.join(str(x) for x in self.subpath_nums) + '>'
	
	def fragment_counter(self):
		"""
		:return: Counter of the fragment data.
		:rtype: collections.Counter.
		"""
		return Counter(self.fragments)

	def annotate_score(self, filepath, part_num):
		"""
		Annotates the part of a given score with the fragment/onset data. 
		"""
		full = converter.parse(filepath)
		inst = full.parts[part_num]

		for this_obj in inst.recurse().iter.notes:
			for this_data in self.data:
				onset_range = this_data[0]
				fragment = this_data[1]
				if this_obj.offset == onset_range[0]:
					this_obj.lyric = fragment.name
					this_obj.style.color = "green"
				elif this_obj.offset == onset_range[-1]:
					this_obj.style.color = "red"

		full.show()

####################################################################################################
# MODEL
def get_all_paths_data(db_path):
	"""
	:param str db_path: path to database file (made in :obj:`decitala.database.create_database`).
	:return: lists of the form ``[[a, n], [b, m], ...]`` where 
			``a`` is the path number on the table and ``n`` is the number of paths in that table. 
	:rtype: list
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

def model(db_path, weights=[]):
	all_info = get_all_paths_data(db_path)
	conn = lite.connect(db_path)

	subpaths = []
	i = 0
	while i < len(all_info):
		curr_info = all_info[i]
		for j in range(1, curr_info[1] + 1):
			if j == 1:
				subpath = SubPath(db_path = db_path, table_num = curr_info[0], path_num = j)
				subpaths.append(subpath)
			else:
				pass
		i += 1
	
	return Path(subpaths=subpaths)

####################################################################################################

# Model 
def model3(subpath, weights):
	components = []
	parameters = [subpath.gap_score(), subpath.average_num_onsets_per_tala_score()]
	for w, constraint in zip(weights, parameters):
		components.append(w * constraint)
	
	return round(sum(components), 6)



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