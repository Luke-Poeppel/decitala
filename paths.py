# -*- coding: utf-8 -*-
####################################################################################################
# File:     paths.py
# Purpose:  Data structure for handling path from sqlite database. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
Stores data for each pareto optimal path.
"""
import numpy as np
import sqlite3 as lite 

from decitala_v2 import Decitala

class Path(object):
    """
    """
    def __init__(self, data, db, **kwargs):
        pass

################### Testing ###################
conn = lite.connect('/Users/lukepoeppel/decitala_v.2.0/sept_haikai_test_2.db')
cur = conn.cursor()

cur.execute("SELECT * FROM Paths")
rows = cur.fetchall()

for row in rows:
    print(row)


