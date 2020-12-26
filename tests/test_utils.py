import pytest

from music21 import chord

from decitala.utils import contiguous_summation

@pytest.fixture
def gc2_example_data():
	data = [
		(chord.Chord(["F#2", "F3"], quarterLength=0.125), (1.625, 1.75)), 
		(chord.Chord(["F#2", "F3"], quarterLength=0.125), (1.75, 1.875)), 
		(chord.Chord(["F#2", "F3"], quarterLength=0.125), (1.875, 2.0)), 
		(chord.Chord(["F#2", "F3"], quarterLength=0.25), (2.0, 2.25))
	]
	return data

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