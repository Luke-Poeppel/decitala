import os
import random

from decitala.fragment import (
	Decitala,
	GreekFoot,
	GeneralFragment
)

here = os.path.abspath(os.path.dirname(__file__))
decitala_path = os.path.dirname(here) + "/Fragments/Decitalas"
greek_path = os.path.dirname(here) + "/Fragments/Greek_Metrics/XML"

# Possible manipulations for Decitalas and GreekFoot objects. 
full_name = lambda x: x
without_extension = lambda x: x[:-4]
without_id_num_pre = lambda x: "".join([i for i in x if not(i.isdigit())])
without_id_num = lambda x: without_id_num_pre(x)[1:]
without_id_num_without_extension = lambda x: without_id_num(x)[:-4]

def test_all_decitala_names():
	# 4 possible inputs are allowed for the names. 
	funcs = [full_name, without_extension, without_id_num, without_id_num_without_extension]
	for this_file in os.listdir(decitala_path):
		new_name = random.choice(funcs)(this_file)
		this_decitala = Decitala(new_name)
		assert this_decitala.full_path == decitala_path + "/" + this_file

# I also test a few problematic examples below, just for safety. 
def test_gaja_gajajhampa_gajalila():
	gaja = Decitala("Gaja")
	gajajhampa = Decitala("77_Gajajhampa")
	gajalila = Decitala("18_Gajalila.xml")

	assert gaja.name == "99_Gaja"
	assert gajajhampa.name == "77_Gajajhampa"
	assert gajalila.name == "18_Gajalila"

def test_sama_kankala_sama():
	sama = Decitala("Sama.xml")
	kankala_sama = Decitala("Kankala_Sama")
	
	assert sama.name == "53_Sama"
	assert kankala_sama.name == "65_C_Kankala_Sama"

def test_jaya_jayacri_jayamangala():
	jaya = Decitala("Jaya")
	jaya2 = Decitala("Jaya.xml")
	jayacri = Decitala("46_Jayacri")
	jayamangala = Decitala("Jayamangala.xml")

	assert jaya.name == "28_Jaya"
	assert jaya2.name == "28_Jaya"
	assert jayacri.name == "46_Jayacri"
	assert jayamangala.name == "42_Jayamangala"

def test_all_greek_foot_names():
	# 4 possible inputs are allowed for the names. 
	funcs = [full_name, without_extension]
	for this_file in os.listdir(greek_path):
		new_name = random.choice(funcs)(this_file)
		this_greek_foot = GreekFoot(new_name)
		assert this_greek_foot.full_path == greek_path + "/" + this_file