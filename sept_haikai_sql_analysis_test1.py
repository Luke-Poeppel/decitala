import sqlite3 as lite
import sys

from decitala_v2 import Decitala
#from po_non_overlapping_onsets import get_pareto_optimal_longest_paths

conn = lite.connect('/Users/lukepoeppel/decitala_v.2.0/sept_haikai_test_1')

cur = conn.cursor()
cur.execute("SELECT * FROM Fragment")
rows = cur.fetchall()

for row in rows:
    print(row)




