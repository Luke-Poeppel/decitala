import os
import pytest
import sqlite3
import json
import random

from decitala.hash_table import (
	DecitalaHashTable,
	GreekFootHashTable,
	get_all_augmentations,
	FragmentHashTable
)
from decitala.fragment import Decitala, GeneralFragment

here = os.path.abspath(os.path.dirname(__file__))
fragment_db = os.path.dirname(here) + "/databases/fragment_database.db"

@pytest.fixture
def DHT():
	return DecitalaHashTable()

@pytest.fixture
def GFHT():
	return GreekFootHashTable()

factors = [0.125, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
differences = [-0.375, -0.25, -0.125, 0.0, 0.125, 0.25, 0.375, 0.5, 0.75, 0.875, 1.75, 2.625, 3.5, 4.375]

normal = lambda x: x
retrograde = lambda x: x[::-1]

def multiplicative_augmentation(x):
	factor = random.choice(factors)
	return [(y * factor) for y in x]

def additive_augmentation(x):
	difference = random.choice(differences)
	return [(y + difference) for y in x]

def retrograde_multiplicative_augmentation(x):
	factor = random.choice(factors)
	return [(y * factor) for y in x[::-1]]

def retrograde_additive_augmentation(x):
	difference = random.choice(differences)
	return [(y + difference) for y in x[::-1]]

def test_decitala_hash_table(DHT):
	conn = sqlite3.connect(fragment_db)
	cur = conn.cursor()
	decitala_table_string = "SELECT * FROM Decitalas"
	cur.execute(decitala_table_string)
	decitala_rows = cur.fetchall()

	funcs = [
		normal,
		retrograde,
		multiplicative_augmentation,
		additive_augmentation,
		retrograde_multiplicative_augmentation,
		retrograde_additive_augmentation
	]

	for fragment in decitala_rows:
		ql_array = json.loads(fragment[1])
		random_modification = random.choice(funcs)(ql_array)
		
		if any(x <= 0 for x in random_modification):
			continue
		
		random_modification = str(tuple(random_modification))
		assert DHT[random_modification] is not None

def test_greek_foot_hash_table(GFHT):
	conn = sqlite3.connect(fragment_db)
	cur = conn.cursor()
	decitala_table_string = "SELECT * FROM Greek_Metrics"
	cur.execute(decitala_table_string)
	greek_rows = cur.fetchall()

	funcs = [
		normal,
		retrograde,
		multiplicative_augmentation,
		additive_augmentation,
		retrograde_multiplicative_augmentation,
		retrograde_additive_augmentation
	]

	for fragment in greek_rows:
		ql_array = json.loads(fragment[1])
		random_modification = random.choice(funcs)(ql_array)
		
		if any(x <= 0 for x in random_modification):
			continue
		
		random_modification = str(tuple(random_modification))
		assert GFHT[random_modification] is not None

# d = FragmentHashTable(
# 	datasets=["greek_foot"],
# 	custom_fragments=[GeneralFragment([3.0, 4.0, 2.0, 1.0], name="my awesome fragment")]
# )
# print(d.data())