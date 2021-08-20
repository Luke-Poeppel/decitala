import os

from unittest.mock import patch

from decitala import vis
from decitala import search
from decitala.hash_table import GreekFootHashTable, DecitalaHashTable

here = os.path.abspath(os.path.dirname(__file__))

def test_fragment_roll(monkeypatch):
	fp = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"
	path = search.path_finder(
		filepath=fp,
		part_num=0,
		table=GreekFootHashTable()
	)
	vis.fragment_roll(
		data=path,
		title="Testing fragment roll."
	)