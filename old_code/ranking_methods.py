'''
Notes:

nPVI isn't totally satisfactory since there are cases where I prefer the reverse :-)
longer versus more complex...? 

one useful constraint is to search for ranges that have talas that already appeared!
'''
import numpy as np
import random

from decitala_v2 import Decitala

#random_tala_id = random.sample(range(0, 120), 5)
random_tala_id1 = [4, 24, 34, 77, 93, 16]
random_tala_id2 = [111, 21, 88, 49, 98, 7]

def get_average_nPVI(lst):
    data = []
    for this_id in lst:
        t = Decitala.get_by_id(this_id)
        data.append(t.nPVI())
    
    return np.mean(data)

print('Group 1')
print(get_average_nPVI(random_tala_id1))
print('Group 2')
print(get_average_nPVI(random_tala_id2))

'''
w_scores = []
for this_tala in talas:
    #this actually is pretty good, but should probably disregard the rule if len(set(vals)) == 1
    if len(set(this_tala.ql_array())) <= 1:
        w_scores.append([this_tala, this_tala.ql_array(), this_tala.nPVI()])
    else:
        w_scores.append([this_tala, this_tala.ql_array(), this_tala.nPVI() + len(this_tala.ql_array())])

for x in sorted(w_scores, key = lambda x: x[-1], reverse = True):
    print(x)
'''



