####################################################################################################
# File:     corpora_models.py
# Purpose:  Module for holding all of the SQLAlchemy models used in the decitala package for
#           included corpora.
#
# Author:   Luke Poeppel
#
# Location: NYC, 2021
####################################################################################################
import json
import os

from sqlalchemy import (
	Column,
	Integer,
	String,
	create_engine,
	ForeignKey,
)
from sqlalchemy.orm import (
	sessionmaker,
	relationship,
	backref
)
from sqlalchemy.ext.declarative import declarative_base

here = os.path.abspath(os.path.dirname(__file__))
decitala_path = os.path.dirname(os.path.dirname(here)) + "/corpora/Decitalas/"
greek_path = os.path.dirname(os.path.dirname(here)) + "/corpora/Greek_Metrics/"
prosody_path = os.path.dirname(os.path.dirname(here)) + "/corpora/Prosody/"

oiseaux_de_nouvelle_caledonie = "/Users/lukepoeppel/Messiaen/Oiseaux_De_Nouvelle_Calédonie"
ODNC_Database = "/Users/lukepoeppel/moiseaux/databases/ODNC.db"

REGIONS = {
	"NC": "Nouvelle Calédonie",
}

Base = declarative_base()

def get_session(db_path=ODNC_Database, echo=False):
	engine = create_engine(f"sqlite:////{db_path}", echo=echo)
	Base.metadata.create_all(engine)

	Session = sessionmaker(bind=engine)
	session = Session()
	return session

class DecitalaData(Base):
	"""
	SQLAlchemy model representing a decitala fragment from the encoded datasets (given in ``corpora``).
	"""
	__tablename__ = "DecitalaData"

	id = Column(Integer, primary_key=True)
	full_id = Column(String)
	name = Column(String)
	ql_array = Column(String)

class GreekFootData(Base):
	"""
	SQLAlchemy model representing a greek foot fragment from the encoded datasets (given
	in ``corpora``).
	"""
	__tablename__ = "GreekFootData"

	id = Column(Integer, primary_key=True)
	name = Column(String)
	ql_array = Column(String)

class ProsodicFragmentData(Base):
	"""
	SQLAlchemy model representing a prosodic fragment from the encoded datasets (given in ``corpora``).
	"""
	__tablename__ = "ProsodicFragmentData"

	id = Column(Integer, primary_key=True)
	name = Column(String)
	source = Column(String)
	ql_array = Column(String)

####################################################################################################
# ODNC
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

class CategoryData(Base):
	"""
	Category table of the database, (possibly) holding multiple subcategories, i.e., species.
	"""
	__tablename__ = "CategoryData"

	id = Column(Integer, primary_key=True)
	name = Column(String)
	group_number = Column(Integer)

	def __repr__(self):
		return f"<moiseaux.CategoryData {self.name}>"

class SubcategoryData(Base):
	"""
	Subcategory table of the database. Holds data for each species.
	"""
	__tablename__ = "SubcategoryData"

	id = Column(Integer, primary_key=True)
	name = Column(String)
	category_id = Column(Integer, ForeignKey("CategoryData.id"))
	category = relationship("CategoryData", backref=backref("subcategories"))
	latin = Column(String)
	local_name = Column(String, nullable=True)
	reported_size = Column(Integer)
	description = Column(String)
	locations = Column(String)

	def __repr__(self):
		return f"<moiseaux.SubcategoryData {self.name}>"

class TranscriptionData(Base):
	"""
	Transcription-level table of the database.
	"""
	__tablename__ = "TranscriptionData"

	id = Column(Integer, primary_key=True)
	name = Column(String)
	subcategory_id = Column(Integer, ForeignKey("SubcategoryData.id"))
	subcategory = relationship("SubcategoryData", backref=backref("transcriptions"))
	analysis = Column(String)
	filepath = Column(String)

	def __repr__(self):
		return f"<moiseaux.TranscriptionData {self.name}>"