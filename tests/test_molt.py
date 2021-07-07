import doctest
import os

from music21 import note

from decitala.hm import molt
from decitala.database.db import Transcription, Species

def test_doctests():
	assert doctest.testmod(molt, raise_on_error=True)

def test_molt_query_str_and_int():
	exstr = ["C#", "D", "G#", "E", "G", "F", "C#"]
	str_queries = molt.MOLT_query(exstr)
	str_expected = [
		molt.MOLT(mode=2, transposition=2),
		molt.MOLT(mode=7, transposition=3),
		molt.MOLT(mode=7, transposition=6)
	]
	assert set(str_expected) == set(str_queries)

	exint = [1, 2, 8, 4, 7, 5, 1]
	int_queries = molt.MOLT_query(exint)
	assert set(str_expected) == set(int_queries)

def test_molt_query_notes():
	pitches = [
		note.Note("D#4"),
		note.Note("E4"),
		note.Note("G#4"),
		note.Note("A4"),
	]
	expected = [
		molt.MOLT(3, 2),
		molt.MOLT(4, 3),
		molt.MOLT(4, 4),
		molt.MOLT(5, 4),
		molt.MOLT(6, 5),
		molt.MOLT(7, 2),
		molt.MOLT(7, 3),
		molt.MOLT(7, 4)
	]
	assert set(expected) == set(molt.MOLT_query(pitches))