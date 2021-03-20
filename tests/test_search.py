import os

from decitala import search, hash_table, utils
from decitala.fragment import GreekFoot

here = os.path.abspath(os.path.dirname(__file__))
filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

def test_shuffled_I_path_with_slur_constraint():
	path = search.path_finder(
		filepath = filepath,
		part_num=0,
		frag_type="greek_foot",
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