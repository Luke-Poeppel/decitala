"""
Analysis work on Sept Haïkaï
"""
import matplotlib.pyplot as plt
import numpy as np

from decitala_v2 import Decitala, FragmentTree

decitala_path = '/Users/lukepoeppel/decitala_v.2.0/Decitalas'
sept_haikai = '/Users/lukepoeppel/Desktop/Sept_Haikai/1_Introduction.xml'

t = FragmentTree(root_path = decitala_path, frag_type = 'decitala', rep_type = 'ratio')

sept_haikai_onset_ranges = []
for thisTala in t.rolling_search(path = sept_haikai, part_num = 0):
	sept_haikai_onset_ranges.append(thisTala)

for x in sept_haikai_onset_ranges:
    print(x)

