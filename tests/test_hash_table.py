import os
import pytest
import sqlite3
import json
import random
import doctest

from decitala import hash_table
from decitala.hash_table import (
	FragmentHashTable,
	DecitalaHashTable,
	GreekFootHashTable
)
from decitala.fragment import (
	Decitala,
	GeneralFragment,
	GreekFoot
)
from decitala.corpora_models import (
	get_engine,
	get_session,
	DecitalaData,
	GreekFootData
)

here = os.path.abspath(os.path.dirname(__file__))
fragment_db = os.path.dirname(here) + "/databases/fragment_database.db"

engine = get_engine(fragment_db)
session = get_session(engine=engine)

def test_doctests():
	assert doctest.testmod(hash_table, raise_on_error=True)

@pytest.fixture
def DHT():
	return DecitalaHashTable()

@pytest.fixture
def GFHT():
	return GreekFootHashTable()

FACTORS = [0.125, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
DIFFERENCES = [-0.375, -0.25, -0.125, 0.0, 0.125, 0.25, 0.375, 0.5, 0.75, 0.875, 1.75, 2.625, 3.5, 4.375]

normal = lambda x: x
retrograde = lambda x: x[::-1]

def multiplicative_augmentation(x):
	factor = random.choice(FACTORS)
	return [(y * factor) for y in x]

def additive_augmentation(x):
	difference = random.choice(DIFFERENCES)
	return [(y + difference) for y in x]

def retrograde_multiplicative_augmentation(x):
	factor = random.choice(FACTORS)
	return [(y * factor) for y in x[::-1]]

def retrograde_additive_augmentation(x):
	difference = random.choice(DIFFERENCES)
	return [(y + difference) for y in x[::-1]]

funcs = [
	normal,
	retrograde,
	multiplicative_augmentation,
	additive_augmentation,
	retrograde_multiplicative_augmentation,
	retrograde_additive_augmentation
]

def test_decitala_hash_table(DHT):
	fragment_data = session.query(DecitalaData).all()
	fragments = [Decitala(x.name) for x in fragment_data]

	for fragment in fragments:
		random_modification = random.choice(funcs)(fragment.ql_array())
		if any(x <= 0 for x in random_modification):
			continue
		
		random_modification = str(tuple(random_modification))
		assert DHT.data[random_modification] is not None

def test_greek_foot_hash_table(GFHT):
	fragment_data = session.query(GreekFootData).all()
	fragments = [GreekFoot(x.name) for x in fragment_data]

	for fragment in fragments:
		random_modification = random.choice(funcs)(fragment.ql_array())
		if any(x <= 0 for x in random_modification):
			continue
		
		random_modification = str(tuple(random_modification))
		assert GFHT.data[random_modification] is not None