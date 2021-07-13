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

	prime_contour_1 = contour.contour_to_prime_contour(contour_1)
	expected_prime_contour_1 = [2, 4, 1, 5, 0, 6, 3]
	assert list(prime_contour_1[0]) == expected_prime_contour_1
	assert prime_contour_1[1] == 0
	
	prime_contour_2 = contour.contour_to_prime_contour(contour_2)
	assert list(prime_contour_2[0]) == [2, 1, 3, 0]
	assert prime_contour_2[1] == 0

def test_contours_morris():
	c = [1, 3, 1, 2, 0, 1, 4]
	calculated = contour.contour_to_prime_contour(contour=c)
	assert list(calculated[0]) == [1, 0, 2]
	assert calculated[1] == 3

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
	assert contour._get_initial_extrema(c) == expected

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

def test_no_schultz_repetition():
	c = [[1, {1, -1}], [3, {1}], [0, {-1}], [3, {1}], [2, {1, -1}]]
	checked = contour._no_schultz_repetition(c)
	assert checked == True

####################################################################################################
# SCHULTZ TEST
class TestSchultz:
	def test_contour_ex15a_schultz(self):
		# See p. 109
		c = [1, 0, 2, 0, 2, 1]
		calculated = contour.contour_to_schultz_prime_contour(contour=c)

		expected = [1, 0, 2, 1]
		expected_depth = 2  # hm...

		assert list(calculated[0]) == expected
		assert calculated[1] == expected_depth

	def test_contour_ex15b_schultz(self):
		# See p. 110
		c = [1, 3, 0, 3, 0, 3, 0, 3, 2]
		calculated = contour.contour_to_schultz_prime_contour(contour=c)

		expected = [1, 3, 0, 3, 2]
		expected_depth = 2

		assert list(calculated[0]) == expected
		assert calculated[1] == expected_depth

	def test_alouette_17_schultz(self):
		pitches = [73, 89, 86, 75, 75, 75, 75, 75, 75]
		alouette_17 = [0, 3, 2, 1, 1, 1, 1, 1, 1]

		assert list(contour.pitch_content_to_contour(pitches)) == alouette_17

		expected = [0, 2, 1]
		schultz_contour = contour.contour_to_schultz_prime_contour(alouette_17)
		assert list(schultz_contour[0]) == expected

	def test_alouette_3_schultz(self):
		pitches = [68, 68, 79, 68, 68, 74, 66, 68, 81]
		alouette_3 = [1, 1, 3, 1, 1, 2, 0, 1, 4]

		expected = [1, 0, 2]

		schultz_contour = contour.contour_to_schultz_prime_contour(alouette_3)
		assert list(schultz_contour[0]) == expected

	def test_alouette_8_schultz(self):
		pitches = [81, 70, 70, 66, 79]
		alouette_8 = [3, 1, 1, 0, 2, 2, 2, 2]

		expected = [2, 0, 1]

		schultz_contour = contour.contour_to_schultz_prime_contour(alouette_8)
		assert list(schultz_contour[0]) == expected

	def test_alouette_9_schultz(self):
		pitches = [68, 79, 68, 79, 68, 79, 68, 79, 68, 79, 68, 79]
		alouette_9 = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]

		expected = [0, 1]

		schultz_contour = contour.contour_to_schultz_prime_contour(alouette_9)
		assert list(schultz_contour[0]) == expected

####################################################################################################
class TestContourSymmetries:
	def test_contour_symmetry_a(self):
		contour_a = (1, 3, 0, 2)
		expected = 	("P", 0)
		calculated = contour.contour_symmetry(contour_a, contour_a)
		return expected == calculated

	def test_commutativity_i(self):
		contour_a = (1, 3, 0, 2)
		forward = contour.invert_contour(contour_a)
		out = contour.invert_contour(forward)
		assert out == list(contour_a)

	def test_commutativity_ri(self):
		contour_a = (1, 3, 0, 2)
		forward = contour.retrograde_invert_contour(contour_a)
		out = contour.retrograde_invert_contour(forward)
		assert out == list(contour_a)

# # def test_contour_symmetry_b():
# # 	contour_a = (1, 3, 0, 2)
# # 	# RI: (1, 0, 2, 3)
# # 	contour_b = (0, 2, 3, 1)
# # 	expected =  ("RI", 1)
# # 	calculated = contour.contour_symmetry(contour_a, contour_b)
# # 	assert expected == calculated

# # print(test_contour_symmetry_b())

# def test_contour_retrograde_inversion():
# 	c = (1, 3, 0, 2)
# 	assert(contour.retrograde_invert_contour(c)) == (1, 0, 2, 3)