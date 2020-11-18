# -*- coding: utf-8 -*-
####################################################################################################
# File:     database.py
# Purpose:  Data structure for creating and representing databases using sqlite. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
NOTE: 
- IMPORTANT: there should be a kind of discrimination approach here. We should be able to create a 
database that excludes all single-onset talas and create the paths from there. 
- Should have the option to create a decitala database, greek foot database, combined 
database, etc... For now, let's just assume it's a decitala databse. 
- This function would work well in command line. decitala_v2 create_database <score_path> <part_num>

TODO:
- It doesn't make sense to rewrite all the code twice. Make "filter" a parameter for create_database.
So the command line tool would be something like decitala create_database (un)filtered <path> <part_num>
- get_indices_of_object_occurrence really shouldn't be a tree function; it should be separate. 
- you should be able to build a database on exact matches only. this is more of a TODO for get_by_ql_list.
"""
import click
import numpy as np
import sqlite3 as lite
import sys

from music21 import converter
from music21 import stream

from fragment import Decitala
from trees import FragmentTree#, rolling_search2
from pofp import (
	dynamically_partition_onset_list, 
	get_pareto_optimal_longest_paths,
	filter_single_anga_class_talas,
	filter_subtalas
)

decitala_path = '/Users/lukepoeppel/decitala_v2/Decitalas'

####################################################################################################
# Helper functions
def _name_from_tala_string(tala_string):
	"""
	'<decitala.Decitala 51_Vijaya>' -> Decitala
	"""
	new_str = tala_string.split()[1][:-1]
	if new_str == '121_Varied_Ragavardhana':
		return Decitala('121_Varied_Ragavardhana.mxl')
	
	return Decitala(new_str)

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

def create_database(score_path, part_num, db_name):
	"""
	Function for creating a decitala and paths database in the cwd. 
	NOTE: this function creates the raw database with no filtering
	"""
	tree = FragmentTree(root_path = decitala_path, frag_type = 'decitala', rep_type = 'ratio')
	onset_ranges = []
	for this_tala in tree.rolling_search(path = score_path, part_num = part_num):
		onset_ranges.append(list(this_tala))

	sorted_onset_ranges = sorted(onset_ranges, key = lambda x: x[1][0])

	partitioned = dynamically_partition_onset_list(sorted_onset_ranges)
	all_objects = tree.get_indices_of_object_occurrence(score_path, part_num)

	conn = lite.connect(db_name)

	with conn:
		cur = conn.cursor()
		cur.execute("CREATE TABLE Fragment (Onset_Start REAL, Onset_Stop REAL, Tala BLOB, Mod TEXT, Factor INT)")

		for this_partition in partitioned:
			for x in this_partition:
				cur.execute("INSERT INTO Fragment VALUES({0}, {1}, '{2}', '{3}', {4})".format(x[1][0], x[1][1], x[0][0], x[0][1][0], x[0][1][1]))

		cur.execute("SELECT * FROM Fragment")
		rows = cur.fetchall()
		onset_data = []
		for row in rows:
			onset_data.append((row[0], row[1]))
		
		#paths
		for i, this_partition in enumerate(partitioned):
			pareto_optimal_paths = get_pareto_optimal_longest_paths(this_partition)
			lengths = [len(path) for path in pareto_optimal_paths]
			longest_path = max(lengths)

			columns = ['Onset_Range_{}'.format(i) for i in range(1, longest_path + 1)]
			columns_declaration = ', '.join('%s BLOB' % c for c in columns)
			newer = columns_declaration + ', Pitch_Content BLOB'

			cur.execute("CREATE TABLE Paths_{0} ({1})".format(str(i), newer))
			for path in pareto_optimal_paths:
				#Get nPVI information for the path.
				cur.execute("SELECT * FROM Fragment")
				rows = cur.fetchall()

				#nPVI_vals = []
				pitch_content = []
				for this_range in path:
					pitch_content.append(_pitch_info_from_onset_range(this_range[-1], all_objects))
					for row in rows:
						if this_range[-1][0] == row[0] and this_range[-1][1] == row[1]:
							tala = _name_from_tala_string(row[2])
							#nPVI_vals.append(tala.nPVI())
				
				#avg_nPVI = np.mean(nPVI_vals)
				flattened = [note for tala in pitch_content for note in tala]
				formatted_pitch_content = str(tuple([tuple(sublist) for sublist in pitch_content]))

				#format the pitch content as one continous string.
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

def create_filtered_database(score_path, part_num, db_name):
	"""
	Function for creating a decitala and paths database in the cwd. 
	NOTE: this function creates the filtered database. (No subtalas, no single anga-class talas)
	"""
	ratio_tree = FragmentTree(root_path=decitala_path, frag_type='decitala', rep_type = 'ratio')
	difference_tree = FragmentTree(root_path=decitala_path, frag_type='decitala', rep_type = 'difference')

	onset_ranges = []
	for this_tala in rolling_search(score_path, part_num, ratio_tree, difference_tree): # this was rolling_search2...
		onset_ranges.append(list(this_tala))

	sorted_onset_ranges = sorted(onset_ranges, key = lambda x: x[1][0])
	filter_single_anga_classes_list = filter_single_anga_class_talas(sorted_onset_ranges)
	filter_subtalas_list = filter_subtalas(filter_single_anga_classes_list)

	partitioned = dynamically_partition_onset_list(filter_subtalas_list)
	all_objects = ratio_tree.get_indices_of_object_occurrence(score_path, part_num)

	conn = lite.connect(db_name)

	with conn:
		cur = conn.cursor()
		cur.execute("CREATE TABLE Fragment (Onset_Start REAL, Onset_Stop REAL, Tala BLOB, Mod TEXT, Factor INT)")

		for this_partition in partitioned:
			for x in this_partition:
				cur.execute("INSERT INTO Fragment VALUES({0}, {1}, '{2}', '{3}', {4})".format(x[1][0], x[1][1], x[0][0].name, x[0][1][0], x[0][1][1]))

		cur.execute("SELECT * FROM Fragment")
		rows = cur.fetchall()
		onset_data = []
		for row in rows:
			onset_data.append((row[0], row[1]))
		
		#paths
		for i, this_partition in enumerate(partitioned):
			pareto_optimal_paths = get_pareto_optimal_longest_paths(this_partition)
			lengths = [len(path) for path in pareto_optimal_paths]
			longest_path = max(lengths)

			columns = ['Onset_Range_{}'.format(i) for i in range(1, longest_path + 1)]
			columns_declaration = ', '.join('%s BLOB' % c for c in columns)
			newer = columns_declaration + ', Pitch_Content BLOB'

			cur.execute("CREATE TABLE Paths_{0} ({1})".format(str(i), newer))
			for path in pareto_optimal_paths:
				cur.execute("SELECT * FROM Fragment")
				rows = cur.fetchall()

				pitch_content = []
				for this_range in path:
					pitch_content.append(_pitch_info_from_onset_range(this_range[-1], all_objects))
					for row in rows:
						if this_range[-1][0] == row[0] and this_range[-1][1] == row[1]:
							#tala = _name_from_tala_string(row[2])
							if '121' in row[2]:
								tala = Decitala.get_by_id(121)
							else:
								tala = Decitala(row[2])
				
				flattened = [note for tala in pitch_content for note in tala]
				formatted_pitch_content = str(tuple([tuple(sublist) for sublist in pitch_content]))

				#format the pitch content as one continous string.
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

##################### TESTING #####################
if __name__ == "__main__":
	#sept_haikai_path = '/Users/lukepoeppel/Desktop/Messiaen/Sept_Haikai/1_Introduction.xml'
	#liturgie_path = '/Users/lukepoeppel/Dropbox/Luke_Myke/Messiaen_Qt/Messiaen_I_Liturgie/Messiaen_I_Liturgie_de_cristal_CORRECTED.mxl'
	#livre_dorgue_path = "/Users/lukepoeppel/Desktop/Messiaen/Livre_d\'Orgue/V_Piece_En_Trio.xml"

	#create_database(score_path=liturgie_path, part_num=3, db_name="/Users/lukepoeppel/decitala_v2/liturgie_piano3_test1.db")
	'''
	create_filtered_database(sept_haikai_path, 0, '/Users/lukepoeppel/decitala_v2/sept_haikai_0.db')
	create_filtered_database(sept_haikai_path, 1, '/Users/lukepoeppel/decitala_v2/sept_haikai_1.db')

	create_filtered_database(livre_dorgue_path, 0, '/Users/lukepoeppel/decitala_v2/livre_dorgue_0.db')
	create_filtered_database(livre_dorgue_path, 1, '/Users/lukepoeppel/decitala_v2/livre_dorgue_1.db')

	create_filtered_database(liturgie_path, 3, '/Users/lukepoeppel/decitala_v2/liturgie_3.db')
	create_filtered_database(liturgie_path, 4, '/Users/lukepoeppel/decitala_v2/liturgie_4.db')
	'''
	import doctest
	doctest.testmod()