####################################################################################################
# File:     make_core_dbs.py
# Purpose:  File for creating the core databases for the package (fragment and ODNC dbs).
#
# Author:   Luke Poeppel
#
# Location: Kent, 2021
####################################################################################################
import json
import natsort
import os
import unidecode

from music21 import converter
from music21 import note

from .database.corpora_models import (
	GreekFootData,
	DecitalaData,
	ProsodicFragmentData,
	TranscriptionData,
	SubcategoryData,
	CategoryData,
	get_engine,
	get_session
)
from .utils import (
	get_logger,
	loader
)
from .fragment import FragmentEncoder

here = os.path.abspath(os.path.dirname(__file__))
decitala_path = os.path.dirname(os.path.dirname(here)) + "/corpora/Decitalas/"
greek_path = os.path.dirname(os.path.dirname(here)) + "/corpora/Greek_Metrics/"
prosody_path = os.path.dirname(os.path.dirname(here)) + "/corpora/Prosody/"

oiseaux_de_nouvelle_caledonie = "/Users/lukepoeppel/Messiaen/Oiseaux_De_Nouvelle_Calédonie"

REGIONS = {
	"NC": "Nouvelle Calédonie",
}

logger = get_logger(name=__file__)

def make_corpora_database(echo=False):
	abspath_databases_directory = os.path.abspath("./databases/")
	engine = get_engine(
		filepath=os.path.join(abspath_databases_directory, "FRAGMENT_DATABASE.db"),
		echo=echo
	)
	session = get_session(engine=engine)

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

def serialize_species_info(filepath):
	expected_tags = {
		"group",
		"name",
		"local_name",
		"latin",
		"locations",
		"datetimes",
		"reported_size",
		"description"
	}
	species_json = dict()
	with open(filepath, "r") as f:
		lines = list(line for line in (l.strip() for l in f) if line)  # noqa Ignores newlines
		i = 0
		while i < len(lines):
			if lines[i].startswith("description"):
				species_json["description"] = lines[i + 1:]
				break

			split = lines[i].split("=")
			if split[0] == "group":
				species_json["group"] = int(split[1])
			if split[0] == "locations":  # separated by comma (if multiple)
				split_loc = split[1].split(",")
				species_json["locations"] = split_loc
			elif split[0] == "datetimes":
				split_dat = split[1].split(";")  # separated by semicolon (if multiple)
				species_json["datetimes"] = split_dat
			else:
				if split[0] not in expected_tags:
					raise Exception(f"The tag: {split[0]} is unexpected.")
				else:
					species_json[split[0]] = split[1]
			i += 1

		existing_tags = set(species_json.keys())
		diff = expected_tags - existing_tags
		for remaining_tag in diff:
			species_json[remaining_tag] = None

	return json.dumps(species_json, ensure_ascii=False)

def make_ODNC_database(db_path):
	session = get_session(db_path)

	dirs = os.listdir(oiseaux_de_nouvelle_caledonie)
	for i, directory in enumerate(dirs):
		if directory == "ODNC_Engravings.pdf":
			continue

		category_split = directory.split("_")
		category_name = " ".join(category_split[1:])
		category_group_number = int(category_split[0])

		category = CategoryData(
			name=category_name,
			group_number=category_group_number
		)
		logger.info(category)
		session.add(category)
		subcategory_objects = []
		for this_subgroup in os.listdir(os.path.join(oiseaux_de_nouvelle_caledonie, directory)):
			subgroup_path = os.path.join(oiseaux_de_nouvelle_caledonie, directory, this_subgroup)
			for this_file_or_directory in os.listdir(subgroup_path):
				if this_file_or_directory.endswith(".txt"):
					info_path = os.path.join(subgroup_path, this_file_or_directory)
					subgroup_info = json.loads(serialize_species_info(info_path))

					subgroup_name = subgroup_info["name"]
					subgroup_latin = subgroup_info["latin"]
					subgroup_local_name = subgroup_info["local_name"]
					subgroup_reported_size = subgroup_info["reported_size"]
					subgroup_description = json.dumps(subgroup_info["description"], ensure_ascii=False)
					subgroup_locations = json.dumps(subgroup_info["locations"])

					subcategory = SubcategoryData(
						name=subgroup_name,
						latin=subgroup_latin,
						local_name=subgroup_local_name,
						reported_size=subgroup_reported_size,
						description=subgroup_description,
						locations=subgroup_locations
					)
					session.add(subcategory)
					subcategory_objects.append(subcategory)
				else:
					pass

			transcriptions_dir_path = os.path.join(subgroup_path, "XML")
			analyses_dir_path = os.path.join(subgroup_path, "Analyses")
			transcription_objects = []
			for this_transcription in os.listdir(transcriptions_dir_path):
				serialized = None
				for this_file in os.listdir(analyses_dir_path):
					if this_file.endswith(".json"):
						if this_transcription.split("_")[-1].split(".")[0] == this_file.split("_")[-1].split(".")[0]:
							analysis = loader(os.path.join(analyses_dir_path, this_file))
							serialized = json.dumps(analysis, cls=FragmentEncoder)
							break

				transcription = TranscriptionData(
					name=this_transcription.split("_")[-1][:-4],
					analysis=serialized,
					filepath=os.path.join(transcriptions_dir_path, this_transcription),
				)
				session.add(transcription)
				transcription_objects.append(transcription)

			subcategory.transcriptions = transcription_objects
		category.subcategories = subcategory_objects

	session.commit()