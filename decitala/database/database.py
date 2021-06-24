####################################################################################################
# File:     database.py
# Purpose:  Data structure for creating and representing databases using sqlite.
#
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020, 2021 / Frankfurt, DE 2020 / NYC, 2021
####################################################################################################
import json
import numpy as np
import os

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

from music21 import converter

from ..fragment import FragmentDecoder
from ..search import rolling_hash_search
from ..utils import get_logger
from ..hm import molt
from .db_utils import (
	get_session,
	TRANSCRIPTION_BASE
)
from .corpora_models import (
	SubcategoryData,
	TranscriptionData
)

here = os.path.abspath(os.path.dirname(__file__))
ODNC_Database = os.path.dirname(os.path.dirname(here)) + "/databases/ODNC.db"

Base = declarative_base()

class DatabaseException(Exception):
	pass

class CompositionData(Base):
	"""
	SQLAlchemy model representing the basic composition data for a composition.

	Parameters
	----------

	:param str name: Name of the composition.
	:param int part_num: Part number for the extraction.
	:param str local_filepath: Local filepath for the searched composition.

	TODO: could add a `search_constraint` column that stores a JSON of the rolling_search parameters.
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

# TODO: rename to `ExtractionData`
class ExtractionData(Base):
	"""
	SQLAlchemy model representing a fragment extracted from a composition.

	Parameters
	----------

	:param float onset_start: Starting onset of the extracted fragment.
	:param float onset_stop: Ending onset of the extracted fragment
							(onset of final object + quarter length)
	:param str fragment_type: Fragment type; options currently include
							`decitala`, `greek_foot`, and `general_fragment`.
	:param str name: Name of the fragment.
	:param str mod_type: Modification type of the fragment.
	:param float ratio: Ratio of the fragment's values to the values in the database.
	:param float difference: Difference between the fragment's values to the values
							in the database.
	:param str pitch_content: Pitch content of the extracted fragment.
	:param bool is_slurred: Whether the extracted fragment is spanned by a slur object.
	"""
	__tablename__ = "ExtractionData"

	id = Column(Integer, primary_key=True)

	onset_start = Column(Float)
	onset_stop = Column(Float)

	# TODO: just make this fragment with the JSON output from FragmentEncoder.
	fragment_type = Column(String)
	name = Column(String)

	mod_hierarchy_val = Column(Float)
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

def _add_results_to_session(
		filepath,
		part_nums,
		table,
		windows,
		session
	):
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
			f = ExtractionData(
				onset_start=this_fragment.onset_range[0],
				onset_stop=this_fragment.onset_range[1],
				fragment_type=this_fragment.frag_type,
				name=this_fragment.fragment.name,
				mod_hierarchy_val=this_fragment.mod_hierarchy_val,
				ratio=this_fragment.factor,
				difference=this_fragment.difference,
				pitch_content=json.dumps(this_fragment.pitch_content),
				is_slurred=this_fragment.is_spanned_by_slur
			)
			fragment_objects.append(f)
			session.add(f)

		data.composition_data = fragment_objects

def create_database(
		db_path,
		filepath,
		table,
		part_nums=[0],
		windows=list(range(2, 19)),
		echo=False
	):
	"""
	Function for creating a database from a single filepath.

	:param str db_path: Path to the database to be created.
	:param str filepath: Path to the score to be analyzed.
	:param list table: A :obj:`decitala.hash_table.FragmentHashTable` object.
	:param list part_nums: Parts to be analyzed.
	:param list windows: Possible lengths of the search frames.
	:param bool echo: Whether to echo the SQL calls. False by default.
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

	_add_results_to_session(
		filepath,
		part_nums,
		table,
		windows,
		session
	)

	session.commit()
	return

def batch_create_database(
		db_path,
		data_in,
		table,
		windows,
		echo=False
	):
	"""
	This function creates a database from a dictionary of filepaths and desires ``part_nums``
	to analyze.

	:param str db_path: Path to the database to be created.
	:param dict data_in: Dictionary of filepaths (key) and part nums in a list (value).
	:param list table: A :obj:`decitala.hash_table.FragmentHashTable` object.
	:param list windows: Possible lengths of the search frames.
	:param bool echo: Whether to echo the SQL calls. False by default.
	"""
	assert db_path.endswith(".db"), DatabaseException("✗ The db_path must end with '.db'.")
	if os.path.isfile(db_path):
		return "That database already exists ✔"

	logger = get_logger(name=__file__, print_to_console=True)
	logger.info(f"Preparing database at {db_path}...")

	engine = create_engine(f"sqlite:////{db_path}", echo=echo)
	Base.metadata.create_all(engine)

	Session = sessionmaker(bind=engine)
	session = Session()

	for filepath, part_nums in data_in.items():
		_add_results_to_session(
			filepath,
			part_nums,
			table,
			windows,
			session
		)

	session.commit()
	return

####################################################################################################
class Species:
	"""
	This class allows a user to access the SubcategoryData results without relying on SQLAlchemy.
	It only requires a name (and also supports class methods).
	"""
	def __init__(self, name):
		self.session = get_session(db_path=ODNC_Database, base=TRANSCRIPTION_BASE)
		res = self.session.query(SubcategoryData).filter(SubcategoryData.name == name).first()
		if not res:
			raise DatabaseException(f"No matches found for '{name}'")

		self.name = res.name
		self.latin = res.latin
		self.local_name = res.local_name
		self.reported_size = res.reported_size
		self.description = json.loads(res.description)
		self.locations = json.loads(res.locations)

		self.transcriptions = [Transcription(transcription.name) for transcription in res.transcriptions]

	def __repr__(self):
		return f"<database.Species {self.name}>"

	@property
	def num_transcriptions(self):
		return len(self.transcriptions)

	def aggregate_pc_distribution(self, as_vector=True):
		combined_pc_counter = []
		for transcription in self.transcriptions:
			fp = transcription.filepath
			pc_counter_dict = molt.pc_counter(fp, 0, normalize_over_duration=True)
			pc_counter_vector = molt.pc_dict_to_vector(pc_counter_dict)
			combined_pc_counter.append(pc_counter_vector)

		combined_pc_counter = np.sum(np.array(combined_pc_counter), axis=0)
		combined_pc_counter = combined_pc_counter / sum(combined_pc_counter)
		if as_vector:
			return combined_pc_counter
		else:
			combined_pc_dict = dict()
			for i, val in enumerate(combined_pc_counter):
				combined_pc_dict[str(i)] = val
			return combined_pc_dict

class Transcription:
	"""
	This class allows a user to access the TranscriptionData results without relying on SQLAlchemy.
	It only requires a name (and also supports class methods).
	"""
	def __init__(self, name):
		self.session = get_session(db_path=ODNC_Database, base=TRANSCRIPTION_BASE)
		res = self.session.query(TranscriptionData).filter(TranscriptionData.name == name).first()
		if not res:
			raise DatabaseException(f"No matches found for '{name}'")

		self.name = res.name
		self.filepath = res.filepath
		if not(res.analysis):
			self.analysis = None
		else:
			self.analysis = json.loads(res.analysis, cls=FragmentDecoder)

	def __repr__(self):
		return f"<database.Transcription {self.name}>"

	def show(self):
		converted = converter.parse(self.filepath)
		converted.show()