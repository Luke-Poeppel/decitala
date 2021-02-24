# -*- coding: utf-8 -*-
####################################################################################################
# File:     database.py
# Purpose:  Data structure for creating and representing databases using sqlite. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020 / Frankfurt, DE 2020 / NYC, 2021
####################################################################################################
"""
Tools for creating SQLite databases of extracted rhythmic data from Messiaen's music.  
"""
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import random
import sqlite3
import sys
import timeout_decorator
import timeit
import uuid

from ast import literal_eval
from itertools import groupby
from progress.bar import Bar
from progress.spinner import Spinner
from scipy import stats

from sqlalchemy.ext.declarative import declarative_base 
from sqlalchemy import (
	create_engine,
	MetaData,
	Column,
	Table,
	Integer,
	String,
	Float,
	Boolean,
	PickleType,
	ARRAY,
	select
)

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
	contour_to_prime_contour, 
	get_logger
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

mpl.style.use("seaborn")

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

# Helper function
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

def as_native_type(x):
	if type(x).__module__ == np.__name__:
		return x.item()
	return x

####################################################################################################
Base = declarative_base()
class Fragment(Base):
	__tablename__ = "Fragments"

	onset_start = Column(Float)
	onset_stop = Column(Float)
	fragment = Column(String, primary_key=True)
	mod = Column(String)
	fod = Column(Float)
	pitch_content = Column(String)
	contour = Column(String)
	prime_contour = Column(String)
	is_slurred = Column(Boolean)

	def __init__(
			self, 
			onset_start, 
			onset_stop,
			fragment,
			mod,
			fod,
			pitch_content,
			contour,
			prime_contour,
			is_slurred
		):
		self.onset_start = onset_start
		self.onset_stop = onset_stop
		self.fragment = fragment
		self.mod = mod
		self.fod = fod
		self.pitch_content = pitch_content
		self.contour = contour
		self.prime_contour = prime_contour
		self.is_slurred = is_slurred
	
	def __repr__(self):
		pass
		#return json.dumps()

def _prepare_fragment_data(
		filepath,
		part_num,
		frag_types,
		rep_types,
		allowed_modifications,
		try_contiguous_summation,
		windows,
		allow_unnamed,
		filter_found_single_anga_class,
		filter_found_sub_fragments,
		keep_grace_notes,
		logger
	):
	UNFILTERED_DATA = []
	ALL_DATA = []
	for this_frag_type in frag_types:
		logger.info("\n")
		logger.info("Making fragment tree(s) (and searching) for frag_type: {}".format(this_frag_type))

		if "ratio" in rep_types:
			curr_ratio_tree = FragmentTree.from_frag_type(frag_type=this_frag_type, rep_type="ratio")
		if "difference" in rep_types:
			curr_difference_tree = FragmentTree.from_frag_type(frag_type=this_frag_type, rep_type="difference")

		data = rolling_search(
			filepath,
			part_num,
			curr_ratio_tree,
			curr_difference_tree,
			allowed_modifications,
			try_contiguous_summation,
			windows,
			allow_unnamed,
			logger
		)
		UNFILTERED_DATA.extend(data)
		ALL_DATA.extend(data)

	logger.info("\n{} fragments extracted".format(len(ALL_DATA)))
	
	logger.info("Removing cross-corpus duplicates...")
	ALL_DATA = remove_cross_corpus_duplicates(ALL_DATA)
	logger.info("{} fragments remaining.".format(len(ALL_DATA)))

	if filter_found_single_anga_class:
		logger.info("Removing all single anga class fragments...")
		ALL_DATA = filter_single_anga_class_fragments(ALL_DATA)
		logger.info("{} fragments remaining.".format(len(ALL_DATA)))
	
	if filter_found_sub_fragments:
		ALL_DATA = filter_sub_fragments(ALL_DATA)
		logger.info("Removing all sub fragments...")
		logger.info("{} fragments remaining.".format(len(ALL_DATA)))

	logger.info("Calculated break points: {}".format(get_break_points(ALL_DATA)))
	return UNFILTERED_DATA, ALL_DATA

