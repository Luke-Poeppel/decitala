# -*- coding: utf-8 -*-
####################################################################################################
# File:     non_overlapping_ranges.py
# Purpose:  Non-overlapping index problem for decitala extraction.
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
import copy
import intervaltree
import sys
'''
WANT:
[(0.0, 2.0), (4.0, 5.5), (6.0, 7.25)]
[(0.0, 2.0), (2.5, 4.5), (6.0, 7.25)]
[(0.0, 2.0), (2.0, 5.75), (6.0, 7.25)]
[(0.0, 2.0), (2.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
[(0.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
'''
#test_intervals = [(6.0, 7.25)], [(4.0, 5.5)], [(4.0, 5.5), (6.0, 7.25)], [(2.5, 4.5)], [(2.5, 4.5), (6.0, 7.25)], [(2.0, 5.75)], [(2.0, 5.75), (6.0, 7.25)], [(2.0, 4.0)], [(2.0, 4.0), (6.0, 7.25)], [(2.0, 4.0), (4.0, 5.5)], [(2.0, 4.0), (4.0, 5.5), (6.0, 7.25)], [(0.0, 4.0)], [(0.0, 4.0), (6.0, 7.25)], [(0.0, 4.0), (4.0, 5.5)], [(0.0, 4.0), (4.0, 5.5), (6.0, 7.25)], [(0.0, 2.0)], [(0.0, 2.0), (6.0, 7.25)], [(0.0, 2.0), (4.0, 5.5)], [(0.0, 2.0), (4.0, 5.5), (6.0, 7.25)], [(0.0, 2.0), (2.5, 4.5)], [(0.0, 2.0), (2.5, 4.5), (6.0, 7.25)], [(0.0, 2.0), (2.0, 5.75)], [(0.0, 2.0), (2.0, 5.75), (6.0, 7.25)], [(0.0, 2.0), (2.0, 4.0)], [(0.0, 2.0), (2.0, 4.0), (6.0, 7.25)], [(0.0, 2.0), (2.0, 4.0), (4.0, 5.5)], [(0.0, 2.0), (2.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
test_intervals = [(0.0, 2.0), (0.0, 4.0), (2.5, 4.5), (2.0, 5.75), (2.0, 4.0), (6.0, 7.25), (4.0, 5.5)]

def _isInRange(num, tupleRange) -> bool:
	'''
	Given an input number and a tuple representing a range (i.e. from startVal to endVal), returns
	whether or not the input number is in that range. 

	>>> _isInRange(2.0, (2.0, 2.0))
	True
	>>> _isInRange(3.0, (2.0, 4.0))
	True
	>>> _isInRange(4.0, (2.0, 2.5))
	False
	>>> _isInRange(4.0, (3.0, 4.0))
	True
	'''
	if tupleRange[0] > tupleRange[1]:
		raise Exception('Invalid Range')
	elif tupleRange[0] == tupleRange[1] and num == tupleRange[0]:
		return True
	elif tupleRange[0] == tupleRange[1] and num != tupleRange[0]:
		return False
	else:
		if num > tupleRange[0] or num == tupleRange[0]:
			if num < tupleRange[1] or num == tupleRange[1]:
				return True
			else:
				return False
		else:
			return False

def tuple_overlap(tup1, tup2) -> bool:
    '''
    Given two tuples, returns True if they overlap by anything more than the end/start value.
    All the possible scenarios are outlined below. Assumes they're sorted by the first value.

    >>> tuple_overlap(tup1 = (1, 2), tup2 = (2, 3))
    False
    >>> tuple_overlap(tup1 = (1, 2), tup2 = (1.5, 2.5))
    True
    >>> tuple_overlap(tup1 = (1, 2), tup2 = (1, 1.5))
    True
    >>> tuple_overlap(tup1 = (1, 2), tup2 = (1.5, 2))
    True
    >>> tuple_overlap(tup1 = (1, 2), tup2 = (3, 4))
    False
    '''
    if tup1[1] == tup2[0]:
        return False
    elif tup1[0] < tup2[0] and tup1[1] > tup2[0]:
        return True
    elif tup1[0] == tup2[0]:
        return True
    elif tup1[0] < tup2[0] and tup1[1] == tup2[1]:
        return True
    elif tup1[0] < tup2[0] and tup1[1] < tup2[1]:
        return False
    
def get_all_end_overlapping_intervals(intervals):
    all_possibilities = []
    i = 0
    while i < len(intervals):
        print('FIRST PASS THROUGH')
        curr_interval = intervals[i]
        indices_of_interest = []
        j = 0
        while j < len(intervals):
            curr_all = copy.copy(intervals)
            if i == j:
                j += 1
            else:
                t = tuple_overlap(curr_interval, curr_all[j])
                if t:
                    print('HELLO!')
                    curr_all.pop(j)
                    j += 1
                else:
                    j += 1
            
            all_possibilities.append(curr_all)
        i += 1
    
    return all_possibilities

def get_all_end_overlapping_indices(lst, i, out):
	"""
	Change to make it a binary search –– this is far too slow. 

	Possible paths: 
	[(0.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
	[(0.0, 2.0), (2.5, 4.5), (6.0, 7.25)]
	[(0.0, 2.0), (2.0, 5.75), (6.0, 7.25)]
	[(0.0, 2.0), (2.0, 4.0), (4.0, 5.5), (6.0, 7.25)]

	Eliminate the waste!
	"""
	all_possibilities = []

	def _get_all_end_overlapping_indices_helper(list_in, i, out):
		r = -1
		if i == len(list_in):
			if out:
				if len(all_possibilities) == 0:
					all_possibilities.append(out)
				else:						
					all_possibilities.append(out)

			return 

		n = i + 1
		while n < len(list_in) and r > list_in[n][0]:
			n += 1
		_get_all_end_overlapping_indices_helper(list_in, n, out)

		r = list_in[i][1]
		n = i + 1

		while n < len(list_in) and r > list_in[n][0]:
			n += 1
		_get_all_end_overlapping_indices_helper(list_in, n, out + [list_in[i]])

	_get_all_end_overlapping_indices_helper(list_in = lst, i = 0, out = [])
	
	return all_possibilities

indices = [(0.0, 2.0), (0.0, 4.0), (2.5, 4.5), (2.0, 5.75), (2.0, 4.0), (6.0, 7.25), (4.0, 5.5)]
indices.sort()

for this in get_all_end_overlapping_indices(lst = indices, i = 0, out = []):
	print(this)

if __name__ == '__main__':
    import doctest
    doctest.testmod()










