import os
import pytest
import tempfile
import uuid
import doctest
import json

from sqlalchemy.ext.declarative import declarative_base

from decitala import database
from decitala.database.db_utils import get_session
from decitala.fragment import FragmentDecoder
from decitala.database import db 
from decitala.hash_table import (
	GreekFootHashTable
)

here = os.path.abspath(os.path.dirname(__file__))

def test_doctests():
	assert doctest.testmod(database, raise_on_error=True)

def test_create_database():
	with tempfile.NamedTemporaryFile() as tmpfile:
		db_path = tmpfile.name + ".db"
		db.create_database(
			db_path = db_path,
			filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_2.xml",
			table = GreekFootHashTable(),
			part_nums = [0],
		)
		base = declarative_base()
		session = get_session(db_path=db_path, base=base)

		comps = session.query(db.CompositionData).all()
		assert comps[0].name == "Shuffled_Transcription_2.xml"
		assert comps[0].part_num == 0

		extractions = session.query(db.ExtractionData).all()
		fragments = [json.loads(x.fragment, cls=FragmentDecoder) for x in extractions]
		assert [x.frag_type == "greek_foot" for x in fragments]

# def test_aggregated_pc_distribution():
# 	ct = db.Species("La Colombe Turvert")
# 	expected = [
# 		4.125,
# 		1.0,
# 		0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
# 		2.125,
# 		1.625,
# 		3.625,
# 		4.0
# 	]
# 	assert list(ct.aggregated_pc_distribution()) == expected

# 	normalized_expected = [
# 		0.25,
# 		0.06060606060606061,
# 		0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
# 		0.12878787878787878,
# 		0.09848484848484848,
# 		0.2196969696969697,
# 		0.24242424242424243
# 	]
# 	assert list(ct.aggregated_pc_distribution(normalized=True)) == normalized_expected