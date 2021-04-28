import os
import pytest
import tempfile
import uuid

from decitala.database import (
	create_database,
)
from decitala.hash_table import (
	GreekFootHashTable
)

here = os.path.abspath(os.path.dirname(__file__))

def test_create_database():
	with tempfile.NamedTemporaryFile() as tmpfile:
		create_database(
			db_path = tmpfile.name + ".db",
			filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_2.xml",
			table = GreekFootHashTable(),
			part_nums = [0],
		)