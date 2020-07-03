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
(5) generate the ev dicts. 

Povel and Essens Accent Observations:
(a) relatively isolated events
(b) second tone in a cluster of two
(c) initial and final tones of a cluster consisting of >3 tones
"""
import copy
import math
import numpy as np

from statistics import mean

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

def extend_clock_to_fit(array, clock_unit):
    """
    Solves the problem above. 
    Note: every window should be of the length of the first window. 

    >>> povel_ex3 = np.array([1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0])
    >>> accented = mark_accents(povel_ex3)
    >>> accented
    array([1, 2, 0, 2, 0, 2, 1, 2, 0, 2, 0, 0])
    >>> for this_clock_pos in extend_clock_to_fit(array=accented, clock_unit=5):
    ...     print(this_clock_pos)
    [ 2  7 12]
    [ 3  8 13]
    [ 4  9 14]
    """
    clocks = []
    num_clicks = math.ceil(len(array) / clock_unit)
    for i in range(0, clock_unit):
        this_clock = [j for j in range(i, len(array), clock_unit)]
        if len(this_clock) != num_clicks:
            diff = num_clicks - len(this_clock)
            for _ in range(diff):
                this_clock.extend([this_clock[-1] + clock_unit])
            clocks.append(this_clock)
        else:
            pass

    return np.array(clocks)

def generate_all_clocks(array):
    """
    Generates all possible clocks of an array.
    Input is time-scale! 

    >>> povel_ex3 = np.array([1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0])
    >>> print(povel_ex3)
    [1 1 0 1 0 1 1 1 0 1 0 0]
    >>> for this_clock in generate_all_clocks(array = povel_ex3):
    ...     print(this_clock)
    [ 0  1  2  3  4  5  6  7  8  9 10 11]
    [ 0  2  4  6  8 10]
    [ 1  3  5  7  9 11]
    [0 3 6 9]
    [ 1  4  7 10]
    [ 2  5  8 11]
    [0 4 8]
    [1 5 9]
    [ 2  6 10]
    [ 3  7 11]
    [ 0  5 10]
    [ 1  6 11]
    [ 2  7 12]
    [ 3  8 13]
    [ 4  9 14]
    """
    clocks = []
    
    accented_array = mark_accents(array)
    duration = len(accented_array)
    max_unit = math.floor(duration / 2) - 1
    all_units = range(1, max_unit + 1)

    for this_unit in all_units:
        num_clicks = math.ceil(len(array) / this_unit)
        for i in range(0, this_unit):
            clock = np.array(range(i, 12, this_unit))
            if len(clock) != num_clicks:
                for this_clock in extend_clock_to_fit(array = accented_array, clock_unit = this_unit):
                    clocks.append(this_clock)
            else:
                clocks.append(clock)
    
    uniques = []
    for clock in clocks:
        if not any(np.array_equal(clock, unique_arr) for unique_arr in uniques):
            uniques.append(clock)

    return uniques

def get_ev_dict_by_array_and_clock(array, clock):
    """
    Returns the ev information for an array and clock.
    Input must be accented!
    {'+ev':X, '0ev':Y, '-ev':Z}

    >>> povel_ex3 = np.array([1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0])
    >>> for this_clock in generate_all_clocks(array=povel_ex3):
    ...     print(get_ev_dict_by_array_and_clock(array = mark_accents(povel_ex3), clock = this_clock))
    ({'+ev': 5, '0ev': 2, '-ev': 5}, array([ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11]))
    ({'+ev': 0, '0ev': 2, '-ev': 4}, array([ 0,  2,  4,  6,  8, 10]))
    ({'+ev': 5, '0ev': 0, '-ev': 1}, array([ 1,  3,  5,  7,  9, 11]))
    ({'+ev': 2, '0ev': 2, '-ev': 0}, array([0, 3, 6, 9]))
    ({'+ev': 2, '0ev': 0, '-ev': 2}, array([ 1,  4,  7, 10]))
    ({'+ev': 1, '0ev': 0, '-ev': 3}, array([ 2,  5,  8, 11]))
    ({'+ev': 0, '0ev': 1, '-ev': 2}, array([0, 4, 8]))
    ({'+ev': 3, '0ev': 0, '-ev': 0}, array([1, 5, 9]))
    ({'+ev': 0, '0ev': 1, '-ev': 2}, array([ 2,  6, 10]))
    ({'+ev': 2, '0ev': 0, '-ev': 1}, array([ 3,  7, 11]))
    ({'+ev': 1, '0ev': 1, '-ev': 1}, array([ 0,  5, 10]))
    ({'+ev': 1, '0ev': 1, '-ev': 1}, array([ 1,  6, 11]))
    ({'+ev': 1, '0ev': 1, '-ev': 1}, array([ 2,  7, 12]))
    ({'+ev': 2, '0ev': 0, '-ev': 1}, array([ 3,  8, 13]))
    ({'+ev': 1, '0ev': 0, '-ev': 2}, array([ 4,  9, 14]))
    """
    ev_dict = dict()
    pos_ev_count = 0
    zero_ev_count = 0
    neg_ev_count = 0
    for this_tick in clock:
        try:
            if array[this_tick] == 2:
                pos_ev_count += 1
            if array[this_tick] == 1:
                zero_ev_count += 1
            if array[this_tick] == 0:
                neg_ev_count += 1
        except IndexError:
            diff = this_tick - len(array) + 1
            new = np.append(array, array[:diff])

            if new[this_tick] == 2:
                pos_ev_count += 1
            if new[this_tick] == 1:
                zero_ev_count += 1
            if new[this_tick] == 0:
                neg_ev_count += 1

    ev_dict['+ev'] = pos_ev_count
    ev_dict['0ev'] = zero_ev_count
    ev_dict['-ev'] = neg_ev_count

    return (ev_dict, clock)

#############################################################
def generate_all_ev_dicts(array):
    """
    Returns a list containing all possible ev_dicts.
    """
    accented = mark_accents(array)
    clocks = generate_all_clocks(array = array)
    ev_dicts = []
    for this_clock in clocks:
        ev_dicts.append(get_ev_dict_by_array_and_clock(array = accented, clock = this_clock))

    return np.array(ev_dicts)

def c_score_from_ev_dict(ev_dict, W=4):
    '''
    Returns the c-score of a fragment from its ev dict; we use the convention of the 
    original paper and set W = 4. *Very roughly, the higher the c_score, the more complex. 
    For measuring the complexity of the talas, could take the average c-score? 
    '''
    neg_ev = ev_dict['-ev']
    zero_ev = ev_dict['0ev']

    return ((W * neg_ev) + (1 * zero_ev))

def get_average_c_score(array):
    all_c_scores = []
    for this_ev_dict in generate_all_ev_dicts(array = array):
        all_c_scores.append(c_score_from_ev_dict(ev_dict = this_ev_dict[0]))
    
    return round(mean(all_c_scores), 5)

def get_best_clock(ev_dicts, array):
    good_clocks = []
    array_length = len(array)
    for this_clock in generate_all_clocks(array=array):
        this_clock_unit = this_clock[1] - this_clock[0]
        if array_length % this_clock_unit == 0:
            good_clocks.append(this_clock)
        else:
            pass
    
    curr_min = 10
    for this_clock in good_clocks:
        this_clock_dict = get_ev_dict_by_array_and_clock(array = mark_accents(povel_ex3), clock = this_clock)
        c_score = c_score_from_ev_dict(ev_dict = this_clock_dict[0])
        if c_score < curr_min:
            curr_min = c_score
    
    #need to return the actual clock. 
    return curr_min

#povel_ex3 = np.array([1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0])
#print(get_average_c_score(array = povel_ex3))
#print(get_best_clock(ev_dicts='H', array = povel_ex3))



first_clock = {'+ev': 5, '0ev': 2, '-ev': 5}

'''
for this_clock in generate_all_clocks(array=povel_ex3):
    this_clock_dict = get_ev_dict_by_array_and_clock(array = mark_accents(povel_ex3), clock = this_clock)
    print(c_score_from_ev_dict(ev_dict = this_clock_dict[0]))
'''

#for this_clock in generate_all_clocks(array=povel_ex3):
    #print(get_ev_dict_by_array_and_clock(array = mark_accents(povel_ex3), clock = this_clock))

if __name__ == "__main__":
    import doctest
    doctest.testmod()
