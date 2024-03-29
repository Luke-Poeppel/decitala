import os
import doctest
import pytest

from collections import Counter

from decitala import search, utils
from decitala.fragment import GreekFoot, Decitala
from decitala.hash_table import (
	FragmentHashTable,
	DecitalaHashTable,
	GreekFootHashTable
)
from decitala.path_finding.path_finding_utils import CostFunction3D

here = os.path.abspath(os.path.dirname(__file__))

@pytest.fixture
def fp1():
	return os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

@pytest.fixture
def fp2():
	return os.path.dirname(here) + "/tests/static/Shuffled_Transcription_2.xml"

@pytest.fixture
def fp3():
	return os.path.dirname(here) + "/tests/static/Shuffled_Transcription_3.xml"

@pytest.fixture
def povel_essen_example():
	return os.path.dirname(here) + "/tests/static/deut2290.krn"

@pytest.fixture
def liturgie_reduction():
	return os.path.dirname(here) + "/databases/liturgie_reduction.xml"

@pytest.fixture
def s1_res(fp1):
	return search.rolling_hash_search(
		filepath = fp1,
		part_num = 0,
		table = GreekFootHashTable(),
		allow_subdivision=False,
		allow_contiguous_summation=False
	)

def test_doctests():
	assert doctest.testmod(search, raise_on_error=True)

class TestRollingHashSearch:

	def test_num_fragments(self, s1_res):
		assert len(s1_res) == 27

	def test_id(self, s1_res):
		assert s1_res[0].id_ == 8

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

@pytest.fixture
def extraction():
	return search.Extraction(
		fragment=Decitala("Gajajhampa"),
		onset_range=(0.25, 0.75),
		retrograde=False,
		factor=1.0,
		difference=0.25,
		mod_hierarchy_val=3,
		contiguous_summation=False,
		pitch_content=[(61,), (62,), (65,), (69,)],
		is_spanned_by_slur=True,
		slur_count=1,
		slur_start_end_count=1,
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

	def test_slur_count(self, extraction):
		assert extraction.slur_count == 1

	def test_slur_start_end_count(self, extraction):
		assert extraction.slur_start_end_count == 1

	def test_id(self, extraction):
		assert extraction.id_ == 43

# This also functions as an integration test with Floyd-Warshall. 
def test_shuffled_I_path_with_slur_constraint():
	path = search.path_finder(
		filepath=os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml",
		part_num=0,
		table=GreekFootHashTable(),
		allow_subdivision=False,
		allow_contiguous_summation=False,
		algorithm="floyd-warshall",
		slur_constraint=True
	)
	fragments = [x.fragment for x in path]
	onset_ranges = [x.onset_range for x in path]
	slur_start_end_counts = [x.slur_start_end_count for x in path]

	expected_fragments = [
		GreekFoot("Peon_IV"),
		GreekFoot("Iamb"),
		GreekFoot("Peon_IV"),
		GreekFoot("Iamb"),
		GreekFoot("Peon_IV")
	]
	expected_onset_ranges = [
		(0.0, 0.625),
		(0.875, 1.25),
		(1.25, 1.875),
		(1.875, 2.375),
		(2.375, 3.0)
	]
	expected_slur_start_end_counts = [2, 2, 2, 2, 2]

	assert fragments == expected_fragments
	assert onset_ranges == expected_onset_ranges
	assert slur_start_end_counts == expected_slur_start_end_counts

def test_povel_essen_dijkstra(povel_essen_example):
	custom_ght = GreekFootHashTable()
	custom_ght.load(allow_stretch_augmentation=False)
	path = search.path_finder(
		filepath=povel_essen_example,
		part_num=0,
		table=custom_ght,
		allow_subdivision=False,
		allow_contiguous_summation=False,
		algorithm="dijkstra",
		slur_constraint=False
	)
	assert len(path) == 1
	assert path[0].fragment == GreekFoot("Tribrach") # see ms. 8-9.  

def test_rolling_search_on_array():
	ght = FragmentHashTable(
		datasets=["greek_foot"]
	)
	ght.load()
	example_fragment = [0.25, 0.25, 0.5, 0.25, 1.0, 2.0, 1.0]
	windows = [2, 3]
	found = search.rolling_search_on_array(ql_array=example_fragment, table=ght, windows=windows)
	assert len(found) == 9

def test_found_liturgie_fragments(liturgie_reduction):
	path = search.rolling_hash_search(
		filepath=liturgie_reduction,
		part_num=0,
		table=DecitalaHashTable(),
		allow_subdivision=True,
	)
	fragments = [x.fragment for x in path]
	counted = Counter(fragments)

	new_path = []
	for x in path:
		if x.fragment in {Decitala("Ragavardhana"), Decitala("Lakskmica"), Decitala("Candrakala")}:
			new_path.append(x)

	assert counted[Decitala("Ragavardhana")] == 10
	assert counted[Decitala("Candrakala")] == 10
	assert counted[Decitala("Lakskmica")] == 9

def test_slur_data(fp3):
	path = search.path_finder(
		filepath=fp3,
		part_num=0,
		table=GreekFootHashTable()
	)
	frame_spanned_by_slur = [x.is_spanned_by_slur for x in path]
	slur_counts = sum([x.slur_count for x in path])
	slur_start_end_counts = [x.slur_start_end_count for x in path]

	expected_frame_is_spanned_by_slur = [True, False]
	expected_slur_counts = 2
	expected_slur_start_end_counts = [2, 1]

	assert frame_spanned_by_slur == expected_frame_is_spanned_by_slur
	assert slur_counts == expected_slur_counts
	assert slur_start_end_counts == expected_slur_start_end_counts