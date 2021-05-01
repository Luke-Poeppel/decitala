import os
import numpy as np
import pytest

from decitala.fragment import GreekFoot
from decitala.hash_table import GreekFootHashTable, DecitalaHashTable
from decitala.search import rolling_hash_search
from decitala.path_finding import dijkstra, path_finding_utils

here = os.path.abspath(os.path.dirname(__file__))
s1_fp = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"
s3_fp = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_3.xml"

@pytest.fixture
def s1_fragments():
	return rolling_hash_search(
		filepath=s1_fp,
		part_num=0,
		table=GreekFootHashTable()
	)

@pytest.fixture
def s3_fragments():
	return rolling_hash_search(
		filepath=s3_fp,
		part_num=0,
		table=GreekFootHashTable()
	)

def test_dijkstra_path_1(s1_fragments):
	source, target, best_pred = dijkstra.dijkstra_best_source_and_sink(data=s1_fragments)
	best_path = dijkstra.generate_path(
		best_pred, 
		source,
		target
	)
	path_frags = sorted([x for x in s1_fragments if x["id"] in best_path], key=lambda x: x["onset_range"][0])
	expected_fragments = [
		GreekFoot("Peon_IV"),
		GreekFoot("Peon_II"),
		GreekFoot("Amphibrach"),
		GreekFoot("Peon_IV"),
	]
	assert set(x["fragment"] for x in path_frags) == set(expected_fragments)

def test_dijkstra_path_2(s3_fragments):
	expected_fragments = [GreekFoot("Anapest"), GreekFoot("Choriamb")]
	expected_onset_ranges = [(0.0, 0.5), (0.5, 1.25)]
	
	source, target, best_pred = dijkstra.dijkstra_best_source_and_sink(data=s3_fragments)
	best_path = dijkstra.generate_path(
		best_pred, 
		source,
		target
	)
	path_frags = sorted([x for x in s3_fragments if x["id"] in best_path], key=lambda x: x["onset_range"][0])

	assert [x["onset_range"] for x in path_frags] == expected_onset_ranges
	assert set(x["fragment"] for x in path_frags) == set(expected_fragments)