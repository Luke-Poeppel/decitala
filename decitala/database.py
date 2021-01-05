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
import click
import numpy as np
import os
import pandas as pd
import sqlite3 as lite
import timeout_decorator
import uuid

from ast import literal_eval

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
	logging.info("Keep grace notes: {}".format(keep_grace_notes))

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

	# ALL_DATA = filter_data(ALL_DATA)
	# logging.info("Removing cross-corpus duplicates and LD fragments...")
	# logging.info("Removed {0} fragments ({1} remaining)".format(initial_length - len(ALL_DATA), len(ALL_DATA)))
	
	if filter_found_single_anga_class:
		ALL_DATA = filter_single_anga_class_fragments(ALL_DATA)

		logging.info("Removing all single anga class fragments...")
		logging.info("Removed {0} fragments ({1} remaining)".format(initial_length - len(ALL_DATA), len(ALL_DATA)))
	
	new_length = len(ALL_DATA)

	if filter_found_sub_fragments:
		ALL_DATA = filter_sub_fragments(ALL_DATA)
		logging.info("Removing all sub fragments...")
		logging.info("Removed {0} fragments ({1} remaining)".format(new_length - len(ALL_DATA), len(ALL_DATA)))

	logging.info("Calculated break points: {}".format(get_break_points(ALL_DATA)))

	all_object = get_object_indices(filepath, part_num)
	sorted_onset_ranges = sorted(ALL_DATA, key = lambda x: x["onset_range"][0])
	partitioned_data = partition_data_by_break_points(sorted_onset_ranges)

	conn = lite.connect(db_path)
	with conn:
		logging.info("\n")
		logging.info("Connected to database at: {}".format(db_path))

		cur = conn.cursor()
		fragment_table_string = "CREATE TABLE Fragments (Onset_Start REAL, Onset_Stop REAL, Fragment BLOB, Mod TEXT, Factor REAL, Pitch_Content BLOB, Pitch_Contour BLOB, Prime_Contour BLOB, Is_Slurred INT)"
		cur.execute(fragment_table_string)

		for this_partition in partitioned_data:
			for this_fragment in this_partition:
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

		for i, this_partition in enumerate(partitioned_data):			
			pareto_optimal_paths = get_pareto_optimal_longest_paths(this_partition)
			lengths = [len(path) for path in pareto_optimal_paths]
			longest_path = max(lengths)

			columns = ["Onset_Range_{}".format(i) for i in range(1, longest_path + 1)]
			columns_declaration = ", ".join("%s BLOB" % c for c in columns)

			cur.execute("CREATE TABLE Paths_{0} ({1})".format(str(i), columns_declaration))
			logging.info("Making Paths_{} table".format(i))
			
			for path in pareto_optimal_paths:
				if len(path) == longest_path:
					data = []
					for this_range in path:
						data.append("{0}".format(this_range[-1]))
					
					mid = "', '".join(data)
					post = "INSERT INTO Paths_{0} VALUES('".format(str(i)) + mid + "')"
					cur.execute(post)
				else:
					diff = longest_path - len(path)
					data = []
					for this_range in path:
						data.append('{0}'.format(this_range[-1]))
					
					mid = "', '".join(data)
					nulls = ["'NULL'"] * diff
					post_nulls = ", ".join(nulls)
					new = "INSERT INTO Paths_{0} VALUES('{1}', {2})".format(str(i), mid, post_nulls)
					cur.execute(new)
		
		logging.info("Done preparing ✔")

####################################################################################################
class DBParser(object):
	"""
	Class used for parsing data from the ``Fragments`` page of a database made via :obj:`~decitala.database.create_database`.

	>>> example_data = "/Users/lukepoeppel/decitala/tests/static/ex99_data.db"
	>>> parsed = DBParser(example_data)
	>>> for x in parsed.spanned_fragments()[0:3]:
	... 	print(x["fragment"].name)
	... 	print(x["pitch_content"])
	Iamb
	[(80,), (82,)]
	Iamb
	[(79,), (81,)]
	Iamb
	[(78,), (80,)]
	"""
	def __init__(self, db_path):
		assert os.path.isfile(db_path), DatabaseException("You've provided an invalid file.")

		self.db_path = db_path
		filename = self.db_path.split('/')[-1]
		self.filename = filename

		conn = lite.connect(self.db_path)
		self.conn = conn
		cur = conn.cursor()

		fragment_path_string = "SELECT * FROM Fragments"
		cur.execute(fragment_path_string)
		fragment_rows = cur.fetchall()
		
		data = []
		for this_row in fragment_rows:
			row_data = dict()

			fragment_str = this_row[2]
			if fragment_str[0].isdigit():
				this_fragment = Decitala(fragment_str)
			else:
				this_fragment = GreekFoot(fragment_str)

			row_data["fragment"] = this_fragment
			row_data["onset_range"] = (this_row[0], this_row[1])
			row_data["mod"] = this_row[3]
			row_data["factor"] = this_row[4]
			row_data["pitch_content"] = literal_eval(this_row[5])
			row_data["is_slurred"] = bool(this_row[6])

			data.append(row_data)

		self.data = data

	def __repr__(self):
		return "<database.DBParser {}>".format(self.filename)
	
	@property
	def fragments(self):
		return [x["fragment"] for x in self.data]

	def spanned_fragments(self):
		return [x for x in self.data if x["is_slurred"]==True]

	# Useful visualizations for jupyter.
	def show_fragments_table(self):
		"""
		Displays the Fragments table of the database using pandas. 
		"""
		data = pd.read_sql_query("SELECT * FROM Fragments", self.conn)
		return data
	
	def show_spanned_fragments(self):
		"""
		Displays the Fragments table of the database using pandas. 
		"""
		data = pd.read_sql_query("SELECT * FROM Fragments WHERE Is_Slurred = 1", self.conn)
		return data