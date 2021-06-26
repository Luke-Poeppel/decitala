import numpy as np
import os
import pytest
import doctest
import tempfile
import json

from collections import Counter

from music21 import chord
from music21 import converter
from music21 import note
from music21 import meter

from decitala import utils

from decitala.fragment import (
	Decitala,
	GreekFoot,
	GeneralFragment,
	FragmentEncoder
)

here = os.path.abspath(os.path.dirname(__file__))
analysis_filepath = os.path.dirname(here) + "/databases/analyses/livre_dorgue_1_analysis.json"

def test_doctests():
	assert doctest.testmod(utils, raise_on_error=True)

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

@pytest.fixture
def fp1():
	return os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

def test_carnatic_string_to_ql_array():
	ex = "Sc S | | Sc S o |c Sc o oc o | S"
	converted = np.array([1.5, 1.0, 0.5, 0.5, 1.5, 1.0, 0.25, 0.75, 1.5, 0.25, 0.375, 0.25, 0.5, 1.0])
	assert np.array_equal(utils.carnatic_string_to_ql_array(ex), converted)

def test_ql_array_to_carnatic_string():
	ex = np.array([0.25, 0.25, 1.5, 0.75, 1.0, 0.375, 0.25, 0.375, 1.0, 1.5, 0.5])
	cstring = "o o Sc |c S oc o oc S Sc |"
	assert np.array_equal(utils.ql_array_to_carnatic_string(ex), cstring)

def test_ql_array_to_greek_diacritics():
	ex = [0.25, 0.5, 0.5, 0.25, 0.5, 0.5, 0.25, 0.5, 0.25]
	gstring = "⏑ –– –– ⏑ –– –– ⏑ –– ⏑"
	assert np.array_equal(utils.ql_array_to_greek_diacritics(ex), gstring)

def test_contiguous_summation_same_chord(gc2_example_data):
	res = utils.contiguous_summation(gc2_example_data)
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
	filter_a = utils.filter_single_anga_class_fragments(original)
	assert len(filter_a) == 2

	filter_b = utils.filter_sub_fragments(filter_a)
	assert len(filter_b) == 1

def test_loader():
	loaded = utils.loader(analysis_filepath)
	fragments = set([x["fragment"] for x in loaded])
	actual = {Decitala("Laya"), Decitala("Bhagna"), Decitala("Niccanka")}

	assert fragments == actual

def test_write_analysis():
	f1 = Decitala("Lakskmica")
	f2 = GreekFoot("Peon_III")
	f3 = GeneralFragment([4.0, 4.0, 4.0, 1.0], name="weird fragment set")
	analysis = [
		{
			"fragment": f1,
			"onset_range": (3.0, 9.0)
		},
		{
			"fragment": f2,
			"onset_range": (9.5, 12.25)
		},
		{
			"fragment": f3,
			"onset_range": (12.0, 13.125)
		}
	]
	with tempfile.NamedTemporaryFile() as tmpfile:
		utils.write_analysis(
			data=analysis,
			filepath=tmpfile.name
		)
		# Reread to check proper serialization. 
		loaded = utils.loader(tmpfile.name)
		fragments = [x["fragment"] for x in loaded]
		assert set(fragments) == set([f1, f2, f3])

def test_reframe_ts():
	ex1 = meter.TimeSignature("44/32")
	ex1_res = utils.reframe_ts(ex1)
	expected_ex1 = meter.TimeSignature("11/8")
	assert ex1_res.ratioEqual(expected_ex1)

	ex2 = meter.TimeSignature("8/2")
	ex2_res = utils.reframe_ts(ex2, new_denominator=2)
	expected_ex2 = meter.TimeSignature("8/2")
	assert ex2_res.ratioEqual(expected_ex2)

	ex3 = meter.TimeSignature("8/8")
	ex3_res = utils.reframe_ts(ex3, new_denominator=16)
	expected_ex3 = meter.TimeSignature("16/16")
	assert ex3_res.ratioEqual(expected_ex3)

	ex4 = meter.TimeSignature("13/2")
	ex4_res = utils.reframe_ts(ex4)
	expected_ex4 = meter.TimeSignature("13/2")
	assert ex4_res.ratioEqual(expected_ex4)

def test_rolling_SRR(fp1):
	rolling_srr = utils.rolling_SRR(
		filepath=fp1,
		part_num=0,
		window_size=3
	)
	expected = [
		[1.0, 1.0, 1.0],
		[1.0, 1.0, 2.0],
		[1.0, 2.0, 0.5],
		[1.0, 0.5, 1.0],
		[1.0, 1.0, 1.0],
		[1.0, 1.0, 2.0],
		[1.0, 2.0, 0.5],
		[1.0, 0.5, 3.0],
		[1.0, 3.0, 0.3333333333333333],
		[1.0, 0.3333333333333333, 1.0],
		[1.0, 1.0, 1.0],
		[1.0, 1.0, 2.0]
	]
	assert rolling_srr == expected

def test_measure_divider_mode():
	fp = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"
	objs = utils.get_object_indices(
		filepath=fp,
		part_num=0,
		measure_divider_mode="str"
	)
	assert len(objs) == 3

def test_stretch_augment():
	nc_ex2 = GreekFoot("Iamb")
	stretched = utils.stretch_augment(
		ql_array=nc_ex2.ql_array(),
		factor=0.125,
		stretch_factor=0.1875
	)
	assert list(stretched) == [0.125, 0.375]