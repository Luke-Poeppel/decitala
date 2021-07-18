####################################################################################################
# File:     database.py
# Purpose:  Data structure for creating and representing databases using sqlite.
#
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020, 2021 / Frankfurt, DE 2020 / NYC, 2021
####################################################################################################
import json
import natsort
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

from ..fragment import FragmentDecoder, FragmentEncoder
from ..utils import get_logger
from ..hm import hm_utils
from ..vis import annotate_score
from .db_utils import (
	get_session,
	TRANSCRIPTION_BASE
)
from ..search import (
	rolling_hash_search,
	path_finder
)
from ..path_finding import path_finding_utils
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
	SQLAlchemy model representing a fragment extracted from a composition. Intended to be used with
	the class method :obj:`ExtractionData.from_extraction`. See :obj:`decitala.search.Extraction`
	for the relevant information on each column in the database.
	"""
	__tablename__ = "ExtractionData"

	id = Column(Integer, primary_key=True)

	fragment = Column(String)
	onset_start = Column(Float)
	onset_stop = Column(Float)

	retrograde = Column(Boolean)
	factor = Column(Float)
	difference = Column(Float)
	mod_hierarchy_val = Column(Integer)

	pitch_content = Column(String)
	is_spanned_by_slur = Column(Boolean)
	slur_count = Column(Integer)
	slur_start_end_count = Column(Integer)

	id_ = Column(Integer)
	contiguous_summation = Column(Boolean)

	composition_data_id = Column(Integer, ForeignKey("CompositionData.id"))
	composition_data = relationship("CompositionData", backref=backref("composition_data"))

	def __init__(
			self,
			fragment,
			onset_start,
			onset_stop,
			retrograde,
			factor,
			difference,
			mod_hierarchy_val,
			pitch_content,
			is_spanned_by_slur,
			slur_count,
			slur_start_end_count,
			id_,
			contiguous_summation
		):
		self.fragment = fragment
		self.onset_start = onset_start
		self.onset_stop = onset_stop
		self.retrograde = retrograde
		self.factor = factor
		self.difference = difference
		self.mod_hierarchy_val = mod_hierarchy_val
		self.pitch_content = pitch_content
		self.is_spanned_by_slur = is_spanned_by_slur
		self.slur_count = slur_count
		self.slur_start_end_count = slur_start_end_count
		self.id_ = id_
		self.contiguous_summation = contiguous_summation

	@classmethod
	def from_extraction(cls, extraction):
		"""
		Creates an :obj:`decitala.database.db.ExtractionData` object from a
		:obj:`decitala.search.Extraction` object. This is more durable to accidentally breaking
		things when adding data to extractions.
		"""
		return ExtractionData(
			fragment=json.dumps(extraction.fragment, cls=FragmentEncoder),
			onset_start=extraction.onset_range[0],
			onset_stop=extraction.onset_range[1],
			retrograde=extraction.retrograde,
			factor=extraction.factor,
			difference=extraction.difference,
			mod_hierarchy_val=extraction.mod_hierarchy_val,
			pitch_content=json.dumps(extraction.pitch_content),
			is_spanned_by_slur=extraction.is_spanned_by_slur,
			slur_count=extraction.slur_count,
			slur_start_end_count=extraction.slur_start_end_count,
			id_=extraction.id_,
			contiguous_summation=extraction.contiguous_summation
		)

def _add_extraction_results_to_session(
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

		all_results = rolling_hash_search(
			filepath=filepath,
			part_num=this_part,
			table=table,
			windows=windows
		)
		if not(all_results):
			return "No fragments extracted –– stopping."

		extraction_objects = []
		for extraction in all_results:
			f = ExtractionData.from_extraction(extraction)
			extraction_objects.append(f)
			session.add(f)
		data.composition_data = extraction_objects

def create_extraction_database(
		db_path,
		filepath,
		table,
		part_nums=[0],
		windows=list(range(2, 19)),
		echo=False
	):
	"""
	Function for creating a database from a single filepath. Stores all extracted fragments.

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

	_add_extraction_results_to_session(
		filepath,
		part_nums,
		table,
		windows,
		session
	)

	session.commit()
	return

