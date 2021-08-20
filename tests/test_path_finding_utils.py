import os

from decitala.search import (
	rolling_hash_search,
	path_finder
)
from decitala.path_finding import path_finding_utils
from decitala.hash_table import GreekFootHashTable
from decitala.fragment import GreekFoot

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

# Also an integration test with search module.
def test_nc_106_split_extractions():
	filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_5.xml"
	path = path_finder(
		filepath=filepath,
		part_num=0,
		table=GreekFootHashTable(),
		allow_subdivision=False,
		cost_function_class=path_finding_utils.CostFunction3D(0.8, 0.1, 0.1),
		split_dict=path_finding_utils.default_split_dict(),
		enforce_earliest_start=True
	)
	all_results = rolling_hash_search(
		filepath=filepath,
		part_num=0,
		table=GreekFootHashTable(),
	)
	calculated_split = path_finding_utils.split_extractions(
		data=path,
		all_res=all_results,
		split_dict=path_finding_utils.default_split_dict()
	)
	calculated_split_fragments = [x.fragment for x in calculated_split]
	
	expected_fragments = [
		GreekFoot("Epitrite_II"),
		GreekFoot("Iamb"),
		GreekFoot("Amphimacer"),
		GreekFoot("Epitrite_II"),
		GreekFoot("Anapest"),
		GreekFoot("Anapest"),
		GreekFoot("Epitrite_II"),
		GreekFoot("Dactyl"),
		GreekFoot("Dactyl"),
		GreekFoot("Amphimacer")
	]
	assert calculated_split_fragments == expected_fragments

	calculated_split_onset_ranges = [x.onset_range for x in calculated_split]
	expected_onset_ranges = [
		(0.0, 0.875),
		(1.875, 2.25),
		(2.25, 2.875),
		(3.875, 4.75),
		(6.0, 6.5),
		(6.5, 7.0),
		(8.0, 8.875),
		(9.875, 10.375),
		(10.375, 10.875),
		(10.875, 11.5)
	]
	assert calculated_split_onset_ranges == expected_onset_ranges

def test_net_cost():
	filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_5.xml"
	path = path_finder(
		filepath=filepath,
		part_num=0,
		table=GreekFootHashTable(),
		allow_subdivision=False,
		cost_function_class=path_finding_utils.CostFunction3D(0.8, 0.1, 0.1),
		split_dict=path_finding_utils.default_split_dict(),
		enforce_earliest_start=True
	)
	assert path_finding_utils.net_cost(path) == 5.51047619047619