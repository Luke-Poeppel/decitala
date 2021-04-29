import os
import numpy as np
import pytest

from decitala.fragment import GreekFoot
from decitala.hash_table import GreekFootHashTable
from decitala.search import rolling_hash_search
from decitala.path_finding import dijkstra, path_finding_utils

here = os.path.abspath(os.path.dirname(__file__))
filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

@pytest.fixture
def s1_fragments():
	return rolling_hash_search(
		filepath=filepath,
		part_num=0,
		table=GreekFootHashTable()
	)

def test_dijkstra(s1_fragments):
	source = s1_fragments[0]
	target = s1_fragments[-3]

	dist, pred = dijkstra.dijkstra(
		data=s1_fragments,
		source=source,
		target=target,
	)
	best_path = dijkstra.generate_path(
		pred, 
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