def batch_create_extraction_database(
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
		_add_extraction_results_to_session(
			filepath,
			part_nums,
			table,
			windows,
			session
		)

	session.commit()
	return

def _add_path_results_to_session(
		filepath,
		part_nums,
		table,
		windows,
		allow_subdivision,
		allow_contiguous_summation,
		algorithm,
		cost_function_class,
		split_dict,
		slur_constraint,
		enforce_earliest_start,
		session
	):
	filepath_name = filepath.split("/")[-1]
	for part_num in part_nums:
		data = CompositionData(
			name=filepath_name,
			part_num=part_num,
			local_filepath=filepath
		)
		session.add(data)

		path = path_finder(
			filepath,
			part_num,
			table,
			windows,
			allow_subdivision,
			allow_contiguous_summation,
			algorithm,
			cost_function_class,
			split_dict,
			slur_constraint,
			enforce_earliest_start
		)
		if not(path):
			return "No fragments extracted –– stopping."

		extraction_objects = []
		for extraction in path:
			f = ExtractionData.from_extraction(extraction)
			extraction_objects.append(f)
			session.add(f)
		data.composition_data = extraction_objects

def create_path_database(
		db_path,
		filepath,
		part_nums,
		table,
		windows=list(range(2, 19)),
		allow_subdivision=False,
		allow_contiguous_summation=False,
		algorithm="dijkstra",
		cost_function_class=path_finding_utils.CostFunction3D(),
		split_dict=None,
		slur_constraint=False,
		enforce_earliest_start=False,
		echo=False
	):
	"""
	Function for creating a database from a single filepath. Stores the extracted path.
	See :obj:`decitala.search.path_finder` to find the definitions of the relevant parameters.

	:param str db_path: Path to the database to be created.
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

	_add_path_results_to_session(
		filepath,
		part_nums,
		windows,
		allow_subdivision,
		allow_contiguous_summation,
		algorithm,
		cost_function_class,
		split_dict,
		slur_constraint,
		enforce_earliest_start,
		session
	)

	session.commit()
	return

def create_batch_path_database(
		db_path,
		data_in,
		table,
		windows=list(range(2, 19)),
		allow_subdivision=False,
		allow_contiguous_summation=False,
		algorithm="dijkstra",
		cost_function_class=path_finding_utils.CostFunction3D(),
		split_dict=None,
		slur_constraint=False,
		enforce_earliest_start=False,
		echo=False
	):
	"""
	This function creates a database from a dictionary of filepaths and desires ``part_nums``
	to analyze. See :obj:`decitala.search.path_finder` to find the definitions of the relevant
	parameters.

	:param str db_path: Path to the database to be created.
	:param dict data_in: Dictionary of filepaths (key) and part nums in a list (value).
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
		_add_path_results_to_session(
			filepath,
			part_nums,
			windows,
			allow_subdivision,
			allow_contiguous_summation,
			algorithm,
			cost_function_class,
			split_dict,
			slur_constraint,
			enforce_earliest_start,
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
		self.colors = json.loads(res.colors)
		self.locations = json.loads(res.locations)
		self.datetimes = json.loads(res.datetimes)

		self.transcriptions = [Transcription(transcription.name) for transcription in res.transcriptions]

	def __repr__(self):
		return f"<database.Species {self.name}>"

	@property
	def num_transcriptions(self):
		return len(self.transcriptions)

	def aggregated_pc_distribution(
			self,
			normalized=False,
			as_vector=True
		):
		"""
		Returns the aggregate pitch class distribution across all transcriptions in a species.
		"""
		net_counter_pre = {x: [] for x in range(12)}
		for transcription in self.transcriptions:
			transcription_counter = hm_utils.pc_counter(
				filepath=transcription.filepath,
				part_num=0
			)
			for key in transcription_counter:
				net_counter_pre[key].append(transcription_counter[key])

		net_counter = {x: sum(y) for x, y in net_counter_pre.items()}

		if normalized:
			net = sum(net_counter.values())
			net_counter = {x: (y / net) for x, y in net_counter.items()}

		if not(as_vector):
			return net_counter
		else:
			return hm_utils.pc_dict_to_vector(net_counter)

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

	def show(self, show_analysis=False):
		if not(show_analysis):
			converted = converter.parse(self.filepath)
			converted.show()
		else:
			if self.analysis:
				annotate_score(
					data=self.analysis,
					filepath=self.filepath,
					part_num=0,
					transcription_mode=True
				).show()
			else:
				converted = converter.parse(self.filepath)
				converted.show()

def get_all_species():
	session = get_session(db_path=ODNC_Database, base=TRANSCRIPTION_BASE)
	res = session.query(SubcategoryData).all()
	return [Species(x.name) for x in res]

def get_all_transcriptions():
	session = get_session(db_path=ODNC_Database, base=TRANSCRIPTION_BASE)
	res = session.query(TranscriptionData).all()
	return natsort.natsorted([Transcription(x.name) for x in res], key=lambda x: x.name)