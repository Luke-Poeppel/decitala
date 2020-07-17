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
Notes

TODO:
"""
import sqlite3 as lite

from music21 import converter
from music21 import stream

from decitala_v2 import Decitala, FragmentTree
from po_non_overlapping_onsets import partition_onset_list, get_pareto_optimal_longest_paths

def create_database(score_path, part_num):
    """
    Function for creating a decitala and paths database in the cwd. 
    """
    pass

if __name__ == "__main__":
    import doctest
    doctest.testmod()


