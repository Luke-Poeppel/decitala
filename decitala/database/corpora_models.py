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
	create_engine,
	ForeignKey,
)
from sqlalchemy.orm import (
	sessionmaker,
	relationship,
	backref
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def get_session(db_path, echo=False):
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