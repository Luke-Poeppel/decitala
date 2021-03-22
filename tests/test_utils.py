import numpy as np
import os
import pytest

from collections import Counter

from music21 import chord
from music21 import converter
from music21 import note

from decitala.utils import (
	contiguous_summation,
	frame_to_ql_array,
	filter_single_anga_class_fragments,
	filter_sub_fragments,
	roll_window,
	get_object_indices,
	frame_is_spanned_by_slur,
	frame_to_ql_array,
	contour_to_prime_contour,
	loader
)

from decitala.fragment import (
	Decitala
)

here = os.path.abspath(os.path.dirname(__file__))
analysis_filepath = os.path.dirname(here) + "/databases/analyses/livre_dorgue_1_analysis.json"

# Frame data
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

# Fragment data
@pytest.fixture
def decitala_collection():
	talas = [
		{"fragment": Decitala("75_Pratapacekhara"), "mod": ('sr', 0.6666666666666666), "onset_range": (2.0, 6.25)},
		{"fragment": Decitala("93_Ragavardhana"), "mod": ('rsr', 2.0), "onset_range": (2.0, 6.75)},
		{"fragment": Decitala("Karanayati"), "mod": ('r', 1.0), "onset_range": (0.0, 1.0)},
		{"fragment": Decitala("5_Pancama"), "mod": ('r', 4.0), "onset_range": (2.0, 4.0)},
	]
	return talas

# Score data
@pytest.fixture
def example_transcriptions():
	fp1 = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"
	fp2 = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_2.xml"
	return fp1, fp2

@pytest.fixture
def example_frame():
	frame = (
		(note.Note("C#"), (3.625, 3.625)), 
		(note.Note("E"), (3.625, 3.875)), 
		(note.Note("E"), (3.875, 4.0)), 
		(note.Note("F#"), (4.0, 4.25))
	)
	return frame

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

def test_frame_is_spanned_by_slur_a(example_transcriptions):
	example_transcription_1 = example_transcriptions[0]
	num_slurs = 0
	all_objects = get_object_indices(example_transcription_1, 0)
	for this_window_size in [2, 3, 4]:
		for this_frame in roll_window(all_objects, this_window_size):
			check = frame_is_spanned_by_slur(this_frame)
			if check == True:
				num_slurs += 1
	
	assert num_slurs == 5

def test_frame_is_spanned_by_slur_b(example_transcriptions):
	example_transcription_2 = example_transcriptions[1]
	num_slurs = 0
	all_objects = get_object_indices(example_transcription_2, 0)
	for this_window_size in [2, 3, 4]:
		for this_frame in roll_window(all_objects, this_window_size):
			check = frame_is_spanned_by_slur(this_frame)
			if check == True:
				num_slurs += 1
	
	assert num_slurs == 3

# Examples from the Schultz article.
def test_prime_contour():
	contour_1 = [2, 4, 1, 5, 0, 6, 3]
	contour_2 = [2, 1, 3, 0]

	assert np.array_equal(contour_to_prime_contour(contour_1), np.array([2, 4, 1, 5, 0, 6, 3]))
	assert np.array_equal(contour_to_prime_contour(contour_2), np.array([2, 1, 3, 0]))

def test_loader():
	loaded = loader(analysis_filepath)
	fragments = set([x[0] for x in loaded])
	actual = {Decitala("Laya"), Decitala("Bhagna"), Decitala("Niccanka")}

	assert fragments == actual