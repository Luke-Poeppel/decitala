# -*- coding: utf-8 -*-
####################################################################################################
# File:     histogram.py
# Purpose:  Histogram visualization for talas found in a particular piece. Either path-dependant or
#           or net find. 
#
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
TODO:
- Decitala demographics on Sept Haikai and Liturgie

NOTE:
- As is noted in Issues, the Counter function doesn't work with GeneralFragment objects. For now, use
the Counter on the name. 
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from collections import Counter

from decitala import Decitala, FragmentTree

FONTNAME = 'Times'
FONTSIZE_TITLE = 14
FONTSIZE_LABEL = 12

####################################################################################################
        
decitala_path = '/Users/lukepoeppel/decitala_v2/Decitalas'
liturgie_path = '/Users/lukepoeppel/Dropbox/Luke_Myke/Messiaen_Qt/Messiaen_I_Liturgie/Messiaen_I_Liturgie_de_cristal_CORRECTED.mxl'
#sept_haikai_path = '/Users/lukepoeppel/Desktop/Messiaen/Sept_Haikai/1_Introduction.xml' 

tree = FragmentTree(root_path = decitala_path, frag_type = 'decitala', rep_type = 'ratio')

onset_ranges = []
for this_tala in tree.rolling_search(path = liturgie_path, part_num = 3):
    onset_ranges.append(list(this_tala))

sorted_onset_ranges = sorted(onset_ranges, key = lambda x: x[1][0])

#for x in sorted_onset_ranges:
#    print(x[0][0])

def plot_from_list(lst, title):
    """
    This will plot the count from a raw list of decitalas. Path independent. 
    x-axis: id_num (or full_id)
    y-axis: count
    """
    mpl.style.use('seaborn')
    plt.title(title, fontname=FONTNAME, fontsize=FONTSIZE_TITLE)
    plt.xlabel('id', fontname=FONTNAME, fontsize=FONTSIZE_LABEL)
    plt.ylabel('Count (n)', fontname=FONTNAME, fontsize=FONTSIZE_LABEL)

    tala_names = [x[0][0].name for x in lst]
    c = Counter(tala_names)
    
    plt.bar(c.keys(), c.values(), width=0.5)
    plt.show()

#plot_from_list(lst = sorted_onset_ranges[0:10], title = 'first 10 found talas')

def plot_from_path(path, title):
    pass


