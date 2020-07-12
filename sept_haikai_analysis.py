"""
Analysis work on Sept Haïkaï
"""
import matplotlib.pyplot as plt
import numpy as np

from decitala_v2 import Decitala, FragmentTree
from po_non_overlapping_onsets import get_pareto_optimal_longest_paths

from music21 import converter
from music21 import stream

decitala_path = '/Users/lukepoeppel/decitala_v.2.0/Decitalas'
sept_haikai = '/Users/lukepoeppel/Desktop/Messiaen/Sept_Haikai/1_Introduction.xml'

#c = converter.parse(sept_haikai)
#c.parts[0].show()

t = FragmentTree(root_path = decitala_path, frag_type = 'decitala', rep_type = 'ratio')

sept_haikai_onset_ranges = []
for thisTala in t.rolling_search(path = sept_haikai, part_num = 0):
	sept_haikai_onset_ranges.append(list(thisTala))

sorted_sept_haikai_onset_ranges = sorted(sept_haikai_onset_ranges, key = lambda x: x[1][0])

note_data = t.get_indices_of_object_occurrence(sept_haikai, 0)
for x in sorted_sept_haikai_onset_ranges:
    print(x)

print(note_data)

#partitioning is a bit annoying and complicated –– do it by hand, for now.
sept_partition_1 = sorted_sept_haikai_onset_ranges[0:12]
sept_partition_2 = sorted_sept_haikai_onset_ranges[12:38]
sept_partition_3 = sorted_sept_haikai_onset_ranges[38:47]
sept_partition_4 = sorted_sept_haikai_onset_ranges[47:62]

partitions = [sept_partition_1, sept_partition_2, sept_partition_3, sept_partition_4]

#for i, x in enumerate(get_pareto_optimal_longest_paths(sept_partition_1)):
 #   print(i, x)




'''
Want: function that returns the list of talas in a particular pareto optimal path

In a case like this, using MySQL would probably make things easier since the data in the 
columns are stored independantly... 
'''
def get_talas_per_path(data):
    '''
    Data should be in the form of rolling_window data.
    '''
    
    paths = get_pareto_optimal_longest_paths(tup_lst=[x[1] for x in data[0]])
    print(paths)


#print(get_pareto_optimal_longest_paths(tup_lst=[x[1] for x in partitions[0]]))

