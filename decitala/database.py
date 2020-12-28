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
import sqlite3 as lite
import timeout_decorator
import uuid

from music21 import converter
from music21 import stream

from .utils import (
	get_object_indices,
	successive_ratio_array,
	filter_single_anga_class_fragments,
	filter_sub_fragments
)

from .trees import (
	FragmentTree,
	rolling_search
)

from .pofp import (
	get_break_points,
	partition_data_by_break_points,
	get_pareto_optimal_longest_paths
)

import logging
logging.basicConfig(level=logging.INFO)

# Fragments
here = os.path.abspath(os.path.dirname(__file__))

decitala_path = os.path.dirname(here) + "/Fragments/Decitalas"
greek_path = os.path.dirname(here) + "/Fragments/Greek_Metrics/XML"

############### EXCEPTIONS ###############
class DatabaseException(Exception):
	pass

def _check_tuple_in_tuple_range(tup1, tup2):
	"""
	Checks if tuple 1 is contained in tuple 2, e.g. (2, 4) in (1, 5)
	>>> _check_tuple_in_tuple_range((2, 4), (1, 5))
	True
	>>> _check_tuple_in_tuple_range((0.0, 1.5), (0.0, 4.0))
	True
	>>> _check_tuple_in_tuple_range((2.5, 4.0), (0.0, 4.0))
	True
	>>> _check_tuple_in_tuple_range((4.0, 4.375), (0.0, 4.0))
	False
	"""
	if tup1[0] >= tup2[0] and tup1[0] <= tup2[1] and tup1[1] <= tup2[1]:
		return True
	else:
		return False 

def _pitch_info_from_onset_range(onset_range, all_objects_in_part):
	"""
	Function that takes in onset range and returns the pitch.midi information for that range.
	The input ``data`` is that which is returned in rolling_search. 
	"""
	note_data = []
	for this_object in all_objects_in_part:
		if _check_tuple_in_tuple_range(this_object[1], onset_range):
			note_data.append(this_object)
	
	pitches = [n[0].pitches for n in note_data]
	midi = []
	for pitch_info in pitches:
		midi.append(tuple([x.midi for x in pitch_info]))
	
	return midi

####################################################################################################
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
	assert os.path.isfile(filepath), "The path provided is not a valid file."

	filename = filepath.split('/')[-1]
	if verbose:
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
		if verbose:
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

	if verbose:
		logging.info("\n")
		logging.info("{} fragments extracted".format(initial_length))

	if filter_found_single_anga_class:
		ALL_DATA = filter_single_anga_class_fragments(ALL_DATA)
		if verbose:
			logging.info("Removing all single anga class fragments...")
			logging.info("Removed {0} fragments ({1} remaining)".format(initial_length - len(ALL_DATA), len(ALL_DATA)))
	
	new_length = len(ALL_DATA)

	if filter_found_sub_fragments:
		ALL_DATA = filter_sub_fragments(ALL_DATA)
		if verbose:
			logging.info("Removing all sub fragments...")
			logging.info("Removed {0} fragments ({1} remaining)".format(new_length - len(ALL_DATA), len(ALL_DATA)))

	if verbose:
		logging.info("Calculated break points: {}".format(get_break_points(ALL_DATA)))

	all_object = get_object_indices(filepath, part_num)
	sorted_onset_ranges = sorted(ALL_DATA, key = lambda x: x[1][0])
	partitioned_data = partition_data_by_break_points(sorted_onset_ranges)

	conn = lite.connect(db_path)
	with conn:
		if verbose:
			logging.info("\n")
			logging.info("Connected to database at: {}".format(db_path))
		cur = conn.cursor()
		cur.execute("CREATE TABLE Fragments (Onset_Start REAL, Onset_Stop REAL, Fragment BLOB, Mod TEXT, Factor INT)")

		for this_partition in partitioned_data:
			for this_fragment in this_partition:
				cur.execute("INSERT INTO Fragments VALUES({0}, {1}, '{2}', '{3}', {4})".format(this_fragment[1][0], this_fragment[1][1], this_fragment[0][0], this_fragment[0][1][0], this_fragment[0][1][1]))

		for i, this_partition in enumerate(partitioned_data):
			pareto_optimal_paths = get_pareto_optimal_longest_paths(this_partition)
			lengths = [len(path) for path in pareto_optimal_paths]
			longest_path = max(lengths)

			columns = ['Onset_Range_{}'.format(i) for i in range(1, longest_path + 1)]
			columns_declaration = ', '.join('%s BLOB' % c for c in columns)
			newer = columns_declaration + ', Pitch_Content BLOB'

			cur.execute("CREATE TABLE Paths_{0} ({1})".format(str(i), newer))
			if verbose:
				logging.info("Making Paths_{} table".format(i))
			
			for path in pareto_optimal_paths:
				cur.execute("SELECT * FROM Fragments")
				rows = cur.fetchall()
				pitch_content = []
				for this_range in path:
					pitch_data_in_range = _pitch_info_from_onset_range(this_range[1], all_object)
					pitch_content.append(pitch_data_in_range)

				formatted_pitch_content = str(tuple([tuple(sublist) for sublist in pitch_content]))

				# Format the pitch content as one continous string.
				if len(path) == longest_path:
					data = []
					for this_range in path:
						data.append('{0}'.format(this_range[-1]))
					
					mid = "', '".join(data)
					post = "INSERT INTO Paths_{0} VALUES('".format(str(i)) + mid + "', '{0}')".format(formatted_pitch_content)
					cur.execute(post)
				else:
					diff = longest_path - len(path)
					data = []
					for this_range in path:
						data.append('{0}'.format(this_range[-1]))
					
					mid = "', '".join(data)
					nulls = ["'NULL'"] * diff
					post_nulls = ", ".join(nulls)
					new = "INSERT INTO Paths_{0} VALUES('{1}', {2}, '{3}')".format(str(i), mid, post_nulls, formatted_pitch_content)
					cur.execute(new)
		
		if verbose:
			logging.info("Done preparing ✔")

if __name__ == "__main__":
	import doctest
	doctest.testmod()