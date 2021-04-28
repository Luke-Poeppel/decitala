####################################################################################################
# File:     database.py
# Purpose:  Data structure for creating and representing databases using sqlite.
#
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020 / Frankfurt, DE 2020 / NYC, 2021
####################################################################################################
import uuid
import os
import json

from sqlalchemy import (
	Column,
	String,
	Float,
	Boolean,
	Integer,
	ForeignKey,
	create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
	sessionmaker,
	relationship,
	backref,
)

from .search import rolling_hash_search
from .utils import get_logger
from .hash_table import GreekFootHashTable, MODIFICATION_HIERARCHY

Base = declarative_base()

class DatabaseException(Exception):
	pass

class CompositionData(Base):
	"""
	SQLAlchemy model representing the basic composition data for a composition.

	:param str name: name of the composition.
	:param int part_num: part number for the extraction.
	:param str local_filepath: local filepath for the searched composition. 

	TODO: could add a `search_constraint` column that stores a JSON of the search parameters. 
	"""
	__tablename__ = "CompositionData"

	id = Column(Integer, primary_key=True)

	name = Column(String)
	part_num = Column(Integer)
	local_filepath = Column(String)

	def __init__(self, name, part_num, local_filepath):
		self.name = name
		self.part_num = part_num
		self.local_filepath = local_filepath

class Extraction(Base):
	"""
	SQLAlchemy model representing a fragment extracted from a composition. 

	Parameters
	----------
	
	:param float onset_start: starting onset of the extracted fragment.
	:param float onset_stop: ending onset of the extracted fragment (onset of final object + quarter length)
	:param str fragment_type: fragment type; options currently include `decitala`, `greek_foot`, and `general_fragment`.
	:param str name: name of the fragment.
	:param str mod_type: modification type of the fragment.
	:param float ratio: ratio of the fragment's values to the values in the database. 
	:param float difference: difference between the fragment's values to the values in the database.
	:param str pitch_content: pitch content of the extracted fragment.
	:param bool is_slurred: whether the extracted fragment is spanned by a slur object. 
	"""
	__tablename__ = "Fragments"

	id = Column(Integer, primary_key=True)

	onset_start = Column(Float)
	onset_stop = Column(Float)
	
	# TODO: just make this fragment with the JSON output from FragmentEncoder. 
	fragment_type = Column(String)
	name = Column(String)
	
	mod_type = Column(String)
	ratio = Column(Float)
	difference = Column(Float)
	
	pitch_content = Column(String)
	is_slurred = Column(Boolean)

	composition_data_id = Column(Integer, ForeignKey("CompositionData.id"))
	composition_data = relationship("CompositionData", backref=backref("composition_data"))

	def __init__(
			self,
			onset_start,
			onset_stop,
			fragment_type,
			name,
			mod_hierarchy_val,
			ratio,
			difference,
			pitch_content,
			is_slurred,
		):
		self.onset_start = onset_start
		self.onset_stop = onset_stop
		self.fragment_type = fragment_type
		self.name = name
		self.mod_hierarchy_val = mod_hierarchy_val
		self.ratio = ratio
		self.difference = difference
		self.pitch_content = pitch_content
		self.is_slurred = is_slurred

def create_database(
		db_path,
		filepath,
		table,
		part_nums=[0],
		windows=list(range(2, 19)),
		extra_filter=None,
		echo=False
	):
	"""
	Function for creating a database from a single filepath. 

	:param str db_path: path to the database to be created. 
	:param str filepath: path to the score to be analyzed.
	:param list table: a :obj:`decitala.hash_table.FragmentHashTable` object. 
	:param list part_nums: parts to be analyzed.
	:param extra_filter: lambda expression on the extracted fragments. 
	:param bool echo: whether to echo the SQL calls. False by default. 
	"""
	assert os.path.isfile(filepath), DatabaseException("✗ The path provided is not a valid file.")
	assert db_path.endswith(".db"), DatabaseException("✗ The db_path must end with '.db'.")
	if os.path.isfile(db_path):
		return "That database already exists ✔"

	logger = get_logger(name=__file__, print_to_console=True)
	logger.info(f"Preparing database at {db_path}...")

	engine = create_engine(f"sqlite:////{db_path}", echo=echo)
	Base.metadata.create_all(engine)

	Session = sessionmaker(bind=engine)
	session = Session()

	filepath_name = filepath.split("/")[-1]

	for this_part in part_nums:
		data = CompositionData(
			name=filepath_name,
			part_num=this_part,
			local_filepath=filepath
		)
		session.add(data)

		res = rolling_hash_search(
			filepath=filepath,
			part_num=this_part,
			table=table,
			windows=windows
		)
		if not(res):
			return "No fragments extracted –– stopping."

		fragment_objects = []
		for this_fragment in res:
			f = Extraction(
				onset_start=this_fragment["onset_range"][0],
				onset_stop=this_fragment["onset_range"][1],
				fragment_type=this_fragment["frag_type"],
				name=this_fragment["fragment"].name,
				mod_hierarchy_val=this_fragment["mod_hierarchy_val"],
				ratio=this_fragment["factor"],
				difference=this_fragment["difference"],
				pitch_content=json.dumps(this_fragment["pitch_content"]),
				is_slurred=this_fragment["is_spanned_by_slur"]
			)
			fragment_objects.append(f)
			session.add(f)

		data.composition_data = fragment_objects
	
	session.commit()
	return

def batch_create_database(
	):
	"""
	Provide dictionary of filepath and desired part nums. 
	"""
	pass