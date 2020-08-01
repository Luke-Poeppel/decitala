"""
I'm curious about whether we would be able to find talas in the birdsong transcriptions
if we concatenate contiguous single-anga class rhythms... *Perfect* example is what Messiaen
does with Varied Ragavardhana. Omg this would be so cool. 
"""
decitala_path = '/Users/lukepoeppel/decitala_v2/Decitalas'

import numpy as np

from decitala import Decitala
from trees import FragmentTree, rolling_search2, get_by_ql_list2

ratio_tree = FragmentTree(root_path=decitala_path, frag_type='decitala', rep_type = 'ratio')
difference_tree = FragmentTree(root_path=decitala_path, frag_type='decitala', rep_type = 'difference')

uguiso_9_2 = np.array([0.375, 0.375, 0.25, 0.25]) ####### OMG!!!!!! TURANGALILA!!!!!!!!!!
nobitaki_96 = np.array([0.25, 0.125, 0.125, 0.25, 0.125, 0.125])#, 0.125, 0.125, 0.25])
nobitaki_96_2 = np.array([0.125, 0.125, 0.125, 0.125, 0.25])
#nobitaki_96_2 = np.array([0.25, 0.125, 0.125, 0.25])
#nobitaki_96_2 = np.array([0.25, 0.125, 0.125, 0.25])

#nobitaki_97 = np.array([0.625, 0.25, 0.125, 0.125, 0.25])



print(get_by_ql_list2(np.array([1.0, 1.0, 1.0, 0.5, 0.75, 0.5]), ratio_tree, difference_tree))
print(get_by_ql_list2(uguiso_9_2, ratio_tree, difference_tree))
print(get_by_ql_list2(nobitaki_96, ratio_tree, difference_tree))
print(get_by_ql_list2(nobitaki_96_2, ratio_tree, difference_tree))

print('')

francois = np.array([1.25, 1.25, 1, 0.75, 1.0, 0.5, 0.25, 0.5, 1.0])

#p30_flute = np.array([0.125, 0.25, 0.25, 0.5 + 0.375 + 0.25, 0.25 + 0.375, 0.25, 0.25])
#print(get_by_ql_list2(p30_flute, ratio_tree, difference_tree))

#print(get_by_ql_list2(nobitaki_97, ratio_tree, difference_tree))

#for this_tala in ratio_tree.all_named_paths_of_length_n(5):
    #ql = this_tala.ql_array()
    #print(this_tala, ql)


for i, this_tala in enumerate(ratio_tree.all_named_paths()):
    if i == 0:
        pass
    else:
        ql = this_tala.ql_array()
        rat = this_tala.successive_ratio_list()

        if len(ql) < 4:
            pass
        else:
            if ql[0] == ql[1] and ql[2] < ql[1] and ql[3] < ql[2]:
                print(this_tala, ql)#this_tala.successive_ratio_list())


