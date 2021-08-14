import copy
import doctest

from decitala.hm import contour_utils

def test_doctests():
	assert doctest.testmod(contour_utils, raise_on_error=True)

def test_adjacent_repetition():
	"""
	From Morris (1993: 213). Unflag all but one, unless first-last conditions.
	"""
	c = [[0, {1, -1}], [4, set()], [2, {-1}], [5, {1}], [5, {1}], [1, {1, -1}]]
	contour_utils._adjacency_and_intervening_checks(c, mode="max", algorithm="morris")
	assert c == [[0, {1, -1}], [4, set()], [2, {-1}], [5, {1}], [5, set()], [1, {1, -1}]]

def test_has_intervening_extrema_max():
	"""
	Example for checking when only a single value, in this case the ending, is flagged.
	"""
	window = [(1, [1, set()]), (3, [1, set()]), (5, [1, set()]), (7, [1, set()]), (9, [1, set()]), (11, [1, {-1, 1}])]
	c = [[0, {1, -1}], [1, set()], [0, set()], [1, set()], [0, set()], [1, set()], [0, set()], [1, set()], [0, set()], [1, set()], [0, set()], [1, {-1, 1}]]
	mode = "max" # Unneeded. 

	expected = True
	calculated = contour_utils._window_has_intervening_extrema(
		window=window,
		contour=c,
		mode=mode
	)
	assert expected == calculated

def test_has_intervening_extrema_min():
	# intervening maximum between indices 1 and 3?
	window = [(1, [0, {-1}]), (3, [0, {-1}])]
	c = [[1, {1, -1}], [0, {-1}], [2, {1}], [0, {-1}], [2, {1}], [1, {1, -1}]]
	mode = "min"

	expected = True
	calculated = contour_utils._window_has_intervening_extrema(
		window=window,
		contour=c,
		mode=mode
	)
	assert calculated == True