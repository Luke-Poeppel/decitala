import os
import doctest
import pytest

from decitala import search, hash_table, utils
from decitala.fragment import GreekFoot
from decitala.hash_table import DecitalaHashTable

here = os.path.abspath(os.path.dirname(__file__))

@pytest.fixture
def fp1():
	return os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

@pytest.fixture
def fp2():
	return os.path.dirname(here) + "/tests/static/Shuffled_Transcription_2.xml"

def test_doctests():
	assert doctest.testmod(search, raise_on_error=True)

def test_rolling_hash_search(fp1):
	res = search.rolling_hash_search(
		filepath = fp1,
		part_num = 0,
		table = hash_table.GreekFootHashTable()
	)
	assert len(res) == 18

def test_frame_is_spanned_by_slur_a(fp1):
	num_slurs = 0
	all_objects = utils.get_object_indices(fp1, 0)
	for this_window_size in [2, 3, 4]:
		for this_frame in utils.roll_window(all_objects, this_window_size):
			check = search.frame_is_spanned_by_slur(this_frame)
			if check == True:
				num_slurs += 1
	
	assert num_slurs == 5

def test_frame_is_spanned_by_slur_b(fp2):
	num_slurs = 0
	all_objects = utils.get_object_indices(fp2, 0)
	for this_window_size in [2, 3, 4]:
		for this_frame in utils.roll_window(all_objects, this_window_size):
			check = search.frame_is_spanned_by_slur(this_frame)
			if check == True:
				num_slurs += 1
	
	assert num_slurs == 3

# Also functions as an integration test with Floyd-Warshall. 
def test_shuffled_I_path_with_slur_constraint(fp1):
	path = search.path_finder(
		filepath = fp1,
		part_num=0,
		table=hash_table.GreekFootHashTable(),
		allow_subdivision=True,
		allow_contiguous_summation=True,
		algorithm="floyd-warshall",
		slur_constraint=True
	)
	fragments = [x["fragment"] for x in path]
	analysis = [
		GreekFoot("Peon_IV"),
		GreekFoot("Iamb"),
		GreekFoot("Peon_IV"),
		GreekFoot("Peon_IV")
	]

	assert fragments == analysis

def test_rolling_search_on_array():
	ght = hash_table.FragmentHashTable(
		datasets=["greek_foot"]
	)
	ght.load()
	example_fragment = [0.25, 0.25, 0.5, 0.25, 1.0, 2.0, 1.0]
	windows = [2, 3]
	found = search.rolling_search_on_array(ql_array=example_fragment, table=ght, windows=windows)
	assert len(found) == 9