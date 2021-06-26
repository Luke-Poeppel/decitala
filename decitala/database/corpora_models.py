####################################################################################################
# File:     corpora_models.py
# Purpose:  Module for holding all of the SQLAlchemy models used in the decitala package for
#           included corpora.
#
# Author:   Luke Poeppel
#
# Location: NYC, 2021
####################################################################################################
from sqlalchemy import (
	Column,
	Integer,
	String,
	ForeignKey
)
from sqlalchemy.orm import (
	relationship,
	backref
)
from .db_utils import (
	FRAGMENT_BASE,
	TRANSCRIPTION_BASE
)

class DecitalaData(FRAGMENT_BASE):
	"""
	SQLAlchemy model representing a decitala fragment from the encoded datasets (given in ``corpora``).
	"""
	__tablename__ = "DecitalaData"

	id = Column(Integer, primary_key=True)
	full_id = Column(String)
	name = Column(String)
	ql_array = Column(String)

class GreekFootData(FRAGMENT_BASE):
	"""
	SQLAlchemy model representing a greek foot fragment from the encoded datasets (given
	in ``corpora``).
	"""
	__tablename__ = "GreekFootData"

	id = Column(Integer, primary_key=True)
	name = Column(String)
	ql_array = Column(String)

class ProsodicFragmentData(FRAGMENT_BASE):
	"""
	SQLAlchemy model representing a prosodic fragment from the encoded datasets (given in ``corpora``).
	"""
	__tablename__ = "ProsodicFragmentData"

	id = Column(Integer, primary_key=True)
	name = Column(String)
	source = Column(String)
	ql_array = Column(String)

####################################################################################################
# Transcriptions
class CategoryData(TRANSCRIPTION_BASE):
	"""
	Category table of the database, (possibly) holding multiple subcategories, i.e., species.
	"""
	__tablename__ = "CategoryData"

	id = Column(Integer, primary_key=True)
	name = Column(String)
	group_number = Column(Integer)

	def __repr__(self):
		return f"<decitala.CategoryData {self.name}>"

class SubcategoryData(TRANSCRIPTION_BASE):
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
		return f"<decitala.SubcategoryData {self.name}>"

class TranscriptionData(TRANSCRIPTION_BASE):
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
		return f"<decitala.TranscriptionData {self.name}>"
