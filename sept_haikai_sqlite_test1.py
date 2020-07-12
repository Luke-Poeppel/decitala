"""
Testing the creation of an sqlite3 database for sept haikai.
"""
import numpy as np
import re
import sqlite3 as lite

from ast import literal_eval
from decitala_v2 import Decitala, FragmentTree
from po_non_overlapping_onsets import get_pareto_optimal_longest_paths

decitala_path = '/Users/lukepoeppel/decitala_v.2.0/Decitalas'
sept_haikai = '/Users/lukepoeppel/Desktop/Messiaen/Sept_Haikai/1_Introduction.xml'

def name_from_tala_string(tala_string):
    """
    '<decitala.Decitala 51_Vijaya>' -> Decitala
    """
    new_str = tala_string.split()[1][:-1]
    return Decitala(new_str)

t = FragmentTree(root_path = decitala_path, frag_type = 'decitala', rep_type = 'ratio')

sept_haikai_onset_ranges = []
for thisTala in t.rolling_search(path = sept_haikai, part_num = 0):
	sept_haikai_onset_ranges.append(list(thisTala))

sorted_sept_haikai_onset_ranges = sorted(sept_haikai_onset_ranges, key = lambda x: x[1][0])
sept_partition_1 = sorted_sept_haikai_onset_ranges[0:12]

#### pitch information for this stream

pitches_full = t.get_indices_of_object_occurrence(sept_haikai, 0)
#print(pitches_full[0:18])

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

#example data point is range = (0.0, 4.0)
#function that takes in (0.0, 4.0) and returns [(<music21.note.Note F>, (0.0, 1.5)), (<music21.note.Note F>, (1.5, 2.5)), (<music21.note.Note F>, (2.5, 4.0))]
# Likely just the midi tones, n.pitch.ps or n.pitch.midi; ps accomadates floats which I don't really need here.

def pitch_info_from_onset_range(onset_range, data):
    note_data = []
    for this_object in data:
        if _check_tuple_in_tuple_range(this_object[1], onset_range):
            note_data.append(this_object)
    
    return [n[0].pitch.midi for n in note_data]

#print(pitch_info_from_onset_range(onset_range=(0.0, 4.0), data=pitches_full))

conn = lite.connect('sept_haikai_test_3.db')
with conn:
    cur = conn.cursor()
    cur.execute("CREATE TABLE Fragment (Onset_Start REAL, Onset_Stop REAL, Tala BLOB, Mod TEXT, Factor INT)")

    for x in sept_partition_1:
        cur.execute("INSERT INTO Fragment VALUES({0}, {1}, '{2}', '{3}', {4})".format(x[1][0], x[1][1], x[0][0], x[0][1][0], x[0][1][1]))

    cur.execute("SELECT * FROM Fragment")
    rows = cur.fetchall()
    onset_data = []
    for row in rows:
        onset_data.append((row[0], row[1]))
    
    #paths
    pareto_optimal_paths = get_pareto_optimal_longest_paths(onset_data)
    lengths = [len(path) for path in pareto_optimal_paths]
    longest_path = max(lengths)

    columns = ['Onset_Range_{}'.format(i) for i in range(1, longest_path + 1)]
    columns_declaration = ', '.join('%s BLOB' % c for c in columns)
    #newer = columns_declaration + ', Avg_nPVI REAL, Pitch_Content BLOB'
    newer = columns_declaration + ', Pitch_Content BLOB'

    cur.execute("CREATE TABLE Paths (%s)" % newer)
    for path in pareto_optimal_paths:
        #Get nPVI information for the path.
        cur.execute("SELECT * FROM Fragment")
        rows = cur.fetchall()

        nPVI_vals = []
        pitch_content = []

        for this_range in path:
            pitch_content.append(pitch_info_from_onset_range(this_range, pitches_full))
            for row in rows:
                if this_range[0] == row[0] and this_range[1] == row[1]:
                    tala = name_from_tala_string(row[2])
                    nPVI_vals.append(tala.nPVI())
        
        avg_nPVI = np.mean(nPVI_vals)
        flattened = [note for tala in pitch_content for note in tala]
        #formatted_pitch_content = '(' + ', '.join(map(str, flattened)) + ')'
        formatted_pitch_content = str(tuple([tuple(sublist) for sublist in pitch_content]))

        #format the pitch content as one continous string.

        if len(path) == longest_path:
            data = []
            for this_range in path:
                data.append('{0}'.format(this_range))
            
            mid = "', '".join(data)
            post = "INSERT INTO Paths VALUES('" + mid + "', '{}')".format(formatted_pitch_content)
            cur.execute(post)
        else:
            diff = longest_path - len(path)
            data = []
            for this_range in path:
                data.append('{0}'.format(this_range))
            
            mid = "', '".join(data)
            nulls = ["'NULL'"] * diff
            post_nulls = ", ".join(nulls)
            new = "INSERT INTO Paths VALUES('{0}', {1}, '{2}')".format(mid, post_nulls, formatted_pitch_content)
            cur.execute(new)

if __name__ == '__main__':
    import doctest
    doctest.testmod()


