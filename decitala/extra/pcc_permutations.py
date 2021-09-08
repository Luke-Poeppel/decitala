"""
File for generating a JSON file that holds permutations of the monophonic
prime pitch contour classes with their associated fuzzy set-theoretic
transformations.
"""
import copy
import json

from decitala.hm import contour

def add_swaps(tuple_in, name, transformation, dict_in):
	i = 0
	while i < len(tuple_in) - 1:
		pcc_cpy = copy.deepcopy(list(tuple_in))
		pcc_cpy[i], pcc_cpy[i + 1] = pcc_cpy[i + 1], pcc_cpy[i]
		if tuple(pcc_cpy) not in dict_in:
			dict_in[tuple(pcc_cpy)] = (name, transformation, i)
		i += 1

def make_pcc_json(save_path):
	pcc_data = dict()
	for cc, name in contour.PRIME_CONTOUR_CLASSES.items():
		ret = cc[::-1]
		inv = tuple(contour.invert_contour(cc))
		ret_inv = tuple(contour.invert_contour(cc)[::-1])

		pcc_data[cc] = (name, "P")  # Prime
		if ret not in pcc_data:
			pcc_data[cc[::-1]] = (name, "R")  # Retrograde

		if inv not in pcc_data:
			pcc_data[inv] = (name, "I")  # Inversion

		if ret_inv not in pcc_data:
			pcc_data[ret_inv] = (name, "RI")  # Retrograde-Inversion

		add_swaps(cc, name, "P", pcc_data)
		add_swaps(ret, name, "R", pcc_data)
		add_swaps(inv, name, "I", pcc_data)
		add_swaps(ret_inv, name, "RI", pcc_data)

	pcc_data = {str(x): y for x, y in pcc_data.items()}
	with open(save_path, "w") as fp:
		json.dump(obj=pcc_data, fp=fp, indent=4)
	return

# make_pcc_json(save_path="/Users/lukepoeppel/decitala/decitala/extra/PCC_permutation_data.json")