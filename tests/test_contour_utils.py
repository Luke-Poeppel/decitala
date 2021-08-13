from decitala.hm import contour_utils

def test_doctests():
	assert doctest.testmod(contour_utils, raise_on_error=True)

def test_recheck():
	curr = [
		[1, {1, -1}],
		[3, {1}],
		[3, {1, -1}],
		[3, {1, -1}],
		[3, {1, -1}],
		[3, {1}],
		[0, {-1}],
		[0, {1, -1}],
		[0, {1, -1}],
		[0, {1, -1}],
		[0, {1, -1}],
		[0, {1, -1}],
		[0, {1, -1}],
		[0, {1, -1}],
		[0, {1, -1}],
		[0, {-1}],
		[4, {1, -1}]
	]
	cpy = copy.deepcopy(curr)
	contour_utils._recheck_extrema(cpy, mode="max")
	assert cpy == curr

def test_adjacent_repetition():
	"""
	From Morris (1993: 213). Unflag all but one, unless first-last conditions.
	"""
	c = [[0, {1, -1}], [4, set()], [2, {-1}], [5, {1}], [5, {1}], [1, {1, -1}]]
	contour_utils._adjacency_and_intervening_checks(c, mode="max", algorithm="morris")
	assert c == [[0, {1, -1}], [4, set()], [2, {-1}], [5, {1}], [5, set()], [1, {1, -1}]]