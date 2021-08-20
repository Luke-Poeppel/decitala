import os
import numpy as np
import pytest

from decitala.fragment import GreekFoot
from decitala.hash_table import GreekFootHashTable, DecitalaHashTable
from decitala.search import rolling_hash_search, path_finder
from decitala.path_finding import dijkstra, path_finding_utils

here = os.path.abspath(os.path.dirname(__file__))
s1_fp = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"
s3_fp = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_3.xml"
s4_fp = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_4.xml"
bach_fp = os.path.dirname(here) + "/tests/static/bwv67.7.mxl"

@pytest.fixture
def s1_fragments():
	return rolling_hash_search(
		filepath=s1_fp,
		part_num=0,
		table=GreekFootHashTable(),
		allow_subdivision=False
	)

@pytest.fixture
def s3_fragments():
	return rolling_hash_search(
		filepath=s3_fp,
		part_num=0,
		table=GreekFootHashTable()
	)

@pytest.fixture
def s4_fragments():
	return rolling_hash_search(
		filepath=s4_fp,
		part_num=0,
		table=GreekFootHashTable()
	)

def test_dijkstra_path_1(s1_fragments):
	source, target, best_pred = dijkstra.dijkstra_best_source_and_sink(
		data=s1_fragments,
		cost_function_class=path_finding_utils.CostFunction3D(0.8, 0.1, 0.1)
	)
	best_path = dijkstra.generate_path(
		best_pred, 
		source,
		target
	)
	path_frags = sorted([x for x in s1_fragments if x.id_ in best_path], key=lambda x: x.onset_range[0])

	expected_fragments = [
		GreekFoot("Peon_IV"),
		GreekFoot("Iamb"),
		GreekFoot("Peon_IV"),
		GreekFoot("Iamb"),
		GreekFoot("Peon_IV"),
	]
	expected_onset_ranges = [
		(0.0, 0.625),
		(0.875, 1.25),
		(1.25, 1.875),
		(1.875, 2.375),
		(2.375, 3.0)
	]
	assert set(x.fragment for x in path_frags) == set(expected_fragments)
	assert [x.onset_range for x in path_frags] == expected_onset_ranges

def test_dijkstra_path_2(s3_fragments):
	expected_fragments = [GreekFoot("Anapest"), GreekFoot("Choriamb")]
	expected_onset_ranges = [(0.0, 0.5), (0.5, 1.25)]
	
	source, target, best_pred = dijkstra.dijkstra_best_source_and_sink(data=s3_fragments)
	best_path = dijkstra.generate_path(
		best_pred, 
		source,
		target
	)
	path_frags = sorted([x for x in s3_fragments if x.id_ in best_path], key=lambda x: x.onset_range[0])

	assert [x.onset_range for x in path_frags] == expected_onset_ranges
	assert set(x.fragment for x in path_frags) == set(expected_fragments)

def test_dijkstra_path_3(s4_fragments):
	expected_fragment = GreekFoot("Peon_IV")
	source, target, best_pred = dijkstra.dijkstra_best_source_and_sink(data=s4_fragments)
	best_path = dijkstra.generate_path(
		best_pred, 
		source,
		target
	)
	path_frags = sorted([x for x in s4_fragments if x.id_ in best_path], key=lambda x: x.onset_range[0])
	assert len(path_frags) == 1
	assert path_frags[0].fragment == expected_fragment

def test_dijkstra_best_source_and_sink():
	exact_bach_frags = rolling_hash_search(
		filepath=bach_fp,
		part_num=0,
		table=DecitalaHashTable(exact=True),
	)
	source, target, best_pred = dijkstra.dijkstra_best_source_and_sink(data=exact_bach_frags)
	assert source == target

def test_naive_dijkstra_path(s1_fragments):
	path = dijkstra.naive_dijkstra_path(
		data=s1_fragments,
		source=s1_fragments[0],
		target=s1_fragments[-2]
	)
	
	path = sorted([x for x in s1_fragments if x.id_ in path], key=lambda x: x.onset_range[0])
	assert path[0] == s1_fragments[0]
	assert path[-1] == s1_fragments[-2]