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

from collections import Counter
from scipy import stats

from music21 import converter
from music21 import stream

from decitala import Decitala, get_added_values

def decitala_from_string(tala_string):
    """
    Sqlite3 databases store this info in string form. 

    >>> decitala_from_string('<decitala.Decitala 51_Vijaya>')
    <decitala.Decitala 51_Vijaya>
    """
    new_str = tala_string.split()[1][:-1]
    return Decitala(new_str)

def number_of_tables(db_path):
    """
    Returns the number of Path tables in a database. 
    """
    conn = lite.connect(db_path)
    cur = conn.cursor()

    x = cur.execute("SELECT * FROM sqlite_master where type='table'")

    count = 0
    for y in x.fetchall():
        count += 1
    
    return (count - 1)

def number_of_paths_by_table(db_path, path_table_num):
    """
    Given a path_table_num, returns the number of paths in that particular table.
    """
    conn = lite.connect(db_path)
    cur = conn.cursor()

    path_string = "SELECT * FROM Paths_{}".format(str(path_table_num))
    cur.execute(path_string)
    rows = cur.fetchall()

    count = 0
    for row in rows:
        count += 1
    
    return count

class SubPath(object):
    """
    Object for storing information about the paths stored in Paths_i in a database. Keeps track
    of the path onsets, decitalas within it, and calculates various relevant parameters. Input is 
    a database path, a table name ("Paths_i"), and the path number in that table. Subpaths compose
    a full Path object, under the right conditions. 
    
    NOTE: the individual paths in a table are 1-indexed. 

    >>> haikai_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_0.db'
    >>> p1 = SubPath(db_path=haikai_database_path, table='Paths_2', path_num=6)
    >>> p1
    <SubPath_6: [(38.125, 40.0), (40.0, 41.75), (41.75, 45.75), (45.75, 47.625), (47.625, 48.875), (49.375, 56.875)]>
    >>> p1.path
    [(38.125, 40.0), (40.0, 41.75), (41.75, 45.75), (45.75, 47.625), (47.625, 48.875), (49.375, 56.875)]

    >>> p1.is_end_overlapping
    False
    >>> p1.total_duration
    18.25
    >>> p1.gaps()
    [0.0, 0.0, 0.0, 0.0, 0.5]
    >>> p1.total_gaps
    0.5
    >>> p1.decitalas
    [<decitala.Decitala 77_Gajajhampa>, <decitala.Decitala 53_Sama>, <decitala.Decitala 51_Vijaya>, <decitala.Decitala 77_Gajajhampa>, <decitala.Decitala 76_Jhampa>, <decitala.Decitala 8_Simhavikrama>]
    
    >>> p1.nPVI()
    [53.333333, 9.52381, 40.0, 53.333333, 14.285714, 41.111111]
    >>> p1.average_nPVI()
    35.26455

    Gap score returns the proportion of the 
    >>> p1.gap_score()
    97.33333333333333


    Using the preference rules.
    p1.score()
    51.26984
    """
    def __init__(self, db_path, table, path_num, **kwargs):
        assert path_num > 0

        self.db_path = db_path
        self.table = table
        self.path_num = path_num

        conn = lite.connect(self.db_path)
        cur = conn.cursor()

        path_string = "SELECT * FROM {}".format(table)
        cur.execute(path_string)
        rows = cur.fetchall()

        #really stupid, but this is the only thing working right now.
        #not sure how to fetch by column name; really stupid. 
        all_pitch_data = []
        for this_row in rows:
            for this_elem in this_row:
                if this_elem[0:2] == '((':
                    all_pitch_data.append(literal_eval(this_elem))
        
        lengths = []
        for x in all_pitch_data:
            count = 0
            for this_range in x:
                count += len(this_range)
            lengths.append(count)
        
        self.all_num_onset_data = sorted(lengths)

        all_averages = []
        for this_row in rows:
            each_tala_num_onsets = []
            for this_elem in this_row:
                if this_elem[0:2] == '((':
                    pitch_content = literal_eval(this_elem)
                    for this in pitch_content:
                        each_tala_num_onsets.append(len(this))
            all_averages.append(round(np.mean(each_tala_num_onsets), 6))

        self.all_averages = sorted(all_averages)

        path = []
        pitch_data = []
        all_pitch_data = []
        for i, this_row in enumerate(rows):
            ############ get onset data
            for this_elem in this_row:
                if this_elem[0:2] == '((':
                    all_pitch_data.append(literal_eval(this_elem))
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

        #all_average_num_onsets = []
        decitalas = []
        for this_range in self.path:
            for this_row in rows:
                #tala = this_row[2]
                #as_real_tala = decitala_from_string(tala)

                # get list that holds the average num onset for each row. 
                if this_range[0] == this_row[0] and this_range[1] == this_row[1]:
                    decitalas.append(this_row[2])
        
        self.decitalas = [decitala_from_string(string) for string in decitalas]
        #self.all_average_num_onsets = all_average_num_onsets

    def __repr__(self):
        return '<SubPath_{0}: {1}>'.format(str(self.path_num), str(self.path))

    def gaps(self):
        gaps = []
        i = 0
        while i < len(self.path) - 1:
            curr_range = self.path[i]
            next_range = self.path[i + 1]
            gaps.append(next_range[0] - curr_range[-1])
            i += 1

        return gaps
    
    @property
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

    @property
    def num_onsets(self):
        count = 0
        for x in self.pitch_data:
            count += len(x)
        return count

    def nPVI(self):
        nPVI_vals = []
        for this_tala in self.decitalas:
            nPVI_vals.append(this_tala.nPVI())
        
        return nPVI_vals
        
    def average_nPVI(self):
        return round(np.mean(self.nPVI()), 6)

    def average_num_onsets(self):
        return np.mean([x.num_onsets for x in self.decitalas])

    def all_pitch_content(self):
        flattened = lambda l: [item for sublist in l for item in sublist]
        return flattened(self.pitch_data)

    def annotate_score(self, score_path, part):
        """
        Annotates a given score (matching the score on which the database has been created)
        with the Path data. 
        """
        pass

    ###################### Individual Scores ######################
    def gap_score(self):
        initial_val = self.path[0][0]
        end_val = self.path[-1][-1]
        total_range = end_val - initial_val

        percentage_gap = (self.total_gaps / total_range) * 100
        
        return (100 - percentage_gap)

    def non_retrogradable_score(self):
        """
        TODO: figure out why tala.is_non_retrogradable() is behaving strangely here.
        """
        num_non_retrogradable = 0
        for this_tala in self.decitalas:
            if np.array_equal(this_tala.ql_array(), this_tala.ql_array(retrograde = True)):
                num_non_retrogradable += 1
        
        return (num_non_retrogradable / len(self.path)) * 100

    def recycling_score(self):
        """
        Proportion of decitalas in a path that repeat.

        TODO: Counter works now, fix!
        """
        names = []
        for this_tala in self.decitalas:
            names.append(this_tala.name)

        #print(Counter(names))
        total = 0
        for x in Counter(names):
            if Counter(names)[x] > 1:
                total += Counter(names)[x]

        return (total / len(self.decitalas)) * 100
    
    def average_num_onsets_per_tala_score(self):
        """
        Gets the percentile of a path by the average num_onsets for the talas within it.
        Want: average num onsets for all talas in the table. 
        """
        all_data = [len(tala.ql_array()) for tala in self.decitalas]
        avg = round(np.mean(all_data), 6) #added round -- seems to fix the problem...

        return stats.percentileofscore(self.all_averages, avg)#, avg)

    def num_onsets_score(self):
        """
        This is actually pretty cool! :-) 
        Method: get a list that is simply the sorted total number of onsets (from pitch content)
        for each path. Use stats.percentileofscore(data, this_path.total_num_onsets)
        """
        return stats.percentileofscore(self.all_num_onset_data, self.num_onsets())

    def show(self):
        """
        TODO: should definitely be able to display the file.
        """
        pass

