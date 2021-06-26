import pytest
import doctest

from decitala.path_finding import pofp
from decitala.path_finding.pofp import (
	check_break_point,
	get_break_points,
	get_pareto_optimal_longest_paths,
	partition_data_by_break_points,
	get_pareto_optimal_longest_paths
)
from decitala.fragment import (
	GeneralFragment,
	GreekFoot
)
from decitala.search import Extraction

@pytest.fixture
def fake_data():
	extraction_1 = Extraction(
		fragment=GeneralFragment(name="info1", data=[1, 2]),
		frag_type="general_fragment",
		onset_range=(0.0, 2.0),
		retrograde=False,
		factor=1.0,
		difference=0.0,
		mod_hierarchy_val=1,
		pitch_content=[None],
		is_spanned_by_slur=False,
		slur_count=0,
		slur_start_end_count=0,
		id_=1
	)
	extraction_2 = Extraction(
		fragment=GeneralFragment(name="info2", data=[1, 2]),
		frag_type="general_fragment",
		onset_range=(0.0, 4.0),
		retrograde=False,
		factor=2.0,
		difference=0.0,
		mod_hierarchy_val=1,
		pitch_content=[None],
		is_spanned_by_slur=False,
		slur_count=0,
		slur_start_end_count=0,
		id_=2
	)
	extraction_3 = Extraction(
		fragment=GeneralFragment(name="info3", data=[1, 2]),
		frag_type="general_fragment",
		onset_range=(2.0, 4.0),
		retrograde=False,
		factor=1.0,
		difference=0.25,
		mod_hierarchy_val=1,
		pitch_content=[None],
		is_spanned_by_slur=False,
		slur_count=0,
		slur_start_end_count=0,
		id_=3
	)
	extraction_4 = Extraction(
		fragment=GeneralFragment(name="info4", data=[1, 2]),
		frag_type="general_fragment",
		onset_range=(2.0, 5.75),
		retrograde=True,
		factor=1.0,
		difference=0.25,
		mod_hierarchy_val=1,
		pitch_content=[None],
		is_spanned_by_slur=False,
		slur_count=0,
		slur_start_end_count=0,
		id_=4
	)
	extraction_5 = Extraction(
		fragment=GeneralFragment(name="info5", data=[1, 2]),
		frag_type="general_fragment",
		onset_range=(2.5, 4.5),
		retrograde=False,
		factor=3.0,
		difference=0.0,
		mod_hierarchy_val=1,
		pitch_content=[None],
		is_spanned_by_slur=False,
		slur_count=0,
		slur_start_end_count=0,
		id_=5
	)
	extraction_6 = Extraction(
		fragment=GeneralFragment(name="info6", data=[1, 2]),
		frag_type="general_fragment",
		onset_range=(4.0, 5.5),
		retrograde=False,
		factor=1.0,
		difference=0.0,
		mod_hierarchy_val=1,
		pitch_content=[None],
		is_spanned_by_slur=False,
		slur_count=0,
		slur_start_end_count=0,
		id_=6
	)
	extraction_7 = Extraction(
		fragment=GeneralFragment(name="info7", data=[1, 2]),
		frag_type="general_fragment",
		onset_range=(6.0, 7.25),
		retrograde=True,
		factor=1.0,
		difference=0.25,
		mod_hierarchy_val=1,
		pitch_content=[None],
		is_spanned_by_slur=False,
		slur_count=0,
		slur_start_end_count=0,
		id_=7
	)
	return [
		extraction_1,
		extraction_2,
		extraction_3,
		extraction_4,
		extraction_5,
		extraction_6,
		extraction_7,
	]

def test_doctests():
	assert doctest.testmod(pofp, raise_on_error=True)

def test_break_point(fake_data):
	assert check_break_point(data=fake_data, i=2) == False
	assert check_break_point(data=fake_data, i=6) == True

def test_get_break_points(fake_data):
	assert get_break_points(fake_data) == [6]

def test_partition_data_by_break_points(fake_data):
	partitioned = partition_data_by_break_points(fake_data)
	assert set([x.id_ for x in partitioned[0]]) == set([1, 2, 3, 4, 5, 6])
	assert set([x.id_ for x in partitioned[1]]) == set([7])

def test_get_pareto_optimal_longest_paths(fake_data):
	possible_paths = get_pareto_optimal_longest_paths(fake_data)
	onset_ranges = [[y.onset_range for y in x] for x in possible_paths]
	assert onset_ranges == [
		[(0.0, 2.0), (2.0, 4.0), (4.0, 5.5), (6.0, 7.25)],
		[(0.0, 2.0), (2.0, 5.75), (6.0, 7.25)],
		[(0.0, 2.0), (2.5, 4.5), (6.0, 7.25)],
		[(0.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
	]