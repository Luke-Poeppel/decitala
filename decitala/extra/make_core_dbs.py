import json
import natsort
import os
import unidecode

from music21 import converter
from music21 import note

from decitala.database.corpora_models import (
	GreekFootData,
	DecitalaData,
	ProsodicFragmentData
)
from decitala.database.db_utils import get_session

here = os.path.abspath(os.path.dirname(__file__))
decitala_path = os.path.dirname(os.path.dirname(here)) + "/corpora/Decitalas/"
greek_path = os.path.dirname(os.path.dirname(here)) + "/corpora/Greek_Metrics/"
prosody_path = os.path.dirname(os.path.dirname(here)) + "/corpora/Prosody/"

def _make_corpora_database(echo):
	abspath_databases_directory = os.path.abspath("./databases/")
	session = get_session(db_path=os.path.join(abspath_databases_directory, "FRAGMENT_DATABASE.db"))

	for this_file in natsort.natsorted(os.listdir(decitala_path)):
		# Will use the utils function eventually. Annoying bug.
		split = this_file.split("_")
		if len(split) == 2:
			full_id = split[0]
		elif len(split) >= 3:
			if len(split[1]) == 1:  # e.g. ["80", "B", "..."]
				full_id = "_".join([split[0], split[1]])
			else:
				full_id = split[0]

		converted = converter.parse(os.path.join(decitala_path, this_file))
		ql_array = json.dumps([x.quarterLength for x in converted.flat.getElementsByClass(note.Note)])
		decitala = DecitalaData(
			full_id=full_id,
			name=this_file[:-4],
			ql_array=ql_array
		)
		session.add(decitala)

	for this_file in os.listdir(greek_path):
		converted = converter.parse(os.path.join(greek_path, this_file))
		ql_array = json.dumps([x.quarterLength for x in converted.flat.getElementsByClass(note.Note)])
		greek_foot = GreekFootData(
			name=this_file[:-4],
			ql_array=ql_array
		)
		session.add(greek_foot)

	for this_dir in os.listdir(prosody_path):
		if this_dir == "README.md":
			continue
		subdir = os.path.join(prosody_path, this_dir)
		for this_file in os.listdir(subdir):
			converted = converter.parse(os.path.join(subdir, this_file))
			ql_array = json.dumps([x.quarterLength for x in converted.flat.getElementsByClass(note.Note)])
			prosodic_fragment = ProsodicFragmentData(
				name=unidecode.unidecode(this_file[:-4]),
				source=unidecode.unidecode(this_dir),
				ql_array=ql_array
			)
			session.add(prosodic_fragment)

	session.commit()