import os

from decitala.hash_table import GreekFootHashTable
from decitala.search import rolling_hash_search
from decitala.path_finding import dijkstra

here = os.path.abspath(os.path.dirname(__file__))
filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

fragments = rolling_hash_search(
	filepath=filepath,
	part_num=0,
	table=GreekFootHashTable()
)

source = fragments[0]
target = fragments[-3]

# dist, prev = dijkstra.dijkstra(
# 	data=fragments,
# 	source=source,
# 	target=target,
# 	weights={"gap": 0.75, "onsets": 0.25}
# )
# path = dijkstra.reconstruct_standard_path(
# 	data=fragments,
# 	dist=dist,
# 	prev=prev,
# 	source=source,
# 	target=target,
# )
# print(path)