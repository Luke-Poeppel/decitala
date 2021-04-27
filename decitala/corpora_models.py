####################################################################################################
# File:     corpora_models.py
# Purpose:  Module for holding all of the SQLAlchemy models used in the decitala package for 
#           included corpora. 
#
# Author:   Luke Poeppel
#
# Location: NYC, 2021
####################################################################################################
import uuid
import os

from sqlalchemy import (
	Column,
	Integer,
	String,
	create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

here = os.path.abspath(os.path.dirname(__file__))
decitala_path = os.path.dirname(here) + "/corpora/Decitalas"
greek_path = os.path.dirname(here) + "/corpora/Greek_Metrics/"

Base = declarative_base()

def get_engine(filepath, echo=False):
	engine = create_engine(f"sqlite:////{filepath}", echo=echo)
	Base.metadata.create_all(engine)
	return engine

def get_session(engine):
	Session = sessionmaker(bind=engine)
	session = Session()
	return session

class DecitalaData(Base):
	"""
	SQLAlchemy model representing a decitala fragment from the encoded datasets (given in `corpora`). 
	"""
	__tablename__ = "DecitalaData"
	
	id = Column(Integer, primary_key=True)
	name = Column(String)
	ql_array = Column(String)
	ratio_equivalents = Column(String)
	difference_equivalents = Column(String)

class GreekFootData(Base):
	"""
	SQLAlchemy model representing a greek foot fragment from the encoded datasets (given in `corpora`). 
	"""
	__tablename__ = "GreekFootData"

	id = Column(Integer, primary_key=True)
	name = Column(String)
	ql_array = Column(String)
	ratio_equivalents = Column(String)
	difference_equivalents = Column(String)

def _make_corpora_database():
	abspath_databases_directory = os.path.abspath("./databases/")
	engine = get_engine(filepath=os.path.join(abspath_databases_directory, "{}.db".format(uuid.uuid4().hex)), echo=False)
	session = get_session(engine=engine)

	for this_file in os.listdir(decitala_path):
		pass


