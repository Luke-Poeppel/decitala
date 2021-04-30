import os
import doctest

from decitala import search, hash_table, utils
from decitala.fragment import GreekFoot
from decitala.hash_table import DecitalaHashTable

here = os.path.abspath(os.path.dirname(__file__))
filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

def test_doctests():
	assert doctest.testmod(search, raise_on_error=True)

def test_rolling_hash_search():
	res = search.rolling_hash_search(
		filepath = filepath,
		part_num = 0,
		table = hash_table.GreekFootHashTable()
	)
	assert len(res) == 18

# Also functions as an integration test with Floyd-Warshall. 
def test_shuffled_I_path_with_slur_constraint():
	path = search.path_finder(
		filepath = filepath,
		part_num=0,
		table=hash_table.GreekFootHashTable(),
		algorithm="floyd-warshall",
		slur_constraint=True
	)
	fragments = [x["fragment"] for x in path]
	analysis = [
		GreekFoot("Peon_IV"),
		GreekFoot("Iamb"),
		GreekFoot("Peon_IV"),
		GreekFoot("Peon_IV")
	]

	assert fragments == analysis

# fp = "/Users/lukepoeppel/Messiaen/Encodings/Messiaen_Qt/Messiaen_I_Liturgie/Messiaen_I_Liturgie_de_cristal_CORRECTED.mxl"
# fragments = search.rolling_hash_search(
# 	filepath=fp,
# 	part_num=3,
# 	table=DecitalaHashTable(),
# 	allow_subdivision=True
# )
# for x in fragments:
# 	print(x["fragment"], x["onset_range"], x["id"], x["mod_hierarchy_val"])