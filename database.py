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
Notes: 
- Should have the option to create a decitala database, greek foot database, combined 
database, etc... For now, let's just assume it's a decitala databse. 
- This function would work well in command line. decitala_v2 create_database <score_path> <part_num>

TODO:
- get_indices_of_object_occurrence really shouldn't be a tree function; it should be separate. 
- you should be able to build a database on exact matches only. this is more of a TODO for get_by_ql_list.
"""
import click
import numpy as np
import sqlite3 as lite
import sys

from music21 import converter
from music21 import stream

from decitala import Decitala, FragmentTree
from pofp import dynamically_partition_onset_list, get_pareto_optimal_longest_paths

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

def _pitch_info_from_onset_range(onset_range, data):
    """
    Function that takes in (0.0, 4.0) and returns, for instance, [62, 62, 62].
    Note that n.pitch.ps or n.pitch.midi both work; ps accomadates floats which I don't need here.

    Oooo, here we actually need something a tiny bit more complicated! What if the part is playing chords.
    Assume monophonic for now. 
    """
    note_data = []
    for this_object in data:
        if _check_tuple_in_tuple_range(this_object[1], onset_range):
            note_data.append(this_object)
    
    pitches = [n[0].pitches for n in note_data]
    out = [x.midi for y in pitches for x in y]

    return out#[n[0].pitch.midi for n in note_data]

####################################################################################################

def create_database(score_path, part_num, db_name):
    """
    Function for creating a decitala and paths database in the cwd. 
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

##################### TESTING #####################
if __name__ == "__main__":
    sept_haikai_path = '/Users/lukepoeppel/Desktop/Messiaen/Sept_Haikai/1_Introduction.xml'
    liturgie_path = '/Users/lukepoeppel/Dropbox/Luke_Myke/Messiaen_Qt/Messiaen_I_Liturgie/Messiaen_I_Liturgie_de_cristal_CORRECTED.mxl'
    #create_database(score_path=liturgie_path, part_num=3, db_name="/Users/lukepoeppel/decitala_v2/liturgie_piano3_test1.db")
    #import doctest
    #doctest.testmod()


