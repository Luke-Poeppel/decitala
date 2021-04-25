# -*- coding: utf-8 -*-
####################################################################################################
# File:     database.py
# Purpose:  Data structure for creating and representing databases using sqlite.
#
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020 / Frankfurt, DE 2020 / NYC, 2021
####################################################################################################
import uuid

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

Base = declarative_base()

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

class Fragment(Base):
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
			mod_type,
			ratio,
			difference,
			pitch_content,
			is_slurred,
		):
		self.onset_start = onset_start
		self.onset_stop = onset_stop
		self.fragment_type = fragment_type
		self.name = name
		self.mod_type = mod_type
		self.ratio = ratio
		self.difference = difference
		self.pitch_content = pitch_content
		self.is_slurred = is_slurred

def create_database_test(filepath, echo=False):
	"""
	Function for creating a database. 
	"""
	engine = create_engine(f"sqlite:////{filepath}", echo=echo)
	Base.metadata.create_all(engine)

	Session = sessionmaker(bind=engine)
	session = Session()

	c1 = CompositionData(
		name="BWV66.6",
		part_num=0,
		local_filepath="/some/local/dir"
	)
	session.add(c1)

	c2 = CompositionData(
		name="BWV77.7",
		part_num=0,
		local_filepath="/some/other/dir"
	)
	session.add(c2)
	
	f1 = Fragment(
		onset_start=1.0,
		onset_stop=2.0,
		fragment_type="decitala",
		name="Ragavardhana",
		mod_type="r",
		ratio=1.5,
		difference=0.0,
		pitch_content="(60, 62, 64, 66, 68)",
		is_slurred=True
	)
	f2 = Fragment(
		onset_start=1.0,
		onset_stop=2.0,
		fragment_type="decitala",
		name="Dvitiya",
		mod_type="r",
		ratio=1.5,
		difference=0.0,
		pitch_content="(60, 62, 64, 66, 68)",
		is_slurred=True
	)
	f3 = Fragment(
		onset_start=1.0,
		onset_stop=2.0,
		fragment_type="decitala",
		name="Tritiya",
		mod_type="r",
		ratio=1.5,
		difference=0.0,
		pitch_content="(60, 62, 64, 66, 68)",
		is_slurred=True
	)
	session.add(f1)
	session.add(f2)
	session.add(f3)

	c1.composition_data = [f1, f2]
	c2.composition_data = [f3]

	session.commit()

#create_database_test(filepath="/Users/lukepoeppel/decitala/decitala/tests/{}.db".format(uuid.uuid4().hex), echo=True)

def create_database(
		db_path,
		filepath,
		datasets, # list of hash tables. 
		part_nums=[0], # assumes 0 by default
		windows=list(range(2, 19)),
		ignore_single_anga_class_fragments=False,
		extra_filter=None
	):
	"""
	Function for creating a database from a single filepath. 

	:param str db_path: path to the database to be created. 
	:param str filepath: path to the score to be analyzed.
	:param list datasets: list of hash table objects from `decitala.hash_table`. 
	:param list part_nums: parts to be analyzed.
	:param ignore_single_anga_class_fragments: whether to ignore single anga class fragments. 
											False by default. 
	:param extra_filter: lambda expression on the extracted fragments. 
	"""
	pass

def batch_create_database(
	):
	"""
	Provide dictionary of filepath and desired part nums. 
	"""
	pass