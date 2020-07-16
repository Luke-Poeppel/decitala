# -*- coding: utf-8 -*-
####################################################################################################
# File:     paths.py
# Purpose:  Data structure for handling paths from sqlite database. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
Stores data for each pareto optimal path.
"""
from ast import literal_eval
import numpy as np
import sqlite3 as lite 

from music21 import converter
from music21 import stream

from decitala_v2 import Decitala, get_added_values

preference_rule_points = {
    'non-retrogradable' : 10,
    'end-overlapping' : 8,
    'valeur-ajoutée' : 5,
    'num_onsets' : 4
}

def name_from_tala_string(tala_string):
    """
    '<decitala.Decitala 51_Vijaya>' -> Decitala
    """
    new_str = tala_string.split()[1][:-1]
    return Decitala(new_str)

class Path(object):
    """
    Object for storing information about pareto optimal paths in a database.
    Get data by row number in the database, for now; I don't want to deal with the hassle of 
    searching for onset ranges. 1-indexed, following the table. 

    >>> haikai_database_path = '/Users/lukepoeppel/decitala_v.2.0/sept_haikai_test_5.db'
    >>> p1 = Path(table='Paths_4', path_num=4, db_path=haikai_database_path)
    >>> p1
    <Path: [(56.875, 58.625), (58.625, 62.625), (62.625, 63.875)]>
    >>> p1.path
    [(56.875, 58.625), (58.625, 62.625), (62.625, 63.875)]

    >>> p1.is_end_overlapping
    True
    >>> p1.total_duration
    7.0
    >>> p1.gaps()
    [0.0, 0.0]
    >>> p1.total_gaps()
    0.0

    >>> p1.decitalas
    [<decitala.Decitala 53_Sama>, <decitala.Decitala 51_Vijaya>, <decitala.Decitala 76_Jhampa>]
    >>> p1.nPVI()
    [9.52381, 40.0, 14.285714]
    >>> p1.average_nPVI()
    21.26984

    Using the preference rules.
    p1.score()
    51.26984
    """
    def __init__(self, table, path_num, db_path, **kwargs):
        assert path_num > 0

        self.table = table
        self.path_num = path_num
        self.db_path = db_path

        conn = lite.connect(self.db_path)
        cur = conn.cursor()

        path_string = "SELECT * FROM {}".format(table)
        cur.execute(path_string)
        rows = cur.fetchall()

        path = []
        pitch_data = []
        for i, this_row in enumerate(rows):
            if self.path_num == (i + 1):
                ######### GET DATA
                stop_index = 0
                for this_elem in this_row:
                    if this_elem == 'NULL':
                        stop_index = this_row.index(this_elem)
                        break
                    elif this_elem[0:2] == '((':
                        stop_index = this_row.index(this_elem)

                for this_elem in this_row[0:stop_index]:
                    path.append(literal_eval(this_elem))

                pitch_data = literal_eval(this_row[-1])
                ##########
                break
            else:
                pass
                
        self.path = path
        self.pitch_data = pitch_data

        #get tala data
        fragment_path_string = "SELECT * FROM Fragment"
        cur.execute(fragment_path_string)
        rows = cur.fetchall()

        decitalas = []
        for this_range in self.path:
            for this_row in rows:
                if this_range[0] == this_row[0] and this_range[1] == this_row[1]:
                    decitalas.append(this_row[2])
        
        self.decitalas = [name_from_tala_string(string) for string in decitalas]

    def __repr__(self):
        return '<Path: {}>'.format(str(self.path))

    def gaps(self):
        gaps = []
        i = 0
        while i < len(self.path) - 1:
            curr_range = self.path[i]
            next_range = self.path[i + 1]
            gaps.append(next_range[0] - curr_range[-1])
            i += 1

        return gaps
    
    def total_gaps(self):
        return sum(self.gaps())

    @property
    def is_end_overlapping(self):
        return sum(self.gaps()) == 0

    @property
    def total_duration(self):
        total_duration = 0
        i = 0
        while i < len(self.path):
            curr_range = self.path[i]
            total_duration += curr_range[1] - curr_range[0]
            i += 1
        
        return total_duration

    def nPVI(self):
        nPVI_vals = []
        for this_tala in self.decitalas:
            nPVI_vals.append(this_tala.nPVI())
        
        return nPVI_vals
        
    def average_nPVI(self):
        return round(np.mean(self.nPVI()), 5)

    def average_num_onsets(self):
        return np.mean([x.num_onsets for x in self.decitalas])

    def all_pitch_content(self):
        flattened = lambda l: [item for sublist in l for item in sublist]
        return flattened(self.pitch_data)

    #################################################################################
    def _getStrippedObjectList(self, f, p = 0):
        '''
        Returns the quarter length list of an input stream (with ties removed), but also includes 
        spaces for rests! 

        NOTE: this used to be .iter.notesAndRest, but I took it away, for now, to avoid complications.
        '''
        score = converter.parse(f)
        partIn = score.parts[p]
        objLst = []

        stripped = partIn.stripTies(retainContainers = True)
        for thisObj in stripped.recurse().iter.notes: 
            objLst.append(thisObj)

        return objLst

    def annotate_score(self, score_path, part):
        '''
        c = converter.parse(score_path)
        part = c.parts[part]

        onsets = [x[0] for x in self.path]
        '''
        indices = []
        strippedObjects = self._getStrippedObjectList(f = score_path, p = part)
        for thisObj in strippedObjects:
            indices.append((thisObj, (thisObj.offset, thisObj.offset + thisObj.quarterLength)))

        converted = converter.parse(score_path)
        part = converted.parts[0]
        onsets = [x[0] for x in self.path]
        endsets = [x[1] for x in self.path]

        #part.show()
        for this_element, this_element2 in zip(onsets, endsets):
            for x in part.flat.getElementsByOffset(this_element):
                if this_element == x.offset:
                    x.lyric = 'FOUND YOU!'
                    x.style.color = 'green'

                if this_element2 == x.offset:
                    x.lyric = 'END!'
                    x.style.color = 'red'
    
        part.show()
                
        #s = part.getElementsByOffset(onsets[0])
        #for x in s:
        #    print(x)

    def score(self):
        """
        Testing various parameters for preference rules. 
        """
        if self.is_end_overlapping:
            end_overlapping_score_pre = 100
        else:
            end_overlapping_score_pre = (self.total_gaps() / self.total_duration) * 100
        
        end_overlapping_score = 0.5 * end_overlapping_score_pre

        num_non_retrogradable = 0
        for this_tala in self.decitalas:
            if np.array_equal(this_tala.ql_array(), this_tala.ql_array(retrograde = True)):
                num_non_retrogradable += 1
        
        non_retrogradable_score_pre = (num_non_retrogradable / len(self.path)) * 100
        non_retrogradable_score = 0.3 * non_retrogradable_score_pre

        nPVI_score = 0.20 * self.average_nPVI()

        score = end_overlapping_score + non_retrogradable_score + nPVI_score
        return score

haikai_database_path = '/Users/lukepoeppel/decitala_v.2.0/sept_haikai_test_5.db'
p1 = Path(table='Paths_4', path_num=4, db_path=haikai_database_path)
#p1.annotate_score('/Users/lukepoeppel/Desktop/Messiaen/Sept_Haikai/1_Introduction.xml', 0)
#print(p1.score())

'''
for this_path_num in [1, 2, 3, 4, 5, 6]:
    print('*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-')
    path = Path(table='Paths_4', path_num=this_path_num, db_path=haikai_database_path)
    print(path, path.score())
    print(path.average_nPVI())
    #print(path, path.average_nPVI())
    print(path.decitalas)
    print()

    #print(path.all_pitch_content())
'''

################### Testing ###################
'''
First question: how can you get information from two tables simultanously? 
We need both the range information (in a mathematically readable format, hence literal_eval)
and the tala/tala modification data. 

Double parentheses indicates start of pitch content data.
'''
'''
conn = lite.connect('/Users/lukepoeppel/decitala_v.2.0/sept_haikai_test_5.db')
cur = conn.cursor()

cur.execute("SELECT * FROM Paths_4")
rows = cur.fetchall()
'''


if __name__ == '__main__':
    import doctest
    doctest.testmod()




