import os
import numpy as np
import pytest

from decitala.fragment import GreekFoot
from decitala.hash_table import GreekFootHashTable
from decitala.search import rolling_hash_search
from decitala.path_finding import floyd_warshall, path_finding_utils

here = os.path.abspath(os.path.dirname(__file__))
filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

@pytest.fixture
def s1_fragments():
	return rolling_hash_search(
		filepath=filepath,
		part_num=0,
		table=GreekFootHashTable()
	)

# Should probably get better test... Too similar to test_search path_finder example. 
def test_get_path(s1_fragments):
	distance_matrix, next_matrix = floyd_warshall.floyd_warshall(
		s1_fragments,
		verbose=False
	)
	best_source, best_sink = path_finding_utils.best_source_and_sink(s1_fragments)
	best_path = floyd_warshall.get_path(
		start=best_source,
		end=best_sink,
		next_matrix=next_matrix,
		data=s1_fragments,
		slur_constraint=True
	)
	fragments = [
		GreekFoot("Peon_IV"),
		GreekFoot("Iamb"),
		GreekFoot("Peon_IV"),
		GreekFoot("Peon_IV")
	]
	assert set(x.fragment for x in best_path) == set(fragments)