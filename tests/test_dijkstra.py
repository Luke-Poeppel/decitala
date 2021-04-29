import os

from decitala.hash_table import GreekFootHashTable
from decitala.search import rolling_hash_search
from decitala.path_finding import dijkstra, path_finding_utils

here = os.path.abspath(os.path.dirname(__file__))
filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

fragments = rolling_hash_search(
	filepath=filepath,
	part_num=0,
	table=GreekFootHashTable()
)

source = 12 #fragments[0]
target = 17 #fragments[-3]

graph = path_finding_utils.build_graph(fragments, {"gap": 0.75, "onsets": 0.25})

d, p = dijkstra.dijkstra(
	data=graph,
	source=source,
	target=target,
)

path_frags = dijkstra.generate_path(
	p, 
	source,
	target
)

path = sorted([x for x in fragments if x["id"] in path_frags], key=lambda x: x["onset_range"][0])
for x in path:
	print(x)
# path = dijkstra.reconstruct_standard_path(
# 	data=fragments,
# 	dist=dist,
# 	prev=prev,
# 	source=source,
# 	target=target,
# )
# print(path)