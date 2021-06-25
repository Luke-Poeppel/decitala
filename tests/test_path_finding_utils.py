import os

from decitala.search import rolling_hash_search
from decitala.path_finding import path_finding_utils
from decitala.hash_table import GreekFootHashTable

here = os.path.abspath(os.path.dirname(__file__))
st2 = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_2.xml"
st3 = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_3.xml"

def test_sources_and_sinks():
	fragments = rolling_hash_search(
		filepath=st2,
		part_num=0,
		table=GreekFootHashTable()
	)
	sources, sinks = path_finding_utils.sources_and_sinks(fragments)

	assert len(sources) == 2
	assert len(sinks) == 3

def test_sources_and_sinks_enforce_earliest_start():
	fragments = rolling_hash_search(
		filepath=st3,
		part_num=0,
		table=GreekFootHashTable()
	)
	sources, sinks = path_finding_utils.sources_and_sinks(
		fragments,
		enforce_earliest_start=True
	)

	min_onset = min(x.onset_range[0] for x in fragments)
	assert len(sources) == 2
	assert [x.onset_range[0] == min_onset for x in fragments]