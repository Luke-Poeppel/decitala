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
- sideways sorted histogram with the full_id and ql_array().

NOTE:
- Want: some basic demographic information for the Fragment info for both Sept Haikai and Liturgie.
    - paths.py gives us access to the path information, but we also need access to the fragment information...
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import sqlite3 as lite

from collections import Counter

from decitala import Decitala

FONTNAME = 'Times'
FONTSIZE_TITLE = 14
FONTSIZE_LABEL = 12

decitala_path = '/Users/lukepoeppel/decitala_v2/Decitalas'
liturgie_path = '/Users/lukepoeppel/Dropbox/Luke_Myke/Messiaen_Qt/Messiaen_I_Liturgie/Messiaen_I_Liturgie_de_cristal_CORRECTED.mxl'
sept_haikai_path = '/Users/lukepoeppel/Desktop/Messiaen/Sept_Haikai/1_Introduction.xml' 

#Databases
sept_haikai0_db = '/Users/lukepoeppel/decitala_v2/sept_haikai_0.db'
sept_haikai1_db = '/Users/lukepoeppel/decitala_v2/sept_haikai_1.db'
liturgie3_db = '/Users/lukepoeppel/decitala_v2/liturgie_piano3_test1.db'
####################################################################################################
def _tala_from_string(tala_string):
    """
    '<decitala.Decitala 51_Vijaya>' -> Decitala
    """
    id_num = int(tala_string.split('_')[0])
    return Decitala.get_by_id(id_num)

def get_tala_list_from_db(db_path):
    conn = lite.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM Fragment")
    rows = cur.fetchall()

    talas = []
    for row in rows:
        name = row[2].split()[1]
        id_num = name.split('_')[0]
        talas.append(_tala_from_string(name))
    
    return talas

"""
The relevant stuff here is actually in pofp.py!
"""
def remove_single_anga_class_talas(tala_list):
    return list(filter(lambda x: x.num_anga_classes != 1, tala_list))

liturgie_talas = get_tala_list_from_db(liturgie3_db)
filtered = remove_single_anga_class_talas(liturgie_talas)

sort_filtered = sorted(filtered, key = lambda x: x.num_onsets)
#remove 4_caturthaka, 86_garugi, 95_anlarakrida
filter2 = []
for this in sort_filtered:
    if this.id_num in [4, 86, 95]:
        pass
    else:
        filter2.append(this)

print(set(filter2))

"""
FOR SATURDAY: I need the onset information, so get the data from rolling search! 
Maybe do some of the aforementioned work... move to separate module and add internal
path search method.
"""

#for x in filtered:
#    print(x, x.ql_array())
#print(Counter(filtered))
#print(_tala_from_string('121_Varied_Ragavardhana'))

#for this_tala in set(filtered):
#    print(this_tala, this_tala.num_anga_classes, this_tala.ql_array())

####################################################################################################
# Plotters
def plot_tala_histogram(db_path, title):
    mpl.style.use('seaborn')

    data = get_tala_list_from_db(db_path)
    c = Counter(data)

    xvals = [str(x.id_num) for x in c.keys()]
    #xvals = [x.name for x in c.keys()]
    yvals= c.values()
    max_count = c.most_common(1)[0][1]

    plt.figure(figsize=(7,5))

    plt.title(title + '\n (n={})'.format(len(data)), fontname=FONTNAME, fontsize=FONTSIZE_TITLE)
    plt.xlabel('Count (n)', fontname=FONTNAME, fontsize=FONTSIZE_LABEL)
    plt.ylabel('Lavignac ID', fontname=FONTNAME, fontsize=FONTSIZE_LABEL)
    
    #print()
    plt.barh(xvals, yvals)
    plt.xticks(list(range(0, max_count + 1, 1)))

    plt.show()

def plot_cross_db_tala_histogram(db1_path, db2_path, title):
    """
    Plots tala histograms for, at the moment, two database paths.  
    """
    mpl.style.use('seaborn')

    data1 = get_tala_list_from_db(db1_path)
    c1 = Counter(data1)
    data2 = get_tala_list_from_db(db2_path)
    c2 = Counter(data2)

    xvals1 = [str(x.id_num) for x in c1.keys()]
    xvals2 = [str(x.id_num) for x in c2.keys()]
    #xvals = [x.name for x in c.keys()]
    yvals1 = c1.values()
    yvals2 = c2.values()

    max_count1 = c1.most_common(1)[0][1]
    max_count2 = c2.most_common(1)[0][1]

    fig, axs = plt.subplots(2)#, figsize=(9, 6.7))

    #print(axs[0])
    axs[0].barh(xvals1, yvals1)
    axs[1].barh(xvals2, yvals2)

    #plt.figure(figsize=(7,5))
    
    '''
    plt.title(title + '\n (n={})'.format(len(data)), fontname=FONTNAME, fontsize=FONTSIZE_TITLE)
    plt.xlabel('Count (n)', fontname=FONTNAME, fontsize=FONTSIZE_LABEL)
    plt.ylabel('Lavignac ID', fontname=FONTNAME, fontsize=FONTSIZE_LABEL)
    
    #print()
    plt.barh(xvals, yvals)
    plt.xticks(list(range(0, max_count + 1, 1)))
    '''
    plt.show()

#plot_cross_db_tala_histogram(db1_path=sept_haikai0_db, db2_path=sept_haikai1_db, title='Test')
#plot_tala_histogram(db_path = sept_haikai0_db, title = 'Sept Haikai Part 0')
#plot_tala_histogram(db_path = sept_haikai1_db, title = 'Sept Haikai Part 1')

'''


for x in sept_haikai0_talas:
    print(x.ql_array())

#for x in get_tala_list_from_db(sept_haikai1_db):
    #print(x)
'''



