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
	contour_c = [1, 3, 1, 2, 0, 1, 4]
	calculated = contour.contour_to_prime_contour(contour=contour_c, include_depth=3)
	assert list(calculated[0]) == [1, 0, 2]
	assert calculated[1] == 3