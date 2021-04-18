import os

from decitala.hash_table import GreekFootHashTable
from decitala.search import rolling_hash_search
from decitala.path_finding import dijkstra

here = os.path.abspath(os.path.dirname(__file__))
filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

fragments = rolling_hash_search(
    filepath,
    0,
    GreekFootHashTable()
)


dpf = dijkstra.dijkstra(
    data=fragments,
    source = fragments[1],
    weights = {0.7, 0.3}
)
print(dpf)