def model2(x, weights):
    """
    Two constrains: gap_size and onset_percentile.
    (Input is Path object.)
    Try different percentages.
    """
    sums = []
    constraints = [x.gap_score(), x.num_onsets_score()]
    for w, constraint in zip(weights, constraints):
        sums.append(w * constraint)
    
    return round(sum(sums), 6)

def model3(x, weights):
    """
    Two constrains: gap_size and average_onset
    """
    sums = []
    constraints = [x.gap_score(), x.average_num_onsets_per_tala_score()]
    for w, constraint in zip(weights, constraints):
        sums.append(w * constraint)
    
    return round(sum(sums), 6)

####################################################################################################
haikai0_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_0.db'
haikai1_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_1.db'

liturgie3_database_path = '/Users/lukepoeppel/decitala_v2/liturgie_3.db'
liturgie4_database_path = '/Users/lukepoeppel/decitala_v2/liturgie_4.db'

livre_dorgue_0_path = '/Users/lukepoeppel/decitala_v2/livre_dorgue_0.db'
livre_dorgue_1_path = '/Users/lukepoeppel/decitala_v2/livre_dorgue_1.db'

'''
def sort_table_by_model3_score(db_path, path_table_num):
    conn = lite.connect(db_path)
    cur = conn.cursor()
    path_string = "SELECT * FROM Paths_{}".format(str(path_table_num))
    cur.execute(path_string)
    rows = cur.fetchall()

    paths = []
    for i in range(1, number_of_paths_by_table(db_path, path_table_num) + 1):        
        path = SubPath(table = 'Paths_{}'.format(str(path_table_num)), path_num = i, db_path = db_path)
        paths.append(path)
    
    return sorted(paths, key = lambda x: model3(x, [0.7, 0.3]), reverse=True)
'''

def get_full_model3_path(db_path, weights):
    continuous_paths = []
    for i in range(0, number_of_tables(db_path)):
        curr_path = []
        for j in range(1, number_of_paths_by_table(db_path, i) + 1):
            p = SubPath(db_path, 'Paths_{}'.format(str(i)), j)
            curr_path.append(p)
        
        sorted_paths = sorted(curr_path, key = lambda x: model3(x, weights), reverse=True)

        continuous_paths.append(sorted_paths[0])

    return continuous_paths

full = get_full_model3_path(haikai1_database_path, weights = [0.8, 0.2])
for x in full:
    print(x)
    print(x.decitalas)
    print()
'''
num onsets is not the problem
print([len(tala.ql_array()) for tala in correct.decitalas]) is not the problem...
'''

'''
correct = SubPath(haikai0_database_path, 'Paths_3', 4)
print('CORRECT')
print(correct.decitalas)
#print(correct.decitalas)
#print([len(tala.ql_array()) for tala in correct.decitalas])
#print(correct.num_onsets)
print(correct.gap_score())
print(correct.average_num_onsets_per_tala_score())
print('')

print('NOT CORRECT')
print(full[-1].decitalas)
#print([len(tala.ql_array()) for tala in full[-1].decitalas])
#print(full[-1].num_onsets)
print(full[-1].gap_score())
print(full[-1].average_num_onsets_per_tala_score())
'''

if __name__ == '__main__':
    import doctest
    doctest.testmod()




