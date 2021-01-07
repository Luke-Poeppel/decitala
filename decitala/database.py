# -*- coding: utf-8 -*-
####################################################################################################
# File:     database.py
# Purpose:  Data structure for creating and representing databases using sqlite. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020 / Frankfurt, DE 2020
####################################################################################################
"""
Tools for creating sqlite3 databases of extracted rhythmic data from Messiaen's music.  
"""
import numpy as np
import os
import pandas as pd
import sqlite3 as lite
import timeout_decorator
import uuid

from ast import literal_eval
from scipy import stats

from music21 import converter
from music21 import stream

from .fragment import (
	GeneralFragment,
	Decitala,
	GreekFoot
)
from .utils import (
	get_object_indices,
	successive_ratio_array,
	filter_single_anga_class_fragments,
	filter_sub_fragments,
	pitch_content_to_contour,
	contour_to_prime_contour
)
from .trees import (
	FragmentTree,
	rolling_search,
	filter_data
)
from .pofp import (
	get_break_points,
	partition_data_by_break_points,
	get_pareto_optimal_longest_paths
)

import logging
logging.basicConfig(level=logging.INFO)

__all__ = [
	"create_database",
	"DBParser"
]

# Fragments
here = os.path.abspath(os.path.dirname(__file__))
decitala_path = os.path.dirname(here) + "/Fragments/Decitalas"
greek_path = os.path.dirname(here) + "/Fragments/Greek_Metrics/XML"

############### EXCEPTIONS ###############
class DatabaseException(Exception):
	pass

