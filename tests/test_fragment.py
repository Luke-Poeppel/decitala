import os
import random
import numpy as np
import json
import doctest

from decitala import fragment
from decitala.fragment import (
	Decitala,
	GreekFoot,
	GeneralFragment,
	FragmentEncoder,
	FragmentDecoder
)

here = os.path.abspath(os.path.dirname(__file__))
decitala_path = os.path.dirname(here) + "/corpora/Decitalas"
greek_path = os.path.dirname(here) + "/corpora/Greek_Metrics/"

def test_doctests():
	assert doctest.testmod(fragment, raise_on_error=True)

def test_general_fragment_encoder():
	g1 = GeneralFragment(data=[1.0, 2.0, 3.0, 4.0, 5.0], name="longerrrr")
	dumped_g1 = json.dumps(g1, cls=FragmentEncoder)
	expected_g1 = """{"frag_type": "general_fragment", "data": [1.0, 2.0, 3.0, 4.0, 5.0], "name": "longerrrr"}""" # noqa
	
	# g2 = GeneralFragment(data="/Users/lukepoeppel/decitala/corpora/Decitalas/1_Aditala.xml")
	# dumped_g2 = json.dumps(g2, cls=FragmentEncoder)
	# expected_g2 = """{"frag_type": "general_fragment", "data": "/Users/lukepoeppel/decitala/corpora/Decitalas/1_Aditala.xml", "name": null}""" # noqa

	assert dumped_g1 == expected_g1
	# assert dumped_g2 == expected_g2

def test_decitala_fragment_encoder():
	d = Decitala("Anlarakrida")
	dumped = json.dumps(d, cls=FragmentEncoder)
	expected = """{"frag_type": "decitala", "name": "95_Anlarakrida"}"""

	assert dumped == expected

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

def test_get_by_id():
	random_nums = [71, 23, 14, 91, 108, 44]
	for this_id in random_nums:
		assert Decitala.get_by_id(this_id) is not None

def test_id_num():
	for i in range(0, 121, 20):
		if i == 0:
			assert Decitala("Aditala").id_num == i + 1
		else:
			assert Decitala.get_by_id(i).id_num == i

##### JSON ENCODING / DECODING
def test_decitala_encoding():
	ragavardhana = Decitala("Ragavardhana")
	encoded = '{"frag_type": "decitala", "name": "93_Ragavardhana"}'
	assert json.dumps(ragavardhana, cls=FragmentEncoder) == encoded

def test_decitala_carnatic_string():
	rajacudamani = Decitala("Rajacudamani")
	predicted = "o o | | | o o | S"
	assert rajacudamani.carnatic_string == predicted

def test_dseg():
	frag = GeneralFragment([1.0, 1.0, 2.0, 2.0, 3.0, 0.125, 1.0, 0.5, 4.0])
	predicted = np.array([2, 2, 3, 3, 4, 0, 2, 1, 5])
	assert np.array_equal(predicted, frag.dseg())

def test_reduced_dseg():
	frag = GeneralFragment([1.0, 1.0, 2.0, 2.0, 3.0, 0.125, 1.0, 0.5, 4.0])
	predicted = np.array([2, 3, 4, 0, 2, 1, 5])
	assert np.array_equal(predicted, frag.reduced_dseg())

def test_fragment_augment():
	f1 = GeneralFragment([4.0, 1.0, 2.0], name="myfragment")
	f1a = f1.augment(factor=2, difference=0.25)
	assert f1a.name == "myfragment/r:2/d:0.25"

def test_decitala_repr():
	name_in = "Gajalila"
	frag_id = Decitala(name_in).id_num
	assert Decitala(name_in).__repr__() == "<fragment.Decitala {0}_{1}>".format(frag_id, name_in)

def test_decitala_equivalents():
	example_frag = Decitala("Tribhangi")
	r_equivalents = [Decitala("Crikirti"), Decitala("Kudukka"), Decitala("Ratilila"), GreekFoot("Ionic_Minor")]
	d_equivalents = [Decitala("Crikirti"), Decitala("Ratilila")]
	
	assert example_frag.equivalents(rep_type="ratio") == r_equivalents
	assert example_frag.equivalents(rep_type="difference") == d_equivalents

def test_decitala_num_matras():
	frag = Decitala("Rajatala") # [1.0, 1.5, 0.25, 0.25, 1.0, 0.5, 1.5]
	assert frag.num_matras == 12
	
class TestMorrisSymmetryClass():
	
	def test_class_one(self): # X
		aditala = Decitala("Aditala")
		assert aditala.morris_symmetry_class() == 1

	def test_class_two(self): # XY
		iamb = GreekFoot("Iamb")
		assert iamb.morris_symmetry_class() == 2