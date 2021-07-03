import os
import doctest

from decitala.hm import hm_utils

here = os.path.abspath(os.path.dirname(__file__))
filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

def test_doctests():
	assert doctest.testmod(hm_utils, raise_on_error=True)

def test_pc_counter_counts():
	predicted = { # checked 06-26-21
		0: 0, # correct
		1: 2, # correct
		2: 0, # correct
		3: 1, # correct
		4: 2, # correct
		5: 3, # correct
		6: 2, # correct
		7: 0, # correct
		8: 4, # correct
		9: 2, # correct
		10: 0, # correct
		11: 0 # correct
	}
	calculated = hm_utils.pc_counter(
		filepath=filepath,
		part_num=0,
		return_counts=True
	)
	assert predicted == calculated

def test_pc_counter_normalized():
	highest_time = 2.75 # sum of all the qls below.
	predicted = { # checked 06-26-21
		0: 0,
		1: (0.25 + 0.125) / highest_time,
		2: 0,
		3: (0.25) / highest_time,
		4: (0.125 + 0.25) / highest_time,
		5: (0.125 + 0.125 + 0.125) / highest_time,
		6: (0.125 + 0.25) / highest_time,
		7: 0,
		8: (0.125 + 0.375 + 0.125 + 0.125) / highest_time,
		9: (0.125 + 0.125) / highest_time,
		10: 0,
		11: 0
	}
	calculated = hm_utils.pc_counter(
		filepath=filepath,
		part_num=0,
		return_counts=False
	)
	calculated = hm_utils.normalize_pc_counter(calculated)
	assert predicted == calculated

def test_pc_dict_to_vector():
	highest_time = 2.75 # sum of all the qls below.
	normalized_results = { # checked 06-26-21
		0: 0,
		1: (0.25 + 0.125) / highest_time,
		2: 0,
		3: (0.25) / highest_time,
		4: (0.125 + 0.25) / highest_time,
		5: (0.125 + 0.125 + 0.125) / highest_time,
		6: (0.125 + 0.25) / highest_time,
		7: 0,
		8: (0.125 + 0.375 + 0.125 + 0.125) / highest_time,
		9: (0.125 + 0.125) / highest_time,
		10: 0,
		11: 0
	}
	predicted = [
		normalized_results[0],
		normalized_results[1],
		normalized_results[2],
		normalized_results[3],
		normalized_results[4],
		normalized_results[5],
		normalized_results[6],
		normalized_results[7],
		normalized_results[8],
		normalized_results[9],
		normalized_results[10],
		normalized_results[11],
	]
	calculated = hm_utils.pc_counter(
		filepath=filepath,
		part_num=0,
		return_counts=False
	)
	calculated = hm_utils.normalize_pc_counter(calculated)
	calculated_vector = hm_utils.pc_dict_to_vector(calculated)
	assert list(calculated_vector) == predicted