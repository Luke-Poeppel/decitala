import os
import doctest
import pytest

from decitala import search, hash_table, utils
from decitala.fragment import GreekFoot, Decitala
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

def test_rolling_hash_search_num_fragments(fp1):
	res = search.rolling_hash_search(
		filepath = fp1,
		part_num = 0,
		table = hash_table.GreekFootHashTable(),
		allow_subdivision=False,
		allow_contiguous_summation=False
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

# This also functions as an integration test with Floyd-Warshall. 
def test_shuffled_I_path_with_slur_constraint():#fp1):
	path = search.path_finder(
		filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml",
		part_num=0,
		table=hash_table.GreekFootHashTable(),
		allow_subdivision=True,
		allow_contiguous_summation=True,
		algorithm="floyd-warshall",
		slur_constraint=True
	)
	fragments = [x.fragment for x in path]
	expected_fragments = [
		GreekFoot("Peon_IV"),
		GreekFoot("Iamb"),
		GreekFoot("Peon_IV"),
		GreekFoot("Peon_IV")
	]

	onset_ranges = [x.onset_range for x in path]
	expected_onset_ranges = [
		(0.0, 0.625),
		(0.875, 1.25),
		(1.25, 1.875),
		(2.375, 3.0)
	]
	assert fragments == expected_fragments
	assert onset_ranges == expected_onset_ranges

def test_rolling_search_on_array():
	ght = hash_table.FragmentHashTable(
		datasets=["greek_foot"]
	)
	ght.load()
	example_fragment = [0.25, 0.25, 0.5, 0.25, 1.0, 2.0, 1.0]
	windows = [2, 3]
	found = search.rolling_search_on_array(ql_array=example_fragment, table=ght, windows=windows)
	assert len(found) == 9

@pytest.fixture
def extraction():
	return search.Extraction(
		fragment=Decitala("Gajajhampa"),
		frag_type="decitala",
		onset_range=(0.25, 0.75),
		retrograde=False,
		factor=1.0,
		difference=0.25,
		mod_hierarchy_val=3,
		contiguous_summation=False,
		pitch_content=[(61,), (62,), (65,), (69,)],
		is_spanned_by_slur=True,
		id_=43
	)

class Test_Extraction:	

	def test_fragment(self, extraction):
		assert extraction.fragment == Decitala("Gajajhampa")

	def test_onset_range(self, extraction):
		assert extraction.onset_range == (0.25, 0.75)

	def test_retrograde(self, extraction):
		assert extraction.retrograde == False

	def test_factor(self, extraction):
		assert extraction.factor == 1.0

	def test_factor(self, extraction):
		assert extraction.difference == 0.25

	def test_mod_hierarchy_val(self, extraction):
		assert extraction.mod_hierarchy_val == 3

	def test_contiguous_summation(self, extraction):
		assert extraction.contiguous_summation == False

	def test_pitch_content(self, extraction):
		assert extraction.pitch_content == [(61,), (62,), (65,), (69,)]

	def test_is_spanned_by_slur(self, extraction):
		assert extraction.is_spanned_by_slur == True

	def test_id(self, extraction):
		assert extraction.id_ == 43