@timeout_decorator.timeout(75)
def create_database(
		db_path,
		filepath,
		part_num,
		# Search parameters
		frag_types=["decitala"],
		rep_types=["ratio", "difference"],
		allowed_modifications=[
			"r", 
			"rr", 
			"d", 
			"rd", 
			"sr",
			"rsr"
		],
		try_contiguous_summation=True,
		windows=list(range(1, 20)),
		allow_unnamed=False,
		# Filtering parameters. 
		filter_found_single_anga_class=True,
		filter_found_sub_fragments=True,
		keep_grace_notes=True,
		verbose=True
	):
	"""
	This function generates an sqlite3 database for storing extracted rhythmic data from :obj:`decitala.trees.rolling_search`.
	The database holds has one page for storing all extracted fragments, their onsets/offsets of occurrence, and their 
	modification data. 

	**NOTE**: I suggest setting ``filter_sub_fragments=True`` for compositions and ``filter_sub_fragments=False`` for birdsong transcriptions. 

	:param str db_path: path where the .db file will be written. 
	:param str filepath: path to score.
	:param bool filter_single_anga_class: whether or not to remove single-anga class fragments from the data in rolling_search. 
	:param bool verbose: whether or not to log information about the database creation process (including data from rolling search). 
	
	:return: sqlite3 database
	:rtype: .db file
	"""
	assert os.path.isfile(filepath), DatabaseException("The path provided is not a valid file.")
	if os.path.isfile(db_path):
		logging.info("That database already exists ✔")
		return

	if not(verbose):
		logging.disable(logging.INFO)
	
	filename = filepath.split('/')[-1]

	logging.info("Preparing database...")
	logging.info("\n")
	logging.info("File: {}".format(filename))
	logging.info("Part: {}".format(part_num))
	logging.info("Fragment types: {}".format(frag_types))
	logging.info("Representation types: {}".format(rep_types))
	logging.info("Modifications: {}".format(allowed_modifications))
	logging.info("Try contiguous summations: {}".format(try_contiguous_summation))
	logging.info("Filter single anga class fragments: {}".format(filter_found_single_anga_class))
	logging.info("Filter sub fragments: {}".format(filter_found_sub_fragments))
	# logging.info("Keep grace notes: {}".format(keep_grace_notes))

	ALL_DATA = []
	for this_frag_type in frag_types:
		logging.info("\n")
		logging.info("Making fragment tree(s) (and searching) for frag_type: {}".format(this_frag_type))

		if "ratio" in rep_types:
			curr_ratio_tree = FragmentTree(frag_type=this_frag_type, rep_type="ratio")
		else:
			curr_ratio_tree = None
		
		if "difference" in rep_types:
			curr_difference_tree = FragmentTree(frag_type=this_frag_type, rep_type="difference")
		else:
			curr_difference_tree = None

		data = rolling_search(
			filepath,
			part_num,
			curr_ratio_tree,
			curr_difference_tree,
			allowed_modifications,
			try_contiguous_summation,
			windows,
			allow_unnamed,
			verbose
		)

		ALL_DATA.extend(data)

	initial_length = len(ALL_DATA)
	logging.info("\n")
	logging.info("{} fragments extracted".format(initial_length))

	# logging.info("Removing cross-corpus duplicates...")
	
	############ Filters ############
	if filter_found_single_anga_class:
		ALL_DATA = filter_single_anga_class_fragments(ALL_DATA)

		logging.info("Removing all single anga class fragments...")
		logging.info("Removed {0} fragments ({1} remaining)".format(initial_length - len(ALL_DATA), len(ALL_DATA)))
	
	new_length = len(ALL_DATA)

	if filter_found_sub_fragments:
		ALL_DATA = filter_sub_fragments(ALL_DATA)
		logging.info("Removing all sub fragments...")
		logging.info("Removed {0} fragments ({1} remaining)".format(new_length - len(ALL_DATA), len(ALL_DATA)))
	#################################

	logging.info("Calculated break points: {}".format(get_break_points(ALL_DATA)))

	all_object = get_object_indices(filepath, part_num)
	sorted_onset_ranges = sorted(ALL_DATA, key = lambda x: x["onset_range"][0])
	partitioned_data = partition_data_by_break_points(sorted_onset_ranges)

	conn = lite.connect(db_path)
	with conn:
		logging.info("\n")
		logging.info("Connected to database at: {}".format(db_path))

		cur = conn.cursor()
		
		###### Creating Fragments Table ######
		fragment_table_string = "CREATE TABLE Fragments (Onset_Start REAL, Onset_Stop REAL, Fragment BLOB, Mod TEXT, Factor REAL, Pitch_Content BLOB, Pitch_Contour BLOB, Prime_Contour BLOB, Is_Slurred INT)"
		cur.execute(fragment_table_string)
		for this_fragment in sorted_onset_ranges:
			contour = list(pitch_content_to_contour(this_fragment["pitch_content"]))
			prime_contour = list(contour_to_prime_contour(contour, include_depth=False))
			fragment_insertion_string = "INSERT INTO Fragments VALUES({0}, {1}, '{2}', '{3}', {4}, '{5}', '{6}', '{7}', {8})".format(this_fragment["onset_range"][0], # start offset
																												this_fragment["onset_range"][1], # end offset
																												this_fragment["fragment"].name, # fragment
																												this_fragment["mod"][0], # mod type 
																												this_fragment["mod"][1], # mod factor/difference
																												this_fragment["pitch_content"], # pitch content
																												contour, # pitch contour 
																												prime_contour, # prime contour
																												int(this_fragment["is_spanned_by_slur"])) # is_slurred
			cur.execute(fragment_insertion_string)

		###### Creating Paths Table ######
		for i, this_partition in enumerate(partitioned_data):			
			pareto_optimal_paths = get_pareto_optimal_longest_paths(this_partition)
			longest_path = max([len(path) for path in pareto_optimal_paths])

			columns = ["Onset_Range_{}".format(i) for i in range(1, longest_path + 1)]
			columns_declaration = ", ".join("%s INTEGER" % c for c in columns)

			cur.execute("CREATE TABLE Paths_{0} ({1})".format(str(i+1), columns_declaration))
			logging.info("Making Paths_{} table".format(i+1))
			
			FRAGMENT_TABLE_STRING = "SELECT * FROM Fragments"
			cur.execute(FRAGMENT_TABLE_STRING)
			fragment_rows = cur.fetchall()
			for path in pareto_optimal_paths:
				fragment_row_ids = []
				for this_fragment_data in path:
					data = this_fragment_data[0]
					for j, this_row in enumerate(fragment_rows):
						if (this_row[2] == data["fragment"].name) and (this_row[0] == data["onset_range"][0]) and (this_row[1] == data["onset_range"][1]):
							fragment_row_ids.append(j + 1)

				if len(path) == longest_path:
					longest_paths_insertion_string = "INSERT INTO Paths_{0} VALUES({1})".format(str(i+1), ", ".join([str(x) for x in fragment_row_ids]))
					cur.execute(longest_paths_insertion_string)
				else:
					diff = longest_path - len(path)
					nulls = ["'NULL'"] * diff
					formatted_nuls = ", ".join(nulls)
					shorter_paths_insertion_string = "INSERT INTO Paths_{0} VALUES({1}, {2})".format(str(i+1), ", ".join([str(x) for x in fragment_row_ids]), formatted_nuls)
					cur.execute(shorter_paths_insertion_string)
		
		logging.info("Done preparing ✔")

