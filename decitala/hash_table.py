####################################################################################################
# File:     hash_table.py
# Purpose:  Hash table lookup algorithm for rhythmic search. 
# 
# Author:   Luke Poeppel
#
# Location: NYC, 2021. 
####################################################################################################
import sqlite3
import os
import json

from .utils import augment
from .fragment import (
	Decitala,
	GreekFoot
)

here = os.path.abspath(os.path.dirname(__file__))
fragment_db = os.path.dirname(here) + "/databases/fragment_database.db"

MODIFICATION_HIERARCHY = [
	"r",
	"rr",
	"d",
	"rd",
	"r+d",
	"r(r+d)"
]

def parse_hash_table_string(string_):
	"""
	In the hash_table classes, we store a string in the value giving both the extracted fragment 
	as well as its modification type. This function parses that string to get the python objects. 

	# if name is more than one word, uses underscores. 
	>>> s = "decitala-Gajajhampa-r-r:2_d:0"
	>>> parse_hash_table_string(s)
	(<fragment.Decitala 77_Gajajhampa>, ('rr', 2.0))
	>>> parse_hash_table_string('decitala-30_Hamsanada-n-r:0.75_d:0.25')
	(<fragment.Decitala 30_Hamsanada>, ('r+d', 0.75, 0.25))
	"""
	split = string_.split("-")
	frag_type = split[0]
	name = split[1]
	nor = split[2]  # normal or retrograde
	mod_data = split[3].split("_")
	
	if frag_type == "decitala":
		f = Decitala(name)
	else:
		f = GreekFoot(name)
	
	mod_vals = [float(mod_data[0][2:]), float(mod_data[1][2:])]
	if mod_vals[0] != 1 and mod_vals[1] == 0:
		mod_vals = [mod_vals[0]]
		if nor == "n":
			mod_type="r"
		else:
			mod_type="rr"
	elif mod_vals[0] == 1 and mod_vals[1] != 0:
		mod_vals = [mod_vals[1]]
		if nor == "n":
			mod_type="d"
		else:
			mod_type="rd"
	else:
		if nor == "n":
			mod_type="r+d"
		else:
			mod_type="r(r+d)"
	
	return (f, (mod_type, *mod_vals))

def _compare_mods(mod_a, mod_b):
	return min([mod_a, mod_b], key = lambda x: MODIFICATION_HIERARCHY.index(x))

def get_all_augmentations( 
		fragment,
		dict_in,
		factors=[0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0],
		differences=[0.0, 0.25, 0.5, 0.75],
		retrograde=True,
		superdivision_str=None
	):
	for this_factor in factors:
		for this_difference in differences:
			name = fragment[0]
			ql_array = json.loads(fragment[1])
			
			searches = [ql_array]
			if retrograde==True:
				searches.append(ql_array[::-1])
			
			for i, this_search in enumerate(searches):
				augmentation = tuple(augment(fragment=ql_array, factor=this_factor, difference=this_difference))            
				if any(x < 0 for x in augmentation):
					continue
				
				# Parse whether curr augmentation is more or less common.
				if augmentation in dict_in:
					value = dict_in[augmentation]
					data = parse_hash_table_string(value)
					mod = data[1][0] # already stored                    
				
					if i == 0:
						nor = ""
					else:
						nor = "r"
					
					if this_factor != 0 and this_difference == 0:
						curr_mod = nor + "r"
					elif this_factor == 1 and this_difference != 0:
						curr_mod = nor + "d"
					else:
						if nor == "":
							curr_mod = "r+d"
						else:
							curr_mod = "r(r+d)"
										
					if _compare_mods(mod, curr_mod) == mod:
						continue
					else:
						aug_string = "r:{}_d:{}".format(this_factor, this_difference)
						formatted_curr_mod = "decitala" + "-" + name + "-" + nor + "-" + aug_string
						dict_in[augmentation] == formatted_curr_mod
				else:
					if i == 0:
						nor = "n"
					else:
						nor = "r"
					
					aug_string = "r:{}_d:{}".format(this_factor, this_difference)
					full_value = "decitala" + "-" + name + "-" + nor + "-" + aug_string
					dict_in[augmentation] = full_value

def DecitalaHashTable(read_from_json=True):
	conn = sqlite3.connect("/Users/luke/decitala/databases/fragment_database.db")
	cur = conn.cursor()
	decitala_table_string = "SELECT * FROM Decitalas"
	cur.execute(decitala_table_string)
	decitala_rows = cur.fetchall()
	
	dht = dict()
	for fragment in decitala_rows:
		get_all_augmentations(dict_in=dht, fragment=fragment)
		
	return dht