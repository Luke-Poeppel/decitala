import sqlite3 as lite
import sys

from ast import literal_eval

from decitala_v2 import Decitala
#from po_non_overlapping_onsets import get_pareto_optimal_longest_paths

conn = lite.connect('/Users/lukepoeppel/decitala_v.2.0/sept_haikai_test_2.db')
cur = conn.cursor()

###############
cur.execute("SELECT * FROM Paths")
rows = cur.fetchall()

def get_paths_from_database():
    paths = []
    for row in rows:
        useful_data = []
        for x in row:
            try:
                if x[0]=='(' and x[-1] == ')':
                    useful_data.append(x)
            except TypeError:
                pass

            try:
                if isinstance(float(x), float):
                    useful_data.append(str(x))
            except ValueError:
                pass
            
        joined = ','.join(useful_data)
        as_tup = list(literal_eval(joined))
        paths.append(as_tup)

    return paths

print(get_paths_from_database())

'''
def get_all_gaps():
    paths = get_paths_from_database()
    all_differences =[]
    for j, this_path in enumerate(paths):
        difference = 0
        i = 0
        while i < len(this_path) - 1:
            curr_range = this_path[i]
            next_range = this_path[i + 1]

            end_val = curr_range[-1]
            start_val = next_range[0]

            diff = start_val - end_val
            difference += diff
            i += 1

        all_differences.append((j, difference))
    
    return all_differences

def sort_by_gap_size():
    differences = get_all_gaps()
    return sorted(differences, key = lambda x: x[1])

def sort_paths_by_sorted_gaps():
    data = get_paths_from_database()
    sorted_gaps = sort_by_gap_size()

    return [data[i[0]] for i in sorted_gaps]

for x, gap in zip(sort_paths_by_sorted_gaps(), sort_by_gap_size()):
    print(x, gap)
'''

#paths = get_paths_from_database()
#differences = 

#for this_path, this_difference in zip(get_paths_from_database(), get_all_gaps()):
#    print(this_path, this_difference)
#print(get_all_gaps())
#print(len(get_all_gaps()))