def _make_fragment_table(name, data, metadata):
	"""Helper function for writing the Fragments table of the database."""
	FragmentTable = Table(
		name,
		metadata,
		Column("onset_start", Float),
		Column("onset_stop", Float),
		Column("fragment", String),
		Column("mod", String),
		Column("fod", Float),
		Column("pitch_content", String),
		Column("contour", String),
		Column("prime_contour", String),
		Column("is_slurred", Boolean)
	)
	FragmentTable.create()
	
	cur = FragmentTable.insert()
	for this_fragment in data:
		pitch_content = this_fragment["pitch_content"]
		contour = pitch_content_to_contour(this_fragment["pitch_content"]).tolist()
		prime_contour = contour_to_prime_contour(contour, include_depth=False).tolist()
		cur.execute(
			onset_start=as_native_type(this_fragment["onset_range"][0]),
			onset_stop=as_native_type(this_fragment["onset_range"][1]),
			fragment=this_fragment["fragment"].name,
			mod=this_fragment["mod"][0],
			fod=as_native_type(this_fragment["mod"][1]),
			pitch_content=json.dumps(pitch_content),
			contour=json.dumps(contour),
			prime_contour=json.dumps(prime_contour),
			is_slurred=int(this_fragment["is_spanned_by_slur"])
		)
	return FragmentTable

def _make_subpath_table(partitioned_data, fragment_table, metadata, connection, logger):
	query = select([fragment_table])
	res_exec = connection.execute(query)
	fragment_rows = res_exec.fetchall()
	for i, this_partition in enumerate(partitioned_data, start=1):
		pareto_optimal_paths = get_pareto_optimal_longest_paths(this_partition)
		longest_path = max([len(path) for path in pareto_optimal_paths])
		
		columns = [Column("onset_range_{}".format(i), Integer) for i in range(1, longest_path + 1)]
		subpath_table = Table("SubPath_{}".format(i), metadata, *columns)
		subpath_table.create()
		for path in pareto_optimal_paths:
			fragment_row_ids = []
			for this_fragment_data in path:
				data = this_fragment_data
				for j, this_row in enumerate(fragment_rows, start=1):
					if (this_row[2] == data["fragment"].name) and (this_row[0] == data["onset_range"][0]) and (this_row[1] == data["onset_range"][1]):
						fragment_row_ids.append(j)
			
			connection.execute(subpath_table.insert().values(fragment_row_ids))
	return

@timeout_decorator.timeout(75)
def create_database(
		db_path,
		filepath,
		part_num,
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
		windows=list(range(2, 20)),
		allow_unnamed=False,
		filter_found_single_anga_class=True,
		filter_found_sub_fragments=True,
		keep_grace_notes=True,
		verbose=True,
		write_logs_to_file=False
	):
	"""
	This function generates an sqlite3 database for storing extracted rhythmic data from :obj:`decitala.trees.rolling_search`.
	The database holds has one page for storing all extracted fragments, their onsets/offsets of occurrence, and their 
	modification data. 

	:param str db_path: path where the .db file will be written. 
	:param str filepath: path to score.
	:param int part_num: part number in the score. 
	:param bool filter_single_anga_class: whether or not to remove single-anga class fragments from the data in rolling_search. 
	:param bool filter_found_sub_fragments: whether or not to remove sub-fragments from the dataset. 
	:param bool verbose: whether or not to log information about the database creation process (including data from rolling search). 
	
	:return: sqlite3 database
	:rtype: .db file
	"""
	assert os.path.isfile(filepath), DatabaseException("✗ The path provided is not a valid file.")
	assert db_path.endswith(".db"), DatabaseException("✗ The db_path must end with '.db'.")
	if os.path.isfile(db_path):
		return "That database already exists ✔"

	filename = filepath.split("/")[-1]
	if write_logs_to_file:
		log_filepath = db_path[:-3] + ".log"
	else:
		log_filepath=None

	logger = get_logger(name=__name__, print_to_console=verbose, write_to_file=log_filepath)
	
	logger.info("Preparing database...")
	logger.info("File: {}".format(filename))
	logger.info("Part: {}".format(part_num))
	logger.info("Fragment types: {}".format(frag_types))
	logger.info("Representation types: {}".format(rep_types))
	logger.info("Allowed windows: {}".format(windows))
	logger.info("Modifications: {}".format(allowed_modifications))
	logger.info("Try contiguous summations: {}".format(try_contiguous_summation))
	logger.info("Filter single anga class fragments: {}".format(filter_found_single_anga_class))
	logger.info("Filter sub fragments: {}".format(filter_found_sub_fragments))

	db = create_engine("sqlite:////{}".format(db_path))
	connection = db.connect()
	logger.info("\nConnected to database at: {}".format(db_path))

	metadata = MetaData(db)
	
	UNFILTERED_DATA, ALL_DATA = _prepare_fragment_data(
		filepath,
		part_num,
		frag_types,
		rep_types,
		allowed_modifications,
		try_contiguous_summation,
		windows,
		allow_unnamed,
		filter_found_single_anga_class,
		filter_found_sub_fragments,
		keep_grace_notes,
		logger
	)
	sorted_onset_ranges = sorted(ALL_DATA, key = lambda x: x["onset_range"][0])
	sorted_onset_ranges_two = sorted(UNFILTERED_DATA, key = lambda x: x["onset_range"][0])
	logger.info("Making the (unfiltered) fragment table...")
	fragment_table = _make_fragment_table(name="UnfilteredFragments", data=sorted_onset_ranges_two, metadata=metadata)
	partitioned_data = partition_data_by_break_points(sorted_onset_ranges)

	logger.info("Making the (filtered) fragment table...")
	fragment_table = _make_fragment_table(name="Fragments", data=sorted_onset_ranges, metadata=metadata)
	logger.info("Done ✔")
	logger.info("Calculating pareto optimal paths...")
	_make_subpath_table(partitioned_data=partitioned_data, fragment_table=fragment_table, metadata=metadata, connection=connection, logger=logger)
	logger.info("Done ✔")
	logger.info("Done preparing ✔")

