import numpy as np
import pytest

from decitala.trees import (
	FragmentTree,
	filter_data,
	get_by_ql_array
)
from decitala.fragment import GeneralFragment

@pytest.fixture
def tala_ratio_tree():
	ratio_tree = FragmentTree(frag_type='decitala', rep_type='ratio')
	return ratio_tree

@pytest.fixture
def tala_difference_tree():
	difference_tree = FragmentTree(frag_type='decitala', rep_type='difference')
	return difference_tree

@pytest.fixture
def fake_fragment_dataset():
	g1 = GeneralFragment([3.0, 1.5, 1.5, 0.75, 0.75])
	g2 = GeneralFragment([1.5, 1.0])
	g3 = GeneralFragment([0.75, 0.5, 0.75])
	g4 = GeneralFragment([0.25, 0.25, 0.5])
	g5 = GeneralFragment([0.75, 0.5])
	g6 = GeneralFragment([0.5, 1.0, 2.0, 4.0])
	g7 = GeneralFragment([1.5, 1.0, 1.5])
	g8 = GeneralFragment([1.0, 1.0, 2.0])
	g9 = GeneralFragment([1.0, 0.5, 0.5, 0.25, 0.25])
	g10 = GeneralFragment([0.25, 0.5, 1.0, 2.0])

	return [g1, g2, g3, g4, g5, g6, g7, g8, g9, g10]

@pytest.fixture
def grand_corbeau_examples():
	"""
	These are classic examples of contiguous summation. 
	"""
	from music21 import chord
	phrase_1 = [(chord.Chord(["F#2", "F3"]), (0.0, 0.125)), (chord.Chord(["F#2", "F3"]), (0.125, 0.25)), (chord.Chord(["E-3", "D4"]), (0.25, 0.375)), (chord.Chord(["A2", "A-3>"]) (0.375, 0.625))]
	phrase_2 = [(chord.Chord(["F#2", "F3"]), (1.625, 1.75)), (chord.Chord(["F#2", "F3"]), (1.75, 1.875)), (chord.Chord(["F#2", "F3"]), (1.875, 2.0)), (chord.Chord(["F#2", "F3"]), (2.0, 2.25))]
	phrase_3 = [(chord.Chord(["F#2", "F3"]), (2.75, 2.875)), (chord.Chord(["F#2", "F3"]), (2.875, 3.0)), (chord.Chord(["F#2", "F3"]), (3.0, 3.125)), (chord.Chord(["E-3", "D4"]), (3.125, 3.25)), (chord.Chord(["A2", "A-3"]), (3.25, 3.5))]

def test_filter(fake_fragment_dataset):
	filtered = filter_data(fake_fragment_dataset)
	expected = [
		fake_fragment_dataset[4], # [0.75, 0.5]
		fake_fragment_dataset[2], # [0.75, 0.5, 0.75]
		fake_fragment_dataset[3], # [0.25, 0.25, 0.5]
		fake_fragment_dataset[9], # [0.25, 0.5, 1.0, 2.0]
		fake_fragment_dataset[8], # [1.0, 0.5, 0.5, 0.25, 0.25]
	]
	assert set(filtered) == set(expected)

def test_livre_dorgue_talas(tala_ratio_tree, tala_difference_tree):
	laya = [1.0, 0.5, 1.5, 1.5, 1.5, 1.0, 1.5, 0.25, 0.25, 0.25] #ratio
	bhagna = [0.125, 0.125, 0.125, 0.125, 0.25, 0.25, 0.375] #ratio
	niccanka = [0.75, 1.25, 1.25, 1.75, 1.25, 1.25, 1.25, 0.75] #difference
	
	laya_search = get_by_ql_array(laya, ratio_tree=tala_ratio_tree, difference_tree=tala_difference_tree)
	bhagna_search = get_by_ql_array(bhagna, ratio_tree=tala_ratio_tree, difference_tree=tala_difference_tree)
	niccanka_search = get_by_ql_array(niccanka, ratio_tree=tala_ratio_tree, difference_tree=tala_difference_tree)

	assert laya_search[0].name == "106_Laya"
	assert bhagna_search[0].name == "116_Bhagna"
	assert niccanka_search[1][1] == 0.25

def test_varied_ragavardhana(tala_ratio_tree):
	varied_ragavardhana = np.array([1.0, 1.0, 1.0, 0.5, 0.75, 0.5])
	searched = get_by_ql_array(varied_ragavardhana, ratio_tree=tala_ratio_tree, allowed_modifications=["r", "sr", "rsr"])
	assert searched[0].name, searched[1] == ("93_Ragavardhana", ("rsr", 2.0))
	
def test_contiguous_summation(tala_ratio_tree, tala_difference_tree):
	pass