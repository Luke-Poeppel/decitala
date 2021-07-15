import os
import doctest
import pytest

from music21 import converter
from music21 import analysis

from decitala.hm import hm_utils

here = os.path.abspath(os.path.dirname(__file__))

def test_doctests():
	assert doctest.testmod(hm_utils, raise_on_error=True)

@pytest.fixture
def fp1():
	return os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

@pytest.fixture
def fp2():
	return os.path.dirname(here) + "/tests/static/deut2290.krn"

def test_pc_counter_counts(fp1):
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
		filepath=fp1,
		part_num=0,
		return_counts=True
	)
	assert predicted == calculated

def test_pc_counter_normalized(fp1):
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
		filepath=fp1,
		part_num=0,
		return_counts=False
	)
	calculated = hm_utils.normalize_pc_counter(calculated)
	assert predicted == calculated

def test_pc_dict_to_vector(fp1):
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
		filepath=fp1,
		part_num=0,
		return_counts=False
	)
	calculated = hm_utils.normalize_pc_counter(calculated)
	calculated_vector = hm_utils.pc_dict_to_vector(calculated)
	assert list(calculated_vector) == predicted

def test_ks_diatonic(fp2):
	"""
	B- major.
	"""
	parsed = converter.parse(fp2)
	ks = analysis.discrete.KrumhanslSchmuckler()
	m21_res = ks.getSolution(parsed).tonic
	
	pc_counter_dict = hm_utils.pc_counter(
		filepath=fp2,
		part_num=0,
	)
	pc_counter_vector = hm_utils.pc_dict_to_vector(pc_counter_dict)

	major_res = hm_utils.KS_diatonic(
		pc_counter_vector,
		hm_utils.get_all_coefficients()["Major"],
		method="pearson",
		return_tonic=True
	)
	minor_res = hm_utils.KS_diatonic(
		pc_counter_vector,
		hm_utils.get_all_coefficients()["Minor"],
		method="pearson",
		return_tonic=True
	)	
	decitala_res = max([major_res, minor_res], key=lambda x: x[1][0])	

	assert m21_res.name == decitala_res[0]