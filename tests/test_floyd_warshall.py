import os
import numpy as np

from decitala.hash_table import GreekFootHashTable
from decitala.search import rolling_hash_search
from decitala.path_finding import floyd_warshall, path_finding_utils

here = os.path.abspath(os.path.dirname(__file__))
filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

filepath = "/Users/lukepoeppel/Messiaen/Oiseaux_De_Nouvelle_Calédonie/14_Le_Zostérops/A_Le_Zostérops/XML/Les_Zostérops_Ex114.xml"

fragments = rolling_hash_search(
	filepath=filepath,
	part_num=0,
	table=GreekFootHashTable()
)
print(f"{len(fragments)} fragments extracted.")

from datetime import datetime

start_matrix = datetime.now()
distance_matrix, next_matrix = floyd_warshall.floyd_warshall(
	fragments,
	weights={
		"gap": 0.75,
		"onsets": 0.25
	},
	verbose=False
)
end_matrix = datetime.now()
print(f"Took {end_matrix - start_matrix} to build matrix.")

fw_start = datetime.now()
best_source, best_sink = path_finding_utils.best_source_and_sink(fragments)
best_path = floyd_warshall.get_path(
	start=best_source,
	end=best_sink,
	next_matrix=next_matrix,
	data=fragments,
	slur_constraint=False
)
fw_end = datetime.now()
print(f"Took {fw_end - fw_start} to run FW.")

# 	for x in best_path:
# 		print(x)

# 	print("----------------------------------")

