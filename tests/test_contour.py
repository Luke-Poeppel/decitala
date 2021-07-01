import doctest
import numpy as np

from decitala.hm import contour

def test_doctests():
	assert doctest.testmod(contour, raise_on_error=True)

# Examples from the Schultz article.
def test_immediately_flagged_prime_contours_morris():
	# See page 97
	contour_1 = [2, 4, 1, 5, 0, 6, 3]
	contour_2 = [2, 1, 3, 0]

	prime_contour_1 = contour.contour_to_prime_contour(contour_1, include_depth=True)
	expected_prime_contour_1 = [2, 4, 1, 5, 0, 6, 3]
	assert list(prime_contour_1[0]) == expected_prime_contour_1
	assert prime_contour_1[1] == 0
	
	prime_contour_2 = list(contour.contour_to_prime_contour(contour_2))
	expected_prime_contour_2 = [2, 1, 3, 0]
	assert prime_contour_2 == expected_prime_contour_2

def test_contours_morris():
	c = [1, 3, 1, 2, 0, 1, 4]
	calculated = contour.contour_to_prime_contour(contour=c, include_depth=True)
	assert list(calculated[0]) == [1, 0, 2]
	assert calculated[1] == 3

def test_has_intervening_extrema():
	window = [(1, [0, {-1}]), (3, [0, {-1}])]
	c = [[1, {1, -1}], [0, {-1}], [2, {1}], [0, {-1}], [2, {1}], [1, {1, -1}]]
	mode = "min"

	expected = True
	calculated = contour._window_has_intervening_extrema(
		window=window,
		contour=c,
		mode=mode
	)
	assert expected == calculated

def test_contour_ex15a_schultz():
	# See p. 109
	c = [1, 0, 2, 0, 2, 1]
	calculated = contour.contour_to_schultz_prime_contour(contour=c)

	expected = [1, 0, 2, 1]
	expected_depth = 2  # hm...

	assert list(calculated[0]) == expected
	assert calculated[1] == expected_depth

# def test_contour_ex15b_schultz():
# 	# See p. 110
# 	c = [1, 3, 0, 3, 0, 3, 0, 3, 2]
# 	calculated = contour.contour_to_schultz_prime_contour(contour=c)
# 	print(calculated)

# 	expected = [1, 3, 0, 3, 2]
# 	expected_depth = 2
# # 	# assert list(calculated[0]) == expected

# print(test_contour_ex15b_schultz())