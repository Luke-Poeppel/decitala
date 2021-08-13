import doctest
import numpy as np

from decitala.hm import contour, contour_utils

def test_doctests():
	assert doctest.testmod(contour, raise_on_error=True)
	assert doctest.testmod(contour_utils, raise_on_error=True)

def test_get_initial_extrema():
	c = [0, 3, 2, 1, 1, 1, 1, 1, 1] # From Alouette 17
	expected = [
		[0, {-1, 1}],
		[3, {1}],
		[2, set()],
		[1, {-1}],
		[1, {-1, 1}],
		[1, {-1, 1}],
		[1, {-1, 1}],
		[1, {-1, 1}],
		[1, {-1, 1}]
	]
	assert contour._track_extrema(c) == expected

# Examples from the Schultz article.
def test_immediately_flagged_prime_contours_morris():
	# See page 97
	contour_1 = [2, 4, 1, 5, 0, 6, 3]
	contour_2 = [2, 1, 3, 0]

	prime_contour_1 = contour.prime_contour(contour_1)
	expected_prime_contour_1 = [2, 4, 1, 5, 0, 6, 3]
	assert prime_contour_1[0] == expected_prime_contour_1
	assert prime_contour_1[1] == 0
	
	prime_contour_2 = contour.prime_contour(contour_2)
	assert prime_contour_2[0] == [2, 1, 3, 0]
	assert prime_contour_2[1] == 0

def test_contours_morris():
	c = [1, 3, 1, 2, 0, 1, 4]
	calculated = contour.prime_contour(contour=c)
	assert calculated[0] == [1, 0, 2]
	assert calculated[1] == 3

# All Schultz relevant tests are in tests/test_schultz.