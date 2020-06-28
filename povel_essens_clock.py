# -*- coding: utf-8 -*-
####################################################################################################
# File:     povel_essens_clock.py
# Purpose:  Implementation of the Povel and Essens process for generating the C-score a rhythm (i.e.
#           a temporal pattern). From "Perception of Temporal Patterns" (1985). 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
Algorithm:
(1) take "temporal pattern" in (array)
(2) transform into time-scale notation
(3) mark accents as 2
(3b) calculate duration (length of accented/time-scale notation) 
(4) generate all clocks;
    - longest time-scale is floor(duration/2)
    - generate all floor(duration/2) possible clocks
    - increment downwards by 1

Povel and Essens Accent Observations:
(a) relatively isolated events
(b) second tone in a cluster of two
(c) initial and final tones of a cluster consisting of >3 tones
"""
import copy
import math
import numpy as np

def transform_to_time_scale(array, as_str=False):
    """
    Transforms an array into time-scale notation.

    >>> udikshana = np.array([0.5, 1.5, 0.5, 0.5, 1.0])
    >>> transform_to_time_scale(udikshana)
    array([1, 1, 0, 0, 1, 1, 1, 0])

    >>> transform_to_time_scale(array=np.array([0.5, 0.5, 0.375, 0.375]))
    array([1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0])

    >>> gajajhampa = np.array([1.0, 0.25, 0.25, 0.375])
    >>> transform_to_time_scale(array=gajajhampa, as_str=True)
    '100000001010100'
    """
    result_pre = []
    shortest = min(array)
    if all(map(lambda x: x % shortest == 0, array)):
        result_pre = np.array([(x / shortest) for x in array])
    else:
        i = 2
        while i < 6: #this upper bound is arbitrary (something between 4 and 10 should suffice)
            if all(map(lambda x: (x % (shortest / i)).is_integer(), array)):
                result_pre = np.array([(x / (shortest / i)) for x in array])
                break
            else:
                i += 1

    result_out = []
    for this_elem in result_pre:
        if int(this_elem) == 1:
            result_out.extend([1])
        else:
            result_out.extend([1])
            result_out.extend([0] * (int(this_elem) - 1))

    if as_str==True:
        return ''.join(str(x) for x in result_out)
    else:
        return np.array(result_out)

def _find_isolated_element(array):
    """
    Returns the indices of isolated elements in a sequence.

    >>> povel_ex = np.array([1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0])
    >>> _find_isolated_element(povel_ex)
    array([3, 9])
    """
    if len(array) == 1:
        return np.array([0])

    indices = []
    i = 0 
    while i < len(array) - 1:
        if array[i] == 1:
            if i == 0 and array[i + 1] == 0:
                indices.append(i)
            elif i == len(array) - 1 and array[-1] == 1 and array[i - 1] == 0:
                indices.append(i)
            else:
                if array[i] == 1 and array[i - 1] == 0 and array[i + 1] == 0:
                    indices.append(i)
        i += 1
    
    return np.array(indices)

def _find_isolated_cluster(array):
    """
    Returns the second index of an isolated cluster of two values.

    >>> povel_ex = np.array([1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0])
    >>> _find_isolated_cluster(array=povel_ex)
    array([1])

    >>> _find_isolated_cluster(np.array([1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0]))
    array([1, 5])
    """
    i = 0
    indices = []
    while i <= len(array) - 2:
        this_window = array[i:i+2]
        if len(set(this_window)) == 1 and this_window[0] == 1:
            #potential candidate
            if i == 0 and array[2] == 0:
                indices.append(i+1)
            elif i == len(array) - 2:
                indices.append(i)
            else:
                try:
                    if array[i-1] == 0 and array[i+2] == 0:
                        indices.append(i+1)
                except IndexError:
                    pass
        i += 1

    return np.array(indices)

def _find_longer_cluster(array):
    """
    Returns the first index of an isolated cluster of length greater than >=3.

    >>> povel_ex2 = np.array([1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1])
    >>> for this_cluster in _find_longer_cluster(array=povel_ex2):
    ...     print(this_cluster)
    [16 20]
    [0 3]
    """
    indices = []
    if len(set(array)) == 1:
        indices.append(0)
    
    i = 3
    all_possibilities = []
    while i <= len(array) - 1:
        j = 0
        while j <= len(array) - i:
            this_window = array[j:j+i]
            if len(set(this_window)) == 1 and this_window[0] == 1:
                #potential candidate
                all_possibilities.append([this_window, j, j + len(this_window) - 1])
            j += 1
        i += 1

    sorted_down = sorted(all_possibilities, key=lambda x: len(x[0]), reverse=True)
    
    def _check_tuple_in_tuple_range(tup1, tup2):
        """
        Checks if tuple 1 is contained in tuple 2, e.g. (2, 4) in (1, 5)
        >>> _check_tuple_in_tuple_range((2, 4), (1, 5))
        True
        """
        if tup1[0] >= tup2[0] and tup1[0] <= tup2[1] and tup1[1] <= tup2[1]:
            return True
        else:
            return False 

    new = copy.copy(sorted_down)
    k = 0
    while k <= len(new) - 1:
        curr = new[k]
        curr_indices = tuple(curr[1:])
        l = k+1
        while l <= len(new) - 1:
            if _check_tuple_in_tuple_range(tup1=tuple(new[l][1:]), tup2=curr_indices) == True:
                del new[l]
            else:
                l += 1
        k += 1
    
    return np.array([x[1:] for x in new])

def mark_accents(array, as_str=False):
    """
    Marks accents in an array based on the three parameters set by Povel and Essens (see above).

    INPUT MUST BE TIME SCALE! 

    >>> povel_ex2 = np.array([1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0])
    >>> mark_accents(array = povel_ex2)
    array([2, 1, 1, 2, 0, 1, 2, 0, 0, 2, 0, 1, 2, 0, 0, 0, 2, 1, 1, 2, 0])

    >>> povel_ex3 = np.array([1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0])
    >>> mark_accents(array = povel_ex3)
    array([2, 1, 2, 0, 0, 0, 2, 0, 0, 2, 0, 0, 1, 2, 0, 0])
    """
    isolated_accents = _find_isolated_element(array)
    isolated_cluster = _find_isolated_cluster(array)
    long_cluster = _find_longer_cluster(array)

    new = copy.copy(array)

    for this_accent_index in isolated_accents:
        new[this_accent_index] = 2
    for this_accent_index in isolated_cluster:
        new[this_accent_index] = 2
    for this_accent_index in long_cluster:
        new[this_accent_index] = 2

    return new

def generate_all_clocks(array):
    """
    Generates all possible clocks of an array.
    Input is time-scale! 
    """
    clocks = []
    
    accented_array = mark_accents(array)
    duration = len(accented_array)
    max_unit = math.floor(duration / 2) - 1
    all_units = range(1, max_unit + 1)

    for this_unit in all_units:
        for i in range(0, this_unit):
            #clocks.append(range(i, len(accented_array), this_unit))
            clocks.append([x for x in range(i, len(accented_array), this_unit)])
    
    return np.array(clocks)

def get_ev_dict_by_array_and_clock(array, clock):
    """
    Returns the ev information for all clocks.
    Input must be accented
    {'+ev':X, '0ev':Y, '-ev':Z}
    """
    ev_dict = dict()
    pos_ev_count = 0
    zero_ev_count = 0
    neg_ev_count = 0
    for this_tick in clock:
        if array[this_tick] == 2:
            pos_ev_count += 1
        if array[this_tick] == 1:
            zero_ev_count += 1
        if array[this_tick] == 0:
            neg_ev_count += 1
    
    ev_dict['+ev'] = pos_ev_count
    ev_dict['0ev'] = zero_ev_count
    ev_dict['-ev'] = neg_ev_count

    return ev_dict

def generate_all_ev_dicts(array):
    """
    Returns a list containing all possible ev_dicts.
    Hmm... needs to have some reference to the clock...

    ({EV_DICT}, array([]))?
    """
    clocks = generate_all_clocks(array = array)
    ev_dicts = []
    for this_clock in clocks:
        ev_dicts.append(get_ev_dict_by_array_and_clock(array = array, clock = this_clock))

    return ev_dicts

'''
povel_ex3 = np.array([1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0])
for this_clock in generate_all_clocks(array = povel_ex3):
    #print(this_clock)
    pass

test_clock1 = np.array([2, 5, 8, 11])
print(get_ev_dict_by_array_and_clock(array = mark_accents(povel_ex3), clock = test_clock1))
'''
povel_ex3 = np.array([1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0])
for this_dict in generate_all_ev_dicts(array = mark_accents(povel_ex3)):
    print(this_dict)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
