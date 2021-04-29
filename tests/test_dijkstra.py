import os
import numpy as np

from decitala.hash_table import GreekFootHashTable
from decitala.search import rolling_hash_search
from decitala.path_finding import dijkstra, path_finding_utils

here = os.path.abspath(os.path.dirname(__file__))
filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

filepath = "/Users/lukepoeppel/Messiaen/Oiseaux_De_Nouvelle_Calédonie/14_Le_Zostérops/A_Le_Zostérops/XML/Les_Zostérops_Ex114.xml"

from datetime import datetime

fragments = rolling_hash_search(
	filepath=filepath,
	part_num=0,
	table=GreekFootHashTable()
)
print(f"{len(fragments)} fragments extracted.")

source, target = 1, len(fragments) - 3#path_finding_utils.best_source_and_sink(fragments)
print("Best source and sink extracted.")

start_graph = datetime.now()
graph = path_finding_utils.build_graph(fragments, {"gap": 0.75, "onsets": 0.25})
end_graph = datetime.now()
print(f"Took {end_graph - start_graph} to build graph.")

start_dijkstra = datetime.now()
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
end_dijkstra = datetime.now()
print(f"Took {end_dijkstra - start_dijkstra} to run Dijkstra.")
# # for x in path:
# # 	print(x)
# end = datetime.now()

# print("TOTAL TIME: {}".format(end - start))