####################################################################################################
# Helper functions
def _num_subpath_tables(conn):
	"""
	Returns the number of Path tables in a database db.
	
	>>> example_data = "./databases/liturgie_3.db"
	>>> conn = sqlite3.connect(example_data)
	>>> _num_subpath_tables(conn)
	14
	"""
	QUERY_STRING = "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'"
	data = pd.read_sql_query(QUERY_STRING, conn)
	num_path_tables = data["COUNT(*)"].iloc[0] - 1

	return num_path_tables

def _num_rows_in_table(table, conn):
	"""
	Returns the number of rows in a given table.
	
	>>> example_data = "./databases/liturgie_3.db"
	>>> conn = sqlite3.connect(example_data)
	>>> _num_rows_in_table("SubPath_1", conn)
	2
	"""
	QUERY_STRING = "SELECT COUNT(*) FROM {}".format(table)
	data = pd.read_sql_query(QUERY_STRING, conn)
	num_rows = data["COUNT(*)"].iloc[0]
	
	return num_rows

class DBParser:
	"""
	Class used for parsing the SQLite database made in :obj:`~decitala.database.create_database`.

	>>> example_data = "./databases/liturgie_3.db"
	>>> lit_db = DBParser(example_data)
	>>> lit_db
	<database.DBParser liturgie_3.db>
	>>> for frag in lit_db.fragments()[0:5]:
	... 	print(frag)
	<fragment.Decitala 41_Rajavidyadhara>
	<fragment.Decitala 101_Simha>
	<fragment.Decitala 43_Malikamoda>
	<fragment.Decitala 88_Lakskmica>
	<fragment.Decitala 93_Ragavardhana>
	>>> lit_db.num_subpath_tables
	14
	>>> lit_db.subpath(11, 5)
	[42, 44, 49, 54]
	>>> for data in lit_db.subpath_data(11, 5):
	... 	print(data["fragment"], data["onset_range"])
	<fragment.Decitala 93_Ragavardhana> (93.0, 97.75)
	<fragment.Decitala 37_Rangabharana> (97.75, 100.0)
	<fragment.Decitala 21_Tribhinna> (101.5, 103.0)
	<fragment.Decitala 93_Ragavardhana> (106.0, 110.75)
	>>> lit_db.subpath_intra_gap_score(11, 5)
	66.0377358490566
	>>> lit_db.subpath_onset_percentile(11, 5)
	11.904761904761905
	>>> # the model requires weights (for table num > 1, 2 values). 
	>>> lit_db.intra_subpath_model_score(11, 5, weights=[0.7, 0.3])
	49.79784366576819
	>>> # for table num == 1, it requires 3 weights: 
	>>> lit_db.intra_subpath_model_score(1, 1, weights=[0.5, 0.3, 0.2])
	90.83333333333334
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

		earliest_detected_onset = 100 # random starting value.

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
		for i in range(1, self.num_subpath_tables):
			num_rows = _num_rows_in_table("SubPath_{}".format(i), self.conn)
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

	def onset_ranges(self):
		"""
		:return: a list of tuples holding the onset ranges for each extracted fragment.
		:rtype: list
		"""
		return [x["onset_range"] for x in self.fragment_data]

	######## Visualization ########
	def show_fragments_table(self, unfiltered=False):
		"""
		Displays the Fragments table of the database.

		:param bool unfiltered: whether to display the unfiltered fragment data. 
		:return: the fragments table (as a dataframe). 
		:rtype: pandas.DataFrame 
		"""
		if not(unfiltered):
			data = pd.read_sql_query("SELECT * FROM Fragments", self.conn)
		else:
			data = pd.read_sql_query("SELECT * FROM UnfilteredFragments", self.conn)
		return data
	
	def show_slurred_fragments(self):
		"""
		Displays the slurred fragments in the Fragments table of the database.
		
		:return: the subset of slurred fragments in the fragments table (as a dataframe). 
		:rtype: pandas.DataFrame 
		"""
		data = pd.read_sql_query("SELECT * FROM Fragments WHERE is_slurred = 1", self.conn)
		return data

	def show_subpath_table(self, table_num):
		"""
		Displays the queried subpath table. These subpath tables are 1-indexed.
		
		:param int table_num: 1-indexed table number. 
		:return: the queried subpath tale (as a dataframe).
		:rtype: pandas.DataFrame
		"""
		assert table_num >= 1, DatabaseException("The table_num must be >= 1.")
		
		data = pd.read_sql_query("SELECT * FROM SubPath_{}".format(table_num), self.conn)
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
		
		QUERY_STRING = "SELECT * FROM SubPath_{0} WHERE rowid = {1}".format(table_num, path_num)
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

		QUERY_STRING = "SELECT * FROM SubPath_{0} WHERE rowid = {1}".format(table_num, path_num)
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
		:return: list (of length equal to the number of rows in the queried ``SubPath`` table) 
				holding the average number of onsets (type: float) for a fragment in each subpath. 
		:rtype: list
		"""
		assert table_num >= 1, DatabaseException("The table_num must be >= 1.")
		
		num_rows = _num_rows_in_table("SubPath_{}".format(table_num), self.conn)
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
		:return: percentile (0-100) of a given subpath in the context of its full ``Subpath`` table. 
		:rtype: float
		"""
		assert (table_num >= 1 and path_num >= 1), DatabaseException("The table_num and path_num must be >= 1.")
		
		subpath_data = self.subpath_data(table_num, path_num)
		subpath_average_onsets = np.mean([x["fragment"].num_onsets for x in subpath_data])
		
		# NOTE: I call metadata instead of the above function as it then doesn't need to be recalulated. 
		onset_data = self.metadata[table_num - 1][2]
		percentile = stats.percentileofscore(onset_data, subpath_average_onsets)

		return percentile

	def first_subpath_start_gap_score(self, path_num):
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

	def subpath_intra_gap_score(self, table_num, path_num):
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
		
	def subpath_inter_gap_score(
			self, 
			table_num_a, 
			path_num_a, 
			table_num_b, 
			path_num_b
		):
		"""
		Gets the proportion of the gap between two subpaths to the whole range of the paths. 
		"""
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

	#####################################################################################
	def intra_subpath_model_score(
			self, 
			table_num, 
			path_num, 
			weights
		):
		"""
		:param int table_num: 1-indexed table number. 
		:param int path_num: 1-indexed subpath number. 
		:param list weights: intra-subpath weights.  
		:return: returns the intra-subpath model score. 
		:rtype: float
		"""
		assert (table_num >= 1 and path_num >= 1), DatabaseException("The table_num and path_num must be >= 1.")
		if table_num == 1:
			assert len(weights) == 3, DatabaseException("For the first table, three weights must be provided.")

		gap_score = self.subpath_intra_gap_score(table_num, path_num)
		onset_score = self.subpath_onset_percentile(table_num, path_num)
		model = 0
		if table_num == 1:
			start_gap_score = self.first_subpath_start_gap_score(path_num)
			scores = [gap_score, onset_score, start_gap_score]
			for weight, score in zip(weights, scores):
				model += weight * score
		else:
			scores = [gap_score, onset_score]
			for weight, score in zip(weights, scores):
				model += weight * score

		return model
	
	def highest_modeled_subpath(
			self, 
			table_num,
			weights
		):
		"""
		Gets the highest modeled subpath in the table.

		:param int table_num: 1-indexed table number. 
		:param list weights: intra-subpath weights. 
		"""
		assert table_num >= 1, DatabaseException("The table_num must be >= 1.")
		
		num_rows = _num_rows_in_table("SubPath_{}".format(table_num), self.conn)
		highest_subpath = None
		highest_model_val = 0
		for i in range(1, num_rows + 1):
			model_val = self.intra_subpath_model_score(table_num, i, weights)
			if model_val > highest_model_val:
				highest_model_val = model_val
				highest_subpath = i

		return highest_subpath

	def model_full_path(
			self,
			start_weights = [0.5, 0.3, 0.2], 
			rest_weights = [0.7, 0.3], 
			intra_inter_weights = [0.8, 0.2],
			return_data=False
		):
		"""
		Return list of highest modeled subpath nums for each table. 
		"""
		path = []
		table_num = 1
		# the latter two arguments allow for displaying in jupyter. 
		with Bar("Modeling full path...", max=self.metadata[-1][0] + 1, check_tty=False, hide_cursor=False) as bar:
			while table_num < self.metadata[-1][0] + 1:
				if table_num == 1:
					highest_first_subpath = self.highest_modeled_subpath(table_num, weights=start_weights)
					path.append(highest_first_subpath)
				else:
					last = path[-1]
					curr_data = self.metadata[table_num - 1]
					scores = []
					for row_num in range(1, curr_data[1] + 1):
						fragments = [x["fragment"] for x in self.subpath_data(table_num, row_num)]
						intra_model_score = self.intra_subpath_model_score(table_num, row_num, rest_weights)
						inter_subpath_score = self.subpath_inter_gap_score(table_num - 1, last, table_num, row_num)
						combined = (intra_inter_weights[0] * intra_model_score) + (intra_inter_weights[1] * inter_subpath_score)
						scores.append(combined)
					
					path.append(scores.index(max(scores))+1)
				
				bar.next()
				table_num += 1
			
			bar.next() # one extra...
			
		if not(return_data):
			return path
		else:
			return self.path_data(row_nums=path)
	
	def path_data(self, row_nums):
		full_data = []
		for i, row_num in enumerate(row_nums):
			full_data.extend(self.subpath_data(i+1, row_num))
		return full_data
	
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

	#logging.info("Tracking intra-level decitala equivalents...")
	decitala_intra_equivalents = _track_rd_equivalents(
		dataset_a=decitala_initial_data, 
		dataset_b=decitala_initial_data, 
		dataset_b_frag_type="decitala"
	)
	#logging.info("Tracking cross-corpus decitala equivalents...")
	decitala_cross_equivalents = _track_rd_equivalents(
		dataset_a=decitala_intra_equivalents, 
		dataset_b=greek_metric_initial_data, 
		dataset_b_frag_type="greek_foot"
	)

	#logging.info("Getting keep/ignore decitala data...")
	final_decitala_data = _track_keep_vals(data=decitala_cross_equivalents, size=130, frag_type="decitala")

	###############################################################################################
	#logging.info("Tracking intra-level greek metric equivalents...")
	greek_intra_equivalents = _track_rd_equivalents(
		dataset_a=greek_metric_initial_data, 
		dataset_b=greek_metric_initial_data, 
		dataset_b_frag_type="greek_foot"
	)	
	#logging.info("Tracking cross-corpus greek metric equivalents...")
	greek_cross_equivalents = _track_rd_equivalents(
		dataset_a=greek_intra_equivalents, 
		dataset_b=decitala_initial_data, 
		dataset_b_frag_type="decitala"
	)

	#logging.info("Getting keep/ignore greek metric data...")
	final_greek_data = _track_keep_vals(data=greek_cross_equivalents, size=26, frag_type="greek_foot")

	#logging.info("Creating the fragments tables...")
	conn = sqlite3.connect(db_path)
	
	_make_table(data=final_decitala_data, table_name="Decitalas", conn=conn)
	_make_table(data=final_greek_data, table_name="Greek_Metrics", conn=conn)
	
	#logging.info("Done preparing ✔")
	conn.commit()
