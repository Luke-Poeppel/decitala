import doctest
import numpy as np

from decitala.hm import contour

def test_doctests():
	assert doctest.testmod(contour, raise_on_error=True)

# Examples from the Schultz article.
def test_prime_contour():
	contour_1 = [2, 4, 1, 5, 0, 6, 3]
	contour_2 = [2, 1, 3, 0]

	assert np.array_equal(contour.contour_to_prime_contour(contour_1), np.array([2, 4, 1, 5, 0, 6, 3]))
	assert np.array_equal(contour.contour_to_prime_contour(contour_2), np.array([2, 1, 3, 0]))