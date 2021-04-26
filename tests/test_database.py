import os
import pytest
import tempfile
import uuid

from decitala.database import (
	create_database,
)
from decitala.hash_table import GreekFootHashTable

# print(
# 	create_database(
# 		db_path=f"/Users/lukepoeppel/decitala/decitala/tests/siff-{uuid.uuid4().hex}.db", 
# 		filepath="/Users/lukepoeppel/Messiaen/Oiseaux_De_Nouvelle_Calédonie/2_LOiseau_Moine/A_LOiseau_Moine/XML/LOiseau_Moine_Ex22.xml",
# 		datasets=[GreekFootHashTable],
# 	)
# )

# here = os.path.abspath(os.path.dirname(__file__))

# @pytest.fixture
# def db():
# 	path = tempfile.NamedTemporaryFile(delete=False).name + ".db"
# 	create_database(
# 		db_path = path,
# 		filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_2.xml",
# 		part_num = 0,
# 		frag_types = ["decitala"],
# 		rep_types = ["ratio", "difference"],
# 		allowed_modifications = ["r", "rr", "d", "rd"],
# 		try_contiguous_summation = True,
# 		verbose = False
# 	)
# 	return DBParser(path)