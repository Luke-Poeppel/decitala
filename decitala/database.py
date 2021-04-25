# -*- coding: utf-8 -*-
####################################################################################################
# File:     database.py
# Purpose:  Data structure for creating and representing databases using sqlite.
#
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020 / Frankfurt, DE 2020 / NYC, 2021
####################################################################################################

from sqlalchemy import (
	Column,
	String,
	Float,
	Boolean,
	Integer
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
	sessionmaker,
	relationship,
	backref
)

Base = declarative_base()

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
	:param str composition_data: composition data (backref for simple `CompositionData` model). This is retrieved in the
								creation of the database. 
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
	composition_data = Column(String)

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
			composition_data
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
		self.composition_data = composition_data



