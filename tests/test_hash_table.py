import os
import pytest
import sqlite3
import json
import random

from decitala.hash_table import DecitalaHashTable, get_all_augmentations
from decitala.fragment import Decitala

here = os.path.abspath(os.path.dirname(__file__))
decitala_path = os.path.dirname(here) + "/fragments/Decitalas"
greek_path = os.path.dirname(here) + "/fragments/Greek_Metrics/XML"

@pytest.fixture
def DHT():
	return DecitalaHashTable()

factors=[0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
differences=[0.0, 0.25, 0.5, 0.75]

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

def test_hash_table(DHT):
	DHT = DecitalaHashTable()
	conn = sqlite3.connect("/Users/lukepoeppel/decitala/databases/fragment_database.db")
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
		random_modification = str(tuple(random_modification))
		assert DHT[random_modification] is not None


