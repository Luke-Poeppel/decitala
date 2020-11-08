"""
I'm curious about whether we would be able to find talas in the birdsong transcriptions
if we concatenate contiguous single-anga class rhythms... *Perfect* example is what Messiaen
does with Varied Ragavardhana. Omg this would be so cool. 
"""
decitala_path = '/Users/lukepoeppel/decitala_v2/Decitalas'

import numpy as np

from decitala import Decitala
from trees import FragmentTree, rolling_search, rolling_search_on_array, get_by_ql_array

uguiso_9_2 = np.array([0.375, 0.375, 0.25, 0.25]) ####### OMG!!!!!! TURANGALILA!!!!!!!!!!
nobitaki_96 = np.array([0.25, 0.125, 0.125, 0.25, 0.125, 0.125])#, 0.125, 0.125, 0.25])
nobitaki_96_2 = np.array([0.125, 0.125, 0.125, 0.125, 0.25])
#nobitaki_96_2 = np.array([0.25, 0.125, 0.125, 0.25])
#nobitaki_96_2 = np.array([0.25, 0.125, 0.125, 0.25])

#nobitaki_97 = np.array([0.625, 0.25, 0.125, 0.125, 0.25])

'''
print(get_by_ql_list2(np.array([1.0, 1.0, 1.0, 0.5, 0.75, 0.5]), ratio_tree, difference_tree))
print(get_by_ql_list2(uguiso_9_2, ratio_tree, difference_tree))
print(get_by_ql_list2(nobitaki_96, ratio_tree, difference_tree))
print(get_by_ql_list2(nobitaki_96_2, ratio_tree, difference_tree))

print('')
'''
#francois = np.array([1.25, 1.25, 1, 0.75, 1.0, 0.5, 0.25, 0.5, 1.0])
#francois_11 = np.array([0.5, 1.0, 0.5, 0.25, 1.5])

#print(get_by_ql_array(np.array([0.5, 0.75, 0.5, 1.5]), ratio_tree, difference_tree))
'''
for data in rolling_search_on_array(francois, ratio_tree, difference_tree):
    print(data[0], data[1], data[0].ql_array())
'''

#p30_flute = np.array([0.125, 0.25, 0.25, 0.5 + 0.375 + 0.25, 0.25 + 0.375, 0.25, 0.25])
#print(get_by_ql_list2(p30_flute, ratio_tree, difference_tree))

#print(get_by_ql_list2(nobitaki_97, ratio_tree, difference_tree))

#for this_tala in ratio_tree.all_named_paths_of_length_n(5):
    #ql = this_tala.ql_array()
    #print(this_tala, ql)

###################################

# Saint François testing


ratio_tree = FragmentTree(data_path=decitala_path, frag_type='decitala', rep_type = 'ratio')
difference_tree = FragmentTree(data_path=decitala_path, frag_type='decitala', rep_type = 'difference')

francois_1 = '/Users/lukepoeppel/Desktop/Francois_1.xml'
francois_2 = '/Users/lukepoeppel/Desktop/Francois_2.xml'

candor = '/Users/lukepoeppel/Desktop/VI_Candor_est_lucis_aeternae.xml'
transfiguration_1 = np.array([0.5, 0.5, 0.5, 0.75, 0.75, 0.75, 0.25])
transfiguration_2 = np.array([0.75, 0.75, 0.75, 1.0, 1.0, 1.0, 0.25])
transfiguration_3 = np.array([1.0, 1.0, 1.0, 1.25, 1.25, 1.25, 0.25])
transfiguration_4 = np.array([1.25, 1.25, 1.25, 1.5, 1.5, 1.5, 0.25])

from decitala import successive_ratio_array, successive_difference_array
print(successive_difference_array(transfiguration_1))
print(successive_difference_array(transfiguration_2))
print(successive_difference_array(transfiguration_3))
print(successive_difference_array(transfiguration_4))

#print(get_by_ql_array(transfiguration_1, ratio_tree, difference_tree))
#print(get_by_ql_array(transfiguration_2, ratio_tree, difference_tree))


for this_tala in ratio_tree.all_named_paths():
    if this_tala.num_onsets == 8:# and this_tala.is_non_retrogradable:
        print(this_tala, this_tala.ql_array())



'''
for this_tala in rolling_search(candor, 6, ratio_tree, difference_tree):
    tala = this_tala[0][0]
    if tala.num_anga_classes == 1:
        pass
    elif tala.num_onsets == 2:
        pass
    else:
        print(tala.name, tala.ql_array())
'''
'''
for this_tala in rolling_search(francois_2, 0, ratio_tree, difference_tree):
    tala = this_tala[0][0]
    if tala.num_anga_classes == 1 or tala.num_onsets == 2:
        pass
    else:
        print(tala, tala.ql_array())

'''