####################################################################################################
class DBParser:
	"""
	Class used for parsing the database made in :obj:`~decitala.database.create_database`.

	>>> example_data = "/Users/lukepoeppel/decitala/tests/static/ex99_data.db"
	>>> parsed = DBParser(example_data)
	>>> parsed
	<database.DBParser ex99_data.db>
	>>> for spanned_fragment in parsed.spanned_fragments():
	... 	print(spanned_fragment["fragment"])
	<fragment.GreekFoot Iamb>
	<fragment.GreekFoot Iamb>
	<fragment.GreekFoot Iamb>
	<fragment.GreekFoot Iamb>
	<fragment.GreekFoot Iamb>
	<fragment.GreekFoot Iamb>
	>>> parsed.num_rows_in_table("Fragments")
	33
	>>> parsed.num_path_tables()
	1
	>>> parsed.get_subpath(1, 121)
	[1, 10, 19, 24, 29, 33]
	>>> for x in parsed.subpath_data(1, 121):
	... 	print(x)
	{'db_row_index': 1, 'fragment': <fragment.GreekFoot Peon_IV>, 'onset_range': (0.125, 0.75), 'mod': 'r', 'factor': 0.125, 'pitch_content': [(83,), (83,), (83,), (82,)], 'is_slurred': False}
	{'db_row_index': 10, 'fragment': <fragment.GreekFoot Amphibrach>, 'onset_range': (0.75, 1.25), 'mod': 'r', 'factor': 0.125, 'pitch_content': [(80,), (82,), (79,)], 'is_slurred': False}
	{'db_row_index': 19, 'fragment': <fragment.GreekFoot Iamb>, 'onset_range': (1.5, 1.875), 'mod': 'r', 'factor': 0.125, 'pitch_content': [(78,), (80,)], 'is_slurred': True}
	{'db_row_index': 24, 'fragment': <fragment.GreekFoot Iamb>, 'onset_range': (1.875, 2.25), 'mod': 'r', 'factor': 0.125, 'pitch_content': [(77,), (79,)], 'is_slurred': True}
	{'db_row_index': 29, 'fragment': <fragment.GreekFoot Iamb>, 'onset_range': (2.25, 2.625), 'mod': 'r', 'factor': 0.125, 'pitch_content': [(77,), (79,)], 'is_slurred': True}
	{'db_row_index': 33, 'fragment': <fragment.GreekFoot Iamb>, 'onset_range': (2.625, 3.0), 'mod': 'r', 'factor': 0.125, 'pitch_content': [(77,), (79,)], 'is_slurred': True}
	>>> parsed.table_onsets_percentile(1)[0:5]
	[2.2857142857142856, 2.5, 2.3333333333333335, 2.5, 2.5]
	>>> parsed.get_subpath_onset_percentile(1, 121)
	40.63241106719368
	>>> parsed.get_subpath_gap_score(1, 121)
	90.47619047619048
	>>> parsed.get_subpath_model(1, 121)
	75.52305665349144
	"""
	def __init__(self, db_path):
		assert os.path.isfile(db_path), DatabaseException("You've provided an invalid file.")

		filename = db_path.split('/')[-1]
		conn = lite.connect(db_path)
		cur = conn.cursor()

		self.db_path = db_path
		self.filename = filename
		self.conn = conn

		fragment_path_string = "SELECT * FROM Fragments"
		cur.execute(fragment_path_string)
		fragment_rows = cur.fetchall()
		
		fragment_data = []
		for i, this_row in enumerate(fragment_rows):
			row_data = dict()

			fragment_str = this_row[2]
			if fragment_str[0].isdigit():
				this_fragment = Decitala(fragment_str)
			else:
				this_fragment = GreekFoot(fragment_str)

			row_data["db_row_index"] = i+1
			row_data["fragment"] = this_fragment
			row_data["onset_range"] = (this_row[0], this_row[1])
			row_data["mod"] = this_row[3]
			row_data["factor"] = this_row[4]
			row_data["pitch_content"] = literal_eval(this_row[5])
			row_data["is_slurred"] = bool(int(this_row[8]))
			
			fragment_data.append(row_data)

		self.fragment_data = fragment_data

	def __repr__(self):
		return "<database.DBParser {}>".format(self.filename)
	
	@property
	def fragments(self):
		return [x["fragment"] for x in self.fragment_data]

	def spanned_fragments(self):
		return [x for x in self.fragment_data if x["is_slurred"]==True]

	def show_fragments_table(self):
		"""Displays the Fragments table of the db."""
		data = pd.read_sql_query("SELECT * FROM Fragments", self.conn)
		return data
	
	def show_spanned_fragments(self):
		"""Displays a subset (spanned fragments) of the Fragments table of the db."""
		data = pd.read_sql_query("SELECT * FROM Fragments WHERE Is_Slurred = 1", self.conn)
		return data

	def show_path_table(self, table_num):
		"""Displays Path number i."""
		data = pd.read_sql_query("SELECT * FROM Paths_{}".format(table_num), self.conn)
		return data

	def show_path(self, table_num, path_num):
		QUERY_STRING = "SELECT * FROM Paths_{0} WHERE rowid = {1}".format(table_num, path_num)
		data = pd.read_sql_query(QUERY_STRING, self.conn)

		return data

	def num_rows_in_table(self, table):
		"""Returns the number of rows in a given table."""
		QUERY_STRING = "SELECT COUNT(*) FROM {}".format(table)
		data = pd.read_sql_query(QUERY_STRING, self.conn)
		num_rows = data["COUNT(*)"].iloc[0]
		return num_rows

	######## Paths Metadata ########
	def num_path_tables(self):
		"""Returns the number of Path tables in the db."""
		QUERY_STRING = "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'"
		data = pd.read_sql_query(QUERY_STRING, self.conn)
		num_path_tables = data["COUNT(*)"].iloc[0] - 1

		return num_path_tables

	######## Paths Individual ########
	def get_subpath(self, table_num, path_num):
		QUERY_STRING = "SELECT * FROM Paths_{0} WHERE rowid = {1}".format(table_num, path_num)
		data = pd.read_sql_query(QUERY_STRING, self.conn)
		as_ints = data.stack().tolist()
		
		return [x for x in as_ints if x != "NULL"]

	def subpath_data(self, table_num, path_num):
		subpath_data = self.get_subpath(table_num, path_num)
		
		fragment_data = []
		for this_row_id in subpath_data:
			for this_data in self.fragment_data:
				if this_data["db_row_index"] == this_row_id:
					fragment_data.append(this_data)

		return fragment_data
	
	def table_onsets_percentile(self, table_num):
		num_rows = self.num_rows_in_table("Paths_{}".format(table_num))
		averages = []
		for i in range(1, num_rows+1):
			subpath_fragments = [x["fragment"].num_onsets for x in self.subpath_data(table_num, i)]
			averages.append(np.mean(subpath_fragments))
		
		return averages
		
	def get_subpath_onset_percentile(self, table_num, path_num):
		subpath_data = self.subpath_data(table_num, path_num)
		subpath_average_onsets = np.mean([x["fragment"].num_onsets for x in subpath_data])
		percentile = stats.percentileofscore(self.table_onsets_percentile(table_num), subpath_average_onsets)

		return percentile

	def get_subpath_gap_score(self, table_num, path_num):
		gaps = []
		total_range = []
		subpath_data = self.subpath_data(table_num, path_num)
		
		# just use np.diff?
		i = 0
		while i < len(subpath_data) - 1:
			curr_data = subpath_data[i]
			next_data= subpath_data[i + 1]
			
			gap = next_data["onset_range"][0] - curr_data["onset_range"][1]
			gaps.append(gap)
			total_range.append(curr_data["onset_range"][1] - curr_data["onset_range"][0])
			if i == len(subpath_data) - 2:
				total_range.append(next_data["onset_range"][1] - next_data["onset_range"][0])
			i += 1
		
		gaps = sum(gaps)
		total_range = sum(total_range)

		if len(subpath_data) == 1:
			percentage_gap_pre = 0
		else:
			percentage_gap_pre = (gaps / total_range) * 100
		
		percentage_gap = 100.0 - percentage_gap_pre
		return percentage_gap

	def get_subpath_model(self, table_num, path_num, weights=[0.7, 0.3]):
		"""Returns the value of the model for a given subpath."""
		gap_score = self.get_subpath_gap_score(table_num, path_num)
		onset_score = self.get_subpath_onset_percentile(table_num, path_num)
		scores = [gap_score, onset_score]

		model = 0
		for weight, score in zip(weights, scores):
			model += weight * score
		
		return model

	def get_highest_modeled_subpath(self, table_num):
		num_rows = self.num_rows_in_table("Paths_{}".format(table_num))
		highest_subpath = None
		highest_model_val = 0
		for i in range(1, num_rows + 1):
			model_val = self.get_subpath_model(table_num, i)
			print(model_val)
			if model_val > highest_model_val:
				model_val = highest_model_val
				highest_subpath = i

		return self.subpath_data(table_num, highest_subpath)