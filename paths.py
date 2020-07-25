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

    TODO: (potentially) I feel like it makes more sense for the __init__ to be database, table_name, path_num. 
    So it's down up rather than up down (which feels counterintuitive). 

    >>> haikai_database_path = '/Users/lukepoeppel/decitala_v.2.0/sept_haikai_test_0.db'
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
                #as_real_tala = name_from_tala_string(tala)

                # get list that holds the average num onset for each row. 
                if this_range[0] == this_row[0] and this_range[1] == this_row[1]:
                    decitalas.append(this_row[2])
        
        self.decitalas = [name_from_tala_string(string) for string in decitalas]
        #self.all_average_num_onsets = all_average_num_onsets

    def __repr__(self):
        return '<Path_{0}: {1}>'.format(str(self.path_num), str(self.path))

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

    ###################### Individual Scores ######################
    def gap_score(self):
        initial_val = self.path[0][0]
        end_val = self.path[-1][-1]
        total_range = end_val - initial_val

        percentage_gap = (self.total_gaps() / total_range) * 100
        
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
        avg = np.mean(all_data)

        return stats.percentileofscore(self.all_averages, avg)

    def num_onsets_score(self):
        """
        This is actually pretty cool! :-) 
        Method: get a list that is simply the sorted total number of onsets (from pitch content)
        for each path. Use stats.percentileofscore(data, this_path.total_num_onsets)
        """
        return stats.percentileofscore(self.all_num_onset_data, self.num_onsets())

    def score(self, weights = [0.6, 0.05, 0.05, 0.3], breakdown = False):#, 0.1]):
        """
        TODO: not at all sure why += score isn't working here; very strange.

        End-Overlapping:    30%
        Non-Retrogradable:  20%
        Average nPVI:       20%
        Recycling Rate:     20%
        Average onsets:     10%

        I think for num_onsets, we should basically (and unforunately) make a ranking of all the talas
        in the list... 
        """
        individual_scores = [self.gap_score(), 
                            self.recycling_score(),
                            self.non_retrogradable_score(),
                            #self.average_nPVI(),
                            self.num_onsets_score(),]

        l = []
        for weight, score in zip(weights, individual_scores):
            val = weight * score
            l.append(val)
        
        if not(breakdown):
            return round(sum(l), 6)
        else:
            print('*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')
            print('GAP SCORE       ({0}%): {1}'.format(weights[0] * 100, self.gap_score()))
            print('RECYCLING SCORE ({0}%): {1}'.format(weights[1] * 100, self.recycling_score()))
            print('N.R. SCORE      ({0}%): {1}'.format(weights[2] * 100, self.non_retrogradable_score()))
            print('ONSET SCORE     ({0}%): {1}'.format(weights[3] * 100, self.num_onsets_score()))
            print()
            print('SCORE            (100%): {0}'.format(self.score()))
            print('*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')
            return

    def show(self):
        """
        TODO: should definitely be able to display the file.
        """
        pass

####################################################################################################

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
    Two constrains: gap_size and average_onset + 0.0 bias
    """
    sums = []
    constraints = [x.gap_score(), x.average_num_onsets_per_tala_score()]
    for w, constraint in zip(weights, constraints):
        sums.append(w * constraint)
    
    return round(sum(sums), 6)

class FullPath(object):
    """
    Object for concatenating multiple path objects into a new path.
    """
    pass

haikai_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_1.db'

def get_model3_path():
    continuous_paths = []
    for i in range(0, 5):
        curr_path = []
        for j in range(1, 31):
            p = Path('Paths_{}'.format(str(i)), path_num = j, db_path=haikai_database_path)
            curr_path.append(p)
        
        sorted_paths = sorted(curr_path, key = lambda x: model3(x, [0.7, 0.3]), reverse=True)

        continuous_paths.append(sorted_paths[0])
    
    return continuous_paths

#good stuff...
#for x in get_model3_path():
#    print(x)
#    print(x.decitalas)
#    print()
    
####################################################################################################

# Path ranking
'''
Weight work:
End-Overlapping:    30%
Non-Retrogradable:  20%
Average nPVI:       20% // maybe don't include this! make recycling rate 30%
Recycling Rate:     20%
Average onsets:     10%

Next set:
End-Overlapping:    30%
Recycling Rate:     30%
Non-Retrogradable:  20%
Onset-percentile:   20%

Good next try: high weight for end-overlapping and recycling rate.

Fix one and change around the other ones. 
If you set it to 0 and the scores doesn't change much, that parameter doesn't matter much;
alternatively, if you set it to 0 and it completelely changes, it matters a lot. 
'''

def sorted_paths(path_table, db):
    """
    Given a database, returns a list holding the paths sorted (reverse) by score.

    TODO: nobody wants to manually go through and count the number of rows; do it manually!
    """
    conn = lite.connect(db)
    cur = conn.cursor()
    path_string = "SELECT * FROM {}".format(path_table)
    cur.execute(path_string)
    rows = cur.fetchall()

    count = len(rows)

    paths = []
    for this_path_num in list(range(1, count + 1)):
        paths.append(Path(table=path_table, path_num=this_path_num, db_path=db))

    return sorted(paths, reverse = True, key = lambda x: x.score())


if __name__ == '__main__':
    import doctest
    #doctest.testmod()




