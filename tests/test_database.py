import os
import pytest
import tempfile

from decitala.database import (
	create_database,
	DBParser
)

here = os.path.abspath(os.path.dirname(__file__))

@pytest.fixture
def db():
	path = tempfile.NamedTemporaryFile(delete=False).name + ".db"
	create_database(
		db_path = path,
		filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_2.xml",
		part_num = 0,
		frag_types = ["decitala"],
		rep_types = ["ratio", "difference"],
		allowed_modifications = ["r", "rr", "d", "rd"],
		try_contiguous_summation = True,
		verbose = False
	)
	return DBParser(path)

def test_num_subpath_tables(db):
	assert db.num_subpath_tables == 5

def test_spanned_fragments(db):
	assert len(db.spanned_fragments()) == 0