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
import random
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

	This returns the following: (not evaluated because of random element...)
	{'fragment': <fragment.GreekFoot Spondee>, 'mod': ('r', 0.125), 'onset_range': (0.0, 0.5), 'is_spanned_by_slur': False, 'pitch_content': [(80,), (91,)], 'id': 1}
	{'fragment': <fragment.GeneralFragment cs-test1: [0.25 0.25]>, 'mod': ('cs', 2.0), 'onset_range': (0.0, 0.5), 'is_spanned_by_slur': False, 'pitch_content': [(80,), (91,)], 'id': 2}
	{'fragment': <fragment.GreekFoot Trochee>, 'mod': ('r', 0.125), 'onset_range': (0.25, 0.625), 'is_spanned_by_slur': False, 'pitch_content': [(91,), (78,)], 'id': 3}
	{'fragment': <fragment.GeneralFragment cs-test2: [0.25  0.125]>, 'mod': ('cs', 2.0), 'onset_range': (0.25, 0.625), 'is_spanned_by_slur': False, 'pitch_content': [(80,), (91,)], 'id': 4}
	{'fragment': <fragment.GreekFoot Dactyl>, 'mod': ('r', 0.125), 'onset_range': (0.5, 1.0), 'is_spanned_by_slur': False, 'pitch_content': [(91,), (78,), (85,)], 'id': 5}
	"""
	onset_keyfunc = lambda x: x["onset_range"]
	onset_range_partition = [list(x) for k, x in groupby(data, key=onset_keyfunc)]

	data_out = []
	for partition in onset_range_partition:
		if len(partition) == 1:
			data_out.extend(partition)
		else:
			cs_frags = [x for x in partition if "cs" in x["mod"][0]]
			non_cs_frags = [x for x in partition if "cs" not in x["mod"][0]]
			data_out.append(random.choice(non_cs_frags))
			data_out.extend(cs_frags)

	return data_out

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
	:param int part_num: part number in the score. 
	:param bool filter_single_anga_class: whether or not to remove single-anga class fragments from the data in rolling_search. 
	:param boool filter_found_sub_fragments: whether or not to remove sub-fragments from the dataset. 
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
			curr_ratio_tree = FragmentTree.from_frag_type(frag_type=this_frag_type, rep_type="ratio")
		else:
			curr_ratio_tree = None
		
		if "difference" in rep_types:
			curr_difference_tree = FragmentTree.from_frag_type(frag_type=this_frag_type, rep_type="difference")
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

	logging.info("Removing cross-corpus duplicates...")
	ALL_DATA = remove_cross_corpus_duplicates(ALL_DATA)

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
					data = this_fragment_data
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
	
	>>> example_data = "./tests/static/ex99_data.db"	
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
	
	>>> example_data = "./tests/static/ex99_data.db"
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
	Class used for parsing the SQLite database made in :obj:`~decitala.database.create_database`.

	>>> example_data = "./tests/static/ex99_data.db"
	>>> parsed = DBParser(example_data)
	>>> parsed
	<database.DBParser ex99_data.db>
	>>> for frag in parsed.fragments[0:5]:
	... 	print(frag)
	<fragment.GreekFoot Peon_IV>
	<fragment.GreekFoot Anapest>
	<fragment.GreekFoot Peon_III>
	<fragment.GreekFoot Iamb>
	<fragment.GreekFoot Amphibrach>
	>>> parsed.num_subpath_tables
	1
	>>> parsed.subpath(1, 123)
	[1, 10, 19, 24, 31]
	>>> for data in parsed.subpath_data(1, 123):
	... 	print(data)
	{'db_row_index': 1, 'fragment': <fragment.GreekFoot Peon_IV>, 'onset_range': (0.125, 0.75), 'mod': 'r', 'factor': 0.125, 'pitch_content': [(83,), (83,), (83,), (82,)], 'is_slurred': False}
	{'db_row_index': 10, 'fragment': <fragment.GreekFoot Amphibrach>, 'onset_range': (0.75, 1.25), 'mod': 'r', 'factor': 0.125, 'pitch_content': [(80,), (82,), (79,)], 'is_slurred': False}
	{'db_row_index': 19, 'fragment': <fragment.GreekFoot Iamb>, 'onset_range': (1.5, 1.875), 'mod': 'r', 'factor': 0.125, 'pitch_content': [(78,), (80,)], 'is_slurred': True}
	{'db_row_index': 24, 'fragment': <fragment.GreekFoot Iamb>, 'onset_range': (1.875, 2.25), 'mod': 'r', 'factor': 0.125, 'pitch_content': [(77,), (79,)], 'is_slurred': True}
	{'db_row_index': 31, 'fragment': <fragment.GreekFoot Trochee>, 'onset_range': (2.375, 2.75), 'mod': 'r', 'factor': 0.125, 'pitch_content': [(79,), (77,)], 'is_slurred': False}
	>>> parsed.get_subpath_intra_gap_score(1, 123)
	83.33333333333334
	>>> parsed.get_subpath_model_val(1, 123) # 0.7 * intra-gap-score + 0.3 * onset-percentile
	58.333333333333336
	>>> parsed.get_highest_modeled_initial_subpath(1)
	1265
	>>> parsed.get_subpath_model_val(1, 1265)
	66.3157894736842
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

		earliest_detected_onset = 100

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

			if row_data["onset_range"][0] < earliest_detected_onset:
				earliest_detected_onset = row_data["onset_range"][0]
			
			fragment_data.append(row_data)

		self.fragment_data = fragment_data
		self.earliest_detected_onset = earliest_detected_onset

		self.num_subpath_tables = _num_subpath_tables(self.conn)
		metadata = []
		for i in range(1, self.num_subpath_tables + 1):
			num_rows = _num_rows_in_table("Paths_{}".format(i), self.conn)
			onset_data = self.table_average_onsets_per_fragment_per_subpath(i)
			metadata.append([i, num_rows, onset_data])

		self.metadata = metadata

	def __repr__(self):
		return "<database.DBParser {}>".format(self.filename)

	def fragments(self):
		"""
		:return: list of all extracted fragments in the database. 
		:rtype: list
		"""
		return [x["fragment"] for x in self.fragment_data]

	def slurred_fragments(self):
		"""
		:return: the complete data for the extracted fragments that are slurred.
		:rtype: list
		"""
		return [x for x in self.fragment_data if x["is_slurred"]==True]

	######## Visualization ########
	def show_fragments_table(self):
		"""
		Displays the Fragments table of the database.

		:return: the fragments table (as a dataframe). 
		:rtype: pandas.DataFrame 
		"""
		data = pd.read_sql_query("SELECT * FROM Fragments", self.conn)
		return data
	
	def show_slurred_fragments(self):
		"""
		Displays the slurred fragments in the Fragments table of the database.
		
		:return: the subset of slurred fragments in the fragments table (as a dataframe). 
		:rtype: pandas.DataFrame 
		"""
		data = pd.read_sql_query("SELECT * FROM Fragments WHERE Is_Slurred = 1", self.conn)
		return data

	def show_subpath_table(self, table_num):
		"""
		Displays the queried subpath table. These subpath tables are 1-indexed.
		
		:param int table_num: 1-indexed table number. 
		:return: the queried subpath tale (as a dataframe).
		:rtype: pandas.DataFrame
		"""
		assert table_num >= 1, DatabaseException("The table_num must be >= 1.")
		
		data = pd.read_sql_query("SELECT * FROM Paths_{}".format(table_num), self.conn)
		return data

	def show_subpath(self, table_num, path_num):
		"""
		Displays a queried subpath in one of the tables. 
		
		:param int table_num: 1-indexed table number. 
		:param int path_num: 1-indexed subpath number. 
		:return: the queried subpath table (as a dataframe).
		:rtype: pandas.DataFrame
		"""
		assert (table_num >= 1 and path_num >= 1), DatabaseException("The table_num and path_num must be >= 1.")
		
		QUERY_STRING = "SELECT * FROM Paths_{0} WHERE rowid = {1}".format(table_num, path_num)
		data = pd.read_sql_query(QUERY_STRING, self.conn)
		return data
	
	def show_subpath_data(self, table_num, path_num):
		assert (table_num >= 1 and path_num >= 1), DatabaseException("The table_num and path_num must be >= 1.")

		fragment_row_ids = tuple(str(x) for x in self.subpath(table_num, path_num))
		QUERY_STRING = "SELECT * FROM Fragments WHERE rowid IN {0}".format(fragment_row_ids)
		data = pd.read_sql_query(QUERY_STRING, self.conn)
		return data

	######## Paths Individual ########
	def subpath(self, table_num, path_num):
		"""
		Gets the SQLite rowids for the fragments in a subpath. 
		
		:param int table_num: 1-indexed table number. 
		:param int path_num: 1-indexed subpath number. 
		:return: the rowids (int) for the fragments in a subpath.
		:rtype: list
		"""
		assert (table_num >= 1 and path_num >= 1), DatabaseException("The table_num and path_num must be >= 1.")

		QUERY_STRING = "SELECT * FROM Paths_{0} WHERE rowid = {1}".format(table_num, path_num)
		data = pd.read_sql_query(QUERY_STRING, self.conn)
		as_ints = data.stack().tolist()
		
		return [x for x in as_ints if x != "NULL"]

	def subpath_data(self, table_num, path_num):
		"""
		Gets the full extracted fragment data in a given subpath.
		
		:param int table_num: 1-indexed table number. 
		:param int path_num: 1-indexed subpath number. 
		:return: the complete fragment data for a subpath
		:rtype: list
		"""
		assert (table_num >= 1 and path_num >= 1), DatabaseException("The table_num and path_num must be >= 1.")

		subpath_data = self.subpath(table_num, path_num)
		
		fragment_data = []
		for this_row_id in subpath_data:
			for this_data in self.fragment_data:
				if this_data["db_row_index"] == this_row_id:
					fragment_data.append(this_data)

		return fragment_data
	
	#####################################################################################
	def table_average_onsets_per_fragment_per_subpath(self, table_num):
		"""
		This is a bit hacky: this method is called in the __init__ and returns the average
		number of onsets for each fragment in each subpath of the table. Thus, if a paths
		table has 3 rows, this method returns a list of 3 numbers, each of which corresponds
		to the average number of onsets in a fragment in that subpath. 

		:param int table_num: 1-indexed table number. 
		:return: list (of length equal to the number of rows in the queried ``Paths`` table) 
				holding the average number of onsets (type: float) for a fragment in each subpath. 
		:rtype: list
		"""
		assert table_num >= 1, DatabaseException("The table_num must be >= 1.")
		
		num_rows = _num_rows_in_table("Paths_{}".format(table_num), self.conn)
		averages = []
		for i in range(1, num_rows + 1):
			subpath_fragments = [x["fragment"].num_onsets for x in self.subpath_data(table_num, i)]
			averages.append(np.mean(subpath_fragments))
		
		return averages

	#####################################################################################
	# Modeling
	def subpath_onset_percentile(self, table_num, path_num):
		"""
		Given the data from :obj:`~decitala.database.DBParser.table_average_onsets_per_fragment_per_subpath`, gets the 
		percentile of a given subpath. 

		:param int table_num: 1-indexed table number. 
		:param int path_num: 1-indexed subpath number. 
		:return: percentile (0-100) of a given subpath in the context of its full ``Paths`` table. 
		:rtype: float
		"""
		assert (table_num >= 1 and path_num >= 1), DatabaseException("The table_num and path_num must be >= 1.")
		
		subpath_data = self.subpath_data(table_num, path_num)
		subpath_average_onsets = np.mean([x["fragment"].num_onsets for x in subpath_data])
		
		# NOTE: I call metadata instead of the above function as it then doesn't need to be recalulated. 
		onset_data = [x[1] for x in self.metadata if x[0] == table_num]
		percentile = stats.percentileofscore(onset_data, subpath_average_onsets)

		return percentile

	def first_subpath_start_gap(self, path_num):
		"""
		:param int path_num: 1-indexed subpath number. 
		:return: the proportion of the starting gap (i.e. the empty region from the earliest detected onset in the table
				to the start of the queried subpath) to the total range of the queried subpath in the first table. 
		:rtype: float
		"""
		first_subpath_data = self.subpath_data(table_num=1, path_num=path_num)
		starting_onset = first_subpath_data[0]["onset_range"][0]
		ending_onset = first_subpath_data[-1]["onset_range"][-1]
		total_range = ending_onset - self.earliest_detected_onset

		gap = starting_onset - self.earliest_detected_onset
		gap_proportion = (gap / total_range) * 100

		return 100 - gap_proportion

	def get_subpath_intra_gap_score(self, table_num, path_num):
		"""
		Gets the proportion of gaps in a subpath.
		
		:param int table_num: 1-indexed table number. 
		:param int path_num: 1-indexed subpath number. 
		:return: proportion of the total gaps between fragments in a subpath to the total range of the subpath. 
		:rtype: float
		"""
		assert (table_num >= 1 and path_num >= 1), DatabaseException("The table_num and path_num must be >= 1.")
		
		gaps = []
		total_range = []
		subpath_data = self.subpath_data(table_num, path_num)
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
			gap_proportion = 0
		else:
			gap_proportion = (gaps / total_range) * 100
		
		percentage_gap = 100.0 - gap_proportion
		return percentage_gap
		
	def inter_subpath_gap_score(table_num_a, path_num_a, table_num_b, path_num_b):
		data_a = self.subpath_data(table_num_a, path_num_a)
		data_b = self.subpath_data(table_num_b, path_num_b)

		start = data_a[0]["onset_range"][0]
		end = data_b[-1]["onset_range"][1]
		total_range = end - start

		gap_start = data_a[-1]["onset_range"][1]
		gap_stop = data_b[0]["onset_range"][0]
		gap = gap_stop - gap_start
		
		inter_gap_score = (gap / total_range) * 100
		return 100 - inter_gap_score

	def get_subpath_model_val(self, table_num, path_num, weights=[0.7, 0.3]):
		"""
		:return: the value of the model for a given subpath. The default parameters are for the initial path. 
		:rtype: float
		"""		
		assert (table_num >= 1 and path_num >= 1), DatabaseException("The table_num and path_num must be >= 1.")
		
		gap_score = self.get_subpath_intra_gap_score(table_num, path_num)
		onset_score = self.subpath_onset_percentile(table_num, path_num)
		scores = [gap_score, onset_score]

		model = 0
		for weight, score in zip(weights, scores):
			model += weight * score
		
		return model

	def get_highest_modeled_subpath(self, table_num, weights):
		"""Gets the highest modeled subpath in the table."""	
		assert table_num >= 1, DatabaseException("The table_num must be >= 1.")
		
		num_rows = _num_rows_in_table("Paths_{}".format(table_num), self.conn)
		highest_subpath = None
		highest_model_val = 0
		for i in range(1, num_rows + 1):
			model_val = self.get_subpath_model_val(table_num, i, weights)
			if model_val > highest_model_val:
				model_val = highest_model_val
				highest_subpath = i

		return highest_subpath
	
	def model_full_path(self, initial_weights, weights):
		"""Return list of subpath nums for each table."""
		assert table_num >= 1, DatabaseException("The table_num must be >= 1.")
		
		path = []
		# i = 0
		# # get highest first subpath in paths_0 (1)
		# first = self.get_highest_modeled_subpath(1, weights=[0.7, 0.3])


		# #while i < self.num_subpath_tables - 1:
		# 	#i += 1
		# path.append(first)
		return path

####################################################################################################
# Fragment Databases
"""The following function is used to create the databases for fragment querying."""
# Helpers
def _get_initial_data(path, size, log_msg):
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
			frag_dict["r_keep"] = 100 # arbitrary starting value
			frag_dict["d_equivalents"] = []
			frag_dict["d_keep"] = 100 # arbitrary starting value
			
			initial_data.append(frag_dict)
			bar.next()
	return initial_data

def _track_rd_equivalents(dataset_a, dataset_b, dataset_b_frag_type):
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

def _track_keep_vals(data, size, frag_type):
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

def _make_table(data, table_name, conn):
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

def _create_fragment_database(verbose=True):
	"""Dataset counts: 130 Decitalas, 26 Greek Metrics."""
	db_path = os.path.dirname(here) + "/databases/fragment_database.db"
	
	decitala_initial_data = _get_initial_data(path=decitala_path, size=130, log_msg="Getting initial decitala data...")	
	greek_metric_initial_data = _get_initial_data(path=greek_path, size=26, log_msg="Getting initial greek metric data...")

	logging.info("Tracking intra-level decitala equivalents...")
	decitala_intra_equivalents = _track_rd_equivalents(
		dataset_a=decitala_initial_data, 
		dataset_b=decitala_initial_data, 
		dataset_b_frag_type="decitala"
	)
	logging.info("Tracking cross-corpus decitala equivalents...")
	decitala_cross_equivalents = _track_rd_equivalents(
		dataset_a=decitala_intra_equivalents, 
		dataset_b=greek_metric_initial_data, 
		dataset_b_frag_type="greek_foot"
	)

	logging.info("Getting keep/ignore decitala data...")
	final_decitala_data = _track_keep_vals(data=decitala_cross_equivalents, size=130, frag_type="decitala")

	###############################################################################################
	logging.info("Tracking intra-level greek metric equivalents...")
	greek_intra_equivalents = _track_rd_equivalents(
		dataset_a=greek_metric_initial_data, 
		dataset_b=greek_metric_initial_data, 
		dataset_b_frag_type="greek_foot"
	)	
	logging.info("Tracking cross-corpus greek metric equivalents...")
	greek_cross_equivalents = _track_rd_equivalents(
		dataset_a=greek_intra_equivalents, 
		dataset_b=decitala_initial_data, 
		dataset_b_frag_type="decitala"
	)

	logging.info("Getting keep/ignore greek metric data...")
	final_greek_data = _track_keep_vals(data=greek_cross_equivalents, size=26, frag_type="greek_foot")

	logging.info("Creating the fragments tables...")
	conn = sqlite3.connect(db_path)
	
	_make_table(data=final_decitala_data, table_name="Decitalas", conn=conn)
	_make_table(data=final_greek_data, table_name="Greek_Metrics", conn=conn)
	
	logging.info("Done preparing ✔")
	conn.commit()