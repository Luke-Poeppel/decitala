import os
import pytest
import tempfile
import uuid
import doctest

from decitala import database
from decitala.database.db_utils import get_session
from decitala.database.database import (
	create_database,
	CompositionData,
	ExtractionData,
)
from decitala.hash_table import (
	GreekFootHashTable
)

here = os.path.abspath(os.path.dirname(__file__))

def test_doctests():
	assert doctest.testmod(database, raise_on_error=True)

def test_create_database():
	with tempfile.NamedTemporaryFile() as tmpfile:
		db_path = tmpfile.name + ".db"
		create_database(
			db_path = db_path,
			filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_2.xml",
			table = GreekFootHashTable(),
			part_nums = [0],
		)
		session = get_session(db_path=db_path)

		comps = session.query(CompositionData).all()
		assert comps[0].name == "Shuffled_Transcription_2.xml"
		assert comps[0].part_num == 0

		frags = session.query(ExtractionData).all()
		assert [x.fragment_type == "greek_foot" for x in frags]