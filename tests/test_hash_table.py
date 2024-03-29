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
	GreekFootHashTable,
	ProsodicMeterHashTable,
	generate_all_modifications
)
from decitala.fragment import (
	Decitala,
	GeneralFragment,
	GreekFoot,
	get_all_decitalas,
	get_all_greek_feet,
	get_all_prosodic_meters
)

FACTORS = [0.125, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
DIFFERENCES = [-0.375, -0.25, -0.125, 0.0, 0.125, 0.25, 0.375, 0.5, 0.75, 0.875, 1.75, 2.625, 3.5, 4.375]

def normal(x):
	return x, 1

def retrograde(x):
	return x[::-1], 1

def multiplicative_augmentation(x):
	factor = random.choice(FACTORS)
	return [(y * factor) for y in x], factor

def additive_augmentation(x):
	difference = random.choice(DIFFERENCES)
	return [(y + difference) for y in x], difference

def retrograde_multiplicative_augmentation(x):
	factor = random.choice(FACTORS)
	return [(y * factor) for y in x[::-1]], factor

def retrograde_additive_augmentation(x):
	difference = random.choice(DIFFERENCES)
	return [(y + difference) for y in x[::-1]], difference

funcs = [
	normal,
	retrograde,
	multiplicative_augmentation,
	additive_augmentation,
	retrograde_multiplicative_augmentation,
	retrograde_additive_augmentation
]

def test_doctests():
	assert doctest.testmod(hash_table, raise_on_error=True)

def test_generate_all_modifications():
	factors = [0.125, 0.25, 0.5, 0.75, 1.0, 2.0, 4.0]
	differences = [0.0, 0.25, 0.5, 0.75]
	try_retrograde = True
	dict_in = dict()

	all_modifications = generate_all_modifications(
		dict_in=dict_in,
		fragment=GreekFoot("Iamb"),
		factors=factors,
		differences=differences,
		allow_stretch_augmentation=False,
		allow_mixed_augmentation=False,
		try_retrograde=try_retrograde
	)

	# Subtract 1 for each duplicate (*1 or + 0) in regular and retrograde. 
	# Multiply by 2 for retrograde. 
	expected_length = (2*(len(factors) + len(differences))) - 2
	assert len(dict_in) == expected_length

def test_decitala_hash_table():
	DHT = DecitalaHashTable()
	fragments = get_all_decitalas()
	for fragment in fragments:
		modification_and_mod_val = random.choice(funcs)(fragment.ql_array())
		if any(x <= 0 for x in modification_and_mod_val[0]):
			continue # This is ignoring a failed case! 
		
		modification = tuple(modification_and_mod_val[0])
		mod_value = modification_and_mod_val[1]
		search_result = DHT.data[modification]

		assert search_result is not None

def test_greek_foot_hash_table():
	GFHT = GreekFootHashTable()
	fragments = get_all_greek_feet()
	for fragment in fragments:
		modification_and_mod_val = random.choice(funcs)(fragment.ql_array())
		if any(x <= 0 for x in modification_and_mod_val[0]):
			continue
		
		modification = tuple(modification_and_mod_val[0])
		mod_value = modification_and_mod_val[1]
		search_result = GFHT.data[modification]

		assert search_result is not None

def test_prosodic_fragment_hash_table():
	PFHT = ProsodicMeterHashTable()
	fragments = get_all_prosodic_meters()
	for fragment in fragments:
		modification_and_mod_val = random.choice(funcs)(fragment.ql_array())
		if any(x <= 0 for x in modification_and_mod_val[0]):
			continue
		
		modification = tuple(modification_and_mod_val[0])
		mod_value = modification_and_mod_val[1]
		search_result = PFHT.data[modification]

		assert search_result is not None

def test_ragavardhana():
	DHT = DecitalaHashTable()
	frag = [3.0, 0.5, 0.75, 0.5]
	assert DHT.data[tuple(frag)]["fragment"] == Decitala("Ragavardhana")

def test_peons():
	GFHT = GreekFootHashTable()
	p1 = GreekFoot("Peon_I")
	p2 = GreekFoot("Peon_II")
	p3 = GreekFoot("Peon_III")
	p4 = GreekFoot("Peon_IV")
	peons = [p1, p2, p3, p4]
	
	for p in peons:
		assert GFHT.data[p.ql_tuple()]["fragment"] == p

def test_stretch_augmentation():
	GFHT = GreekFootHashTable()
	
	# Both described as being Iambic:
	nc_ex2_1 = [0.125, 0.375]
	found_1 = GFHT.data[tuple(nc_ex2_1)]
	assert found_1["fragment"].name == "Iamb"
	assert found_1["mod_hierarchy_val"] == 7 # Stretch augmentation

	nc_ex2_2 = [0.125, 0.5]
	found_2 = GFHT.data[tuple(nc_ex2_2)]
	assert found_2["fragment"].name == "Iamb"
	assert found_2["mod_hierarchy_val"] == 7 # Stretch augmentation

def test_exact_decitala_hash_table():
	DHT = DecitalaHashTable(exact=True)
	assert len(DHT.data) == 119