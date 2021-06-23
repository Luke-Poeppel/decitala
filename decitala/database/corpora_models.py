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
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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