import numpy as np
import pytest

from music21 import chord

from decitala.utils import (
	contiguous_summation,
	frame_to_ql_array,
	filter_single_anga_class_fragments,
	filter_sub_fragments
)

from decitala.fragment import (
	Decitala
)

@pytest.fixture
def gc2_example_data():
	data = [
		(chord.Chord(["F#2", "F3"], quarterLength=0.125), (1.625, 1.75)), 
		(chord.Chord(["F#2", "F3"], quarterLength=0.125), (1.75, 1.875)), 
		(chord.Chord(["F#2", "F3"], quarterLength=0.125), (1.875, 2.0)), 
		(chord.Chord(["F#2", "F3"], quarterLength=0.25), (2.0, 2.25))
	]
	return data

@pytest.fixture
def liturgie_opening():
	data = [
		(chord.Chord(["E-4", "B4", "E5"]), (2.0, 3.0)), 
		(chord.Chord(["E-4", "A4", "D5"]), (3.0, 4.0)), 
		(chord.Chord(["E-4", "A4", "D5"]), (4.0, 5.0)), 
		(chord.Chord(["E-4", "G4", "C5"]), (5.0, 5.5)), 
		(chord.Chord(["F#4", "B4", "C5"]), (5.5, 6.25)), 
		(chord.Chord(["E4", "A4", "C5"]), (6.25, 6.75))
	]
	return data

@pytest.fixture
def decitala_collection():
	talas = [
		{"fragment": Decitala("75_Pratapacekhara"), "mod": ('sr', 0.6666666666666666), "onset_range": (2.0, 6.25)},
		{"fragment": Decitala("93_Ragavardhana"), "mod": ('rsr', 2.0), "onset_range": (2.0, 6.75)},
		{"fragment": Decitala("Karanayati"), "mod": ('r', 1.0), "onset_range": (0.0, 1.0)},
		{"fragment": Decitala("5_Pancama"), "mod": ('r', 4.0), "onset_range": (2.0, 4.0)},
	]
	return talas

def test_contiguous_summation_same_chord(gc2_example_data):
	res = contiguous_summation(gc2_example_data)
	expected = [
		(chord.Chord(["F#2", "F3"], quarterLength=0.375), (1.625, 2.0)),
		(chord.Chord(["F#2", "F3"], quarterLength=0.25), (2.0, 2.25))
	]
	assert res[0][1] == expected[0][1]
	assert res[1][1] == expected[1][1]
	assert res[0][0].pitches == expected[0][0].pitches
	assert res[1][0].pitches == expected[1][0].pitches

def test_qls_not_change_after_cs():
	liturgie_opening = [
		(chord.Chord(["E-4", "B4", "E5"], quarterLength=1.0), (2.0, 3.0)), 
		(chord.Chord(["E-4", "A4", "D5"], quarterLength=1.0), (3.0, 4.0)), 
		(chord.Chord(["E-4", "A4", "D5"], quarterLength=1.0), (4.0, 5.0)), 
		(chord.Chord(["E-4", "G4", "C5"], quarterLength=0.5), (5.0, 5.5)), 
		(chord.Chord(["F#4", "B4", "C5"], quarterLength=0.75), (5.5, 6.25)), 
		(chord.Chord(["E4", "A4", "C5"], quarterLength=0.5), (6.25, 6.75))
	]

def test_single_anga_class_and_subtala_filtering(decitala_collection):
	original = decitala_collection
	filter_a = filter_single_anga_class_fragments(original)
	assert len(filter_a) == 2

	filter_b = filter_sub_fragments(filter_a)
	assert len(filter_b) == 1