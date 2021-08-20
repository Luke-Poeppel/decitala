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

# def test_dijkstra_gif():
# 	# fp = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"
# 	fp = "/Users/lukepoeppel/Messiaen/Encodings/Sept_Haikai/1_Introduction.xml"
# 	import uuid
# 	vis.dijkstra_gif(
# 		filepath=fp,
# 		part_num=0,
# 		table=DecitalaHashTable(),
# 		allow_subdivision=True,
# 		title="Iterated Dijkstra on Sept Haïkaï (Bois)",
# 		save_path=f"/Users/lukepoeppel/decitala/tests/dijkstra_gif_tests/dijkstra_{uuid.uuid4().hex}",
# 		show=False
# 	)
	
# print(test_dijkstra_gif())

# convert -delay 40 F_*.png -loop 0 movie.gif
