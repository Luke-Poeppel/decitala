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

here = os.path.abspath(os.path.dirname(__file__))
fragment_db = os.path.dirname(here) + "/databases/fragment_database.db"

MODIFICATION_HIERARCHY = [
	"r",
	"rr",
	"d",
	"rd",
	"sr",
	"rsr"
]

def DecitalaHashTable():
	conn = sqlite3.connect(fragment_db)
	cur = conn.cursor()
	decitala_table_string = "SELECT * FROM Decitalas"
	cur.execute(decitala_table_string)
	decitala_rows = cur.fetchall()

	dht = dict()
	factors = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
	differences = [0.0, 0.25, 0.5, 0.75] #-0.75, -0.5, -0.25, 
	for this_fragment in decitala_rows:
		for this_factor in factors:
			for this_difference in differences:
				name = this_fragment[0]
				ql_array = json.loads(this_fragment[1])
				augmentation = tuple(augment(fragment=ql_array, factor=this_factor, difference=this_difference))            
				if all(x > 0 for x in augmentation):
					if this_factor != 1 and this_difference == 0:
						mod_string = "r:{}".format(this_factor)
					elif this_factor == 1 and this_difference != 0:
						mod_string = "d:{}".format(this_difference)
					else:
						mod_string = "r:{0}_d:{1}".format(this_factor, this_difference)
						
					dht[augmentation] = "-".join(["decitala-{0}".format(name), mod_string])
	return dht