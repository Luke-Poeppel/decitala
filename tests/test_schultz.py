import doctest

from decitala.hm import schultz
from decitala.hm import contour

def test_doctests():
	assert doctest.testmod(schultz, raise_on_error=True)

def test_has_intervening_extrema_min():
	window = [(1, [0, {-1}]), (3, [0, {-1}])]
	c = [[1, {1, -1}], [0, {-1}], [2, {1}], [0, {-1}], [2, {1}], [1, {1, -1}]]
	mode = "min"

	expected = True
	calculated = schultz._window_has_intervening_extrema(
		window=window,
		contour=c,
		mode=mode
	)
	assert expected == calculated

def test_has_intervening_extrema_max():
	"""
	Example for checking when only a single value, in this case the ending, is flagged.
	"""
	window = [(1, [1, set()]), (3, [1, set()]), (5, [1, set()]), (7, [1, set()]), (9, [1, set()]), (11, [1, {-1, 1}])]
	c = [[0, {1, -1}], [1, set()], [0, set()], [1, set()], [0, set()], [1, set()], [0, set()], [1, set()], [0, set()], [1, set()], [0, set()], [1, {-1, 1}]]
	mode = "max" # Unneeded. 

	expected = True
	calculated = schultz._window_has_intervening_extrema(
		window=window,
		contour=c,
		mode=mode
	)
	assert expected == calculated

print(test_has_intervening_extrema_max())

def test_no_schultz_repetition():
	c = [[1, {1, -1}], [3, {1}], [0, {-1}], [3, {1}], [2, {1, -1}]]
	checked = schultz._no_schultz_repetition(c)
	assert checked == True

def test_contour_ex15a_schultz():
	# See p. 109
	c = [1, 0, 2, 0, 2, 1]
	calculated = schultz.spc(contour=c)

	expected = [1, 0, 2, 1]
	expected_depth = 2  # hm...

	assert list(calculated[0]) == expected
	assert calculated[1] == expected_depth

def test_contour_ex15b_schultz():
	# See p. 110
	c = [1, 3, 0, 3, 0, 3, 0, 3, 2]
	calculated = schultz.spc(contour=c)

	expected = [1, 3, 0, 3, 2]
	expected_depth = 2

	assert list(calculated[0]) == expected
	assert calculated[1] == expected_depth

def test_alouette_17_schultz():
	pitches = [73, 89, 86, 75, 75, 75, 75, 75, 75]
	alouette_17 = [0, 3, 2, 1, 1, 1, 1, 1, 1]

	assert list(contour.pitch_contour(pitches)) == alouette_17

	expected = [0, 2, 1]
	schultz_contour = contour.spc(alouette_17)
	assert list(schultz_contour[0]) == expected

def test_alouette_3_schultz():
	pitches = [68, 68, 79, 68, 68, 74, 66, 68, 81]
	alouette_3 = [1, 1, 3, 1, 1, 2, 0, 1, 4]

	expected = [1, 0, 2]

	schultz_contour = contour.spc(alouette_3)
	assert list(schultz_contour[0]) == expected

def test_alouette_8_schultz():
	pitches = [81, 70, 70, 66, 79]
	alouette_8 = [3, 1, 1, 0, 2, 2, 2, 2]

	expected = [2, 0, 1]

	schultz_contour = schultz.spc(alouette_8)
	assert list(schultz_contour[0]) == expected

def test_alouette_9_schultz():
	pitches = [68, 79, 68, 79, 68, 79, 68, 79, 68, 79, 68, 79]
	alouette_9 = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]

	expected = [0, 1]

	schultz_contour = schultz.spc(alouette_9)
	assert list(schultz_contour[0]) == expected

# print(test_alouette_9_schultz())

# def test_long_schultz_contour():
# 	c = [6, 1, 4, 4, 7, 0, 9, 8, 8, 1, 7, 3, 5, 0, 6, 1, 1, 0, 7, 2, 7, 6]
# 	print(contour.schultz_prime_contour(c))

# print(test_long_schultz_contour())