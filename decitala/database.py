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
Tools for creating SQLite databases of extracted rhythmic data from Messiaen's music.  
"""
import numpy as np
import os
import pandas as pd
import sqlite3
import timeout_decorator
import timeit
import uuid

from ast import literal_eval
from itertools import groupby
from progress.bar import Bar
from progress.spinner import Spinner
from scipy import stats

from music21 import converter
from music21 import note
from music21 import stream

from .fragment import (
	GeneralFragment,
	Decitala,
	GreekFoot
)
from .utils import (
	get_object_indices,
	successive_ratio_array,
	successive_difference_array,
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
	"DBParser",
	"create_fragment_database"
]

# Fragments
here = os.path.abspath(os.path.dirname(__file__))
decitala_path = os.path.dirname(here) + "/Fragments/Decitalas"
greek_path = os.path.dirname(here) + "/Fragments/Greek_Metrics/XML"

############### EXCEPTIONS ###############
class DatabaseException(Exception):
	pass

def remove_cross_corpus_duplicates(data):
	"""
	>>> fake_data = [
	... 	{'fragment': GreekFoot("Spondee"), 'mod': ('r', 0.125), 'onset_range': (0.0, 0.5), 'is_spanned_by_slur': False, 'pitch_content': [(80,), (91,)], "id":1},
	... 	{'fragment': GeneralFragment([0.25, 0.25], name="cs-test1"), 'mod': ('cs', 2.0), 'onset_range': (0.0, 0.5), 'is_spanned_by_slur': False, 'pitch_content': [(80,), (91,)], "id":2},
	... 	{'fragment': GreekFoot("Trochee"), 'mod': ('r', 0.125), 'onset_range': (0.25, 0.625), 'is_spanned_by_slur': False, 'pitch_content': [(91,), (78,)], "id":3},
	... 	{'fragment': GeneralFragment([0.25, 0.125], name="cs-test2"), 'mod': ('cs', 2.0), 'onset_range': (0.25, 0.625), 'is_spanned_by_slur': False, 'pitch_content': [(80,), (91,)], "id":4},
	... 	{'fragment': GreekFoot("Dactyl"), 'mod': ('r', 0.125), 'onset_range': (0.5, 1.0), 'is_spanned_by_slur': False, 'pitch_content': [(91,), (78,), (85,)], "id":5},
	... 	{'fragment': Decitala("Pratitala"), 'mod': ('d', 2.0), 'onset_range': (0.5, 1.0), 'is_spanned_by_slur' : False, 'pitch_content': [(91,), (78,), (85,)], "id":6}
	... ]
	>>> for x in remove_cross_corpus_duplicates(fake_data):
	... 	print(x)
	"""
	onset_keyfunc = lambda x: x["onset_range"]
	onset_range_partition = [list(x) for k, x in groupby(data, key=onset_keyfunc)]

	data_out = []
	for partition in onset_range_partition:
		if len(partition) == 1:
			data_out.extend(partition)
		else:
			pass
			# segregate cs from non-cs

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

	conn = sqlite3.connect(db_path)
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
					combined = [str(x) for x in fragment_row_ids] + nulls					
					shorter_paths_values_string = ", ".join(combined)

					shorter_paths_insertion_string = "INSERT INTO Paths_{0} VALUES({1})".format(str(i+1), shorter_paths_values_string)
					cur.execute(shorter_paths_insertion_string)
		
		logging.info("Done preparing ✔")

####################################################################################################
# Helper functions
def _num_subpath_tables(conn):
	"""
	Returns the number of Path tables in a database db.

	>>> example_data = "/Users/lukepoeppel/decitala/tests/static/ex99_data.db"
	>>> conn = sqlite3.connect(example_data)
	>>> _num_subpath_tables(conn)
	1
	"""
	QUERY_STRING = "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'"
	data = pd.read_sql_query(QUERY_STRING, conn)
	num_path_tables = data["COUNT(*)"].iloc[0] - 1

	return num_path_tables

def _num_rows_in_table(table, conn):
	"""
	Returns the number of rows in a given table.
	
	>>> example_data = "/Users/lukepoeppel/decitala/tests/static/ex99_data.db"
	>>> conn = sqlite3.connect(example_data)
	>>> _num_rows_in_table("Paths_1", conn)
	1265
	"""
	QUERY_STRING = "SELECT COUNT(*) FROM {}".format(table)
	data = pd.read_sql_query(QUERY_STRING, conn)
	num_rows = data["COUNT(*)"].iloc[0]
	
	return num_rows

class DBParser:
	"""
	Class used for parsing the database made in :obj:`~decitala.database.create_database`.

	>>> example_data = "/Users/lukepoeppel/decitala/tests/static/ex99_data.db"
	>>> parsed = DBParser(example_data)
	>>> parsed
	<database.DBParser ex99_data.db>
	>>> parsed.num_subpath_tables
	1
	"""
	def __init__(self, db_path):
		assert os.path.isfile(db_path), DatabaseException("You've provided an invalid file.")

		filename = db_path.split('/')[-1]
		conn = sqlite3.connect(db_path)
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

		self.num_subpath_tables = _num_subpath_tables(self.conn)
		metadata = []
		for i in range(1, self.num_subpath_tables + 1):
			num_rows = _num_rows_in_table("Paths_{}".format(i), self.conn)
			onset_data = self.table_onsets_percentile(i)
			metadata.append([i, num_rows, onset_data])

		self.metadata = metadata

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
		num_rows = _num_rows_in_table("Paths_{}".format(table_num), self.conn)
		averages = []
		for i in range(1, num_rows+1):
			subpath_fragments = [x["fragment"].num_onsets for x in self.subpath_data(table_num, i)]
			averages.append(np.mean(subpath_fragments))
		
		return averages
		
	def get_subpath_onset_percentile(self, table_num, path_num):
		subpath_data = self.subpath_data(table_num, path_num)
		subpath_average_onsets = np.mean([x["fragment"].num_onsets for x in subpath_data])
		
		onset_data = [x[1] for x in self.metadata if x[0] == table_num]
		percentile = stats.percentileofscore(onset_data, subpath_average_onsets)

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
		num_rows = _num_rows_in_table("Paths_{}".format(table_num), self.conn)
		highest_subpath = None
		highest_model_val = 0
		for i in range(1, num_rows + 1):
			model_val = self.get_subpath_model(table_num, i)
			if model_val > highest_model_val:
				model_val = highest_model_val
				highest_subpath = i

		return self.subpath_data(table_num, highest_subpath)

####################################################################################################
# Fragment Databases
"""The following function is used to create the databases for fragment querying."""
# Helpers
def get_initial_data(path, size, log_msg):
	"""Reads the initial data from the input directory."""
	initial_data = []
	with Bar(log_msg, max=size) as bar:
		for this_file in os.listdir(path):
			filename = this_file[:-4]
			converted = converter.parse("/".join([path, this_file]))
			ql_array = [this_note.quarterLength for this_note in converted.flat.getElementsByClass(note.Note)]
			
			frag_dict = dict()
			frag_dict["name"] = filename
			frag_dict["ql_array"] = ql_array
			frag_dict["r_equivalents"] = []
			frag_dict["r_keep"] = 100
			frag_dict["d_equivalents"] = []
			frag_dict["d_keep"] = 100
			
			initial_data.append(frag_dict)
			bar.next()
	return initial_data

def track_rd_equivalents(dataset_a, dataset_b, dataset_b_frag_type):
	i = 0
	while i < len(dataset_a):
		curr_fragment = dataset_a[i]
		curr_ql_array = curr_fragment["ql_array"]
		curr_rarray = successive_ratio_array(curr_ql_array)
		curr_darray = successive_difference_array(curr_ql_array)
		j = 0
		while j < len(dataset_b):
			if i == j:
				pass # i.e. skip curr step. 
			else:
				other_fragment = dataset_b[j]
				other_ql_array = other_fragment["ql_array"]
				other_rarray = successive_ratio_array(other_ql_array)
				other_darray = successive_difference_array(other_ql_array)
				
				if np.array_equal(curr_rarray, other_rarray):
					curr_fragment["r_equivalents"].append((dataset_b_frag_type, other_fragment["name"]))
				if np.array_equal(curr_darray, other_darray):
					curr_fragment["d_equivalents"].append((dataset_b_frag_type, other_fragment["name"]))	
			j += 1
		i += 1

	return dataset_a

def track_keep_vals(data, size, frag_type):
	i = 0
	while i < size:
		curr_frag_data = data[i]
		r_equivalent_fragments = [x[1] for x in curr_frag_data["r_equivalents"] if x[0] == frag_type]
		d_equivalent_fragments = [x[1] for x in curr_frag_data["d_equivalents"] if x[0] == frag_type]

		if curr_frag_data["r_keep"] == 100:
			curr_frag_data["r_keep"] = 1
			if not(r_equivalent_fragments):
				pass
			else:
				for this_fragment in r_equivalent_fragments:
					for this_other_fragment in data:
						if this_other_fragment["name"] == this_fragment:
							this_other_fragment["r_keep"] = 0
		else:
			pass

		if curr_frag_data["d_keep"] == 100:
			curr_frag_data["d_keep"] = 1
			if not(d_equivalent_fragments):
				pass
			else:
				for this_fragment in d_equivalent_fragments:
					for this_other_fragment in data:
						if this_other_fragment["name"] == this_fragment:
							this_other_fragment["d_keep"] = 0
		else:
			pass

		i += 1

	return data

def make_table(data, table_name, conn):
	"""Function for creating a fragments table in the connected SQL database."""
	table_string = "CREATE TABLE {} (Name BLOB, QL_Array BLOB, R_Equivalents BLOB, D_Equivalents BLOB, R_Keep INT, D_Keep INT)".format(table_name)
	conn.cursor().execute(table_string)

	with Bar("Making {} Table...".format(table_name), max=len(data)) as bar:
		for this_fragment_data in data:
			name = this_fragment_data["name"]
			ql_array = this_fragment_data["ql_array"]
			r_equivalents = this_fragment_data["r_equivalents"]
			d_equivalents = this_fragment_data["d_equivalents"]
			r_keep = this_fragment_data["r_keep"]
			d_keep = this_fragment_data["d_keep"]

			fragment_insertion_string = "INSERT INTO {0} VALUES('{1}', ?, ?, ?, ?, ?)".format(table_name, name)
			conn.cursor().execute(fragment_insertion_string, (str(ql_array), str(r_equivalents), str(d_equivalents), r_keep, d_keep))
			bar.next()

def create_fragment_database(verbose=True):
	"""Dataset counts: 130 Decitalas, 26 Greek Metrics."""
	db_path = os.path.dirname(here) + "/databases/fragment_database.db"
	
	decitala_initial_data = get_initial_data(path=decitala_path, size=130, log_msg="Getting initial decitala data...")	
	greek_metric_initial_data = get_initial_data(path=greek_path, size=26, log_msg="Getting initial greek metric data...")

	logging.info("Tracking intra-level decitala equivalents...")
	decitala_intra_equivalents = track_rd_equivalents(
		dataset_a=decitala_initial_data, 
		dataset_b=decitala_initial_data, 
		dataset_b_frag_type="decitala"
	)
	logging.info("Tracking cross-corpus decitala equivalents...")
	decitala_cross_equivalents = track_rd_equivalents(
		dataset_a=decitala_intra_equivalents, 
		dataset_b=greek_metric_initial_data, 
		dataset_b_frag_type="greek_foot"
	)

	logging.info("Getting keep/ignore decitala data...")
	final_decitala_data = track_keep_vals(data=decitala_cross_equivalents, size=130, frag_type="decitala")

	###############################################################################################
	logging.info("Tracking intra-level greek metric equivalents...")
	greek_intra_equivalents = track_rd_equivalents(
		dataset_a=greek_metric_initial_data, 
		dataset_b=greek_metric_initial_data, 
		dataset_b_frag_type="greek_foot"
	)	
	logging.info("Tracking cross-corpus greek metric equivalents...")
	greek_cross_equivalents = track_rd_equivalents(
		dataset_a=greek_intra_equivalents, 
		dataset_b=decitala_initial_data, 
		dataset_b_frag_type="decitala"
	)

	logging.info("Getting keep/ignore greek metric data...")
	final_greek_data = track_keep_vals(data=greek_cross_equivalents, size=26, frag_type="greek_foot")

	logging.info("Creating the fragments tables...")
	conn = sqlite3.connect(db_path)
	
	make_table(data=final_decitala_data, table_name="Decitalas", conn=conn)
	make_table(data=final_greek_data, table_name="Greek_Metrics", conn=conn)
	
	logging.info("Done preparing ✔")
	conn.commit()