import doctest

from decitala.hm import schultz
from decitala.hm import contour

def test_doctests():
	assert doctest.testmod(schultz, raise_on_error=True)

####################################################################################################
# Tools
def test_has_intervening_extrema_min():
	# intervening maximum between indices 1 and 3?
	window = [(1, [0, {-1}]), (3, [0, {-1}])]
	c = [[1, {1, -1}], [0, {-1}], [2, {1}], [0, {-1}], [2, {1}], [1, {1, -1}]]
	mode = "min"

	expected = True
	calculated = schultz._window_has_intervening_extrema(
		window=window,
		contour=c,
		mode=mode
	)
	assert calculated == True

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

def test_no_schultz_repetition():
	c = [[1, {1, -1}], [3, {1}], [0, {-1}], [3, {1}], [2, {1, -1}]]
	checked = schultz._no_schultz_repetition(c)
	assert checked == True

def test_remove_flags_except_flags_except_closest():
	contour = [
		[1, {1, -1}],
		[3, {1}],
		[0, {-1}],
		[3, {1}],
		[0, {-1}],
		[3, {1}],
		[0, {-1}],
		[3, {1}],
		[2, {1, -1}]
	]
	calculated = schultz._schultz_remove_flag_repetitions_except_closest(contour)[0]
	expected = [[1, {1, -1}], [3, {1}], [0, set()], [3, set()], [0, set()], [3, set()], [0, set()], [3, {1}], [2, {1, -1}]]
	assert calculated == expected

####################################################################################################
# Examples

def test_contour_ex15a_schultz():
	# See p. 109
	c = [1, 0, 2, 0, 2, 1]
	calculated = schultz.spc(contour=c)

	expected = [1, 0, 2, 1]
	expected_depth = 2  # hm...

	assert calculated[0] == expected
	assert calculated[1] == expected_depth

def test_contour_ex15b_schultz():
	# See p. 110
	c = [1, 3, 0, 3, 0, 3, 0, 3, 2]
	calculated = schultz.spc(contour=c)

	expected = [1, 3, 0, 3, 2]
	expected_depth = 2

	assert calculated[0] == expected
	assert calculated[1] == expected_depth

# print(test_contour_ex15b_schultz())

class TestSchultzNightingle:

	def test_nightingale_3_schultz(self):
		pitches = [68, 68, 79, 68, 68, 74, 66, 68, 81]
		nightingale_3 = [1, 1, 3, 1, 1, 2, 0, 1, 4]

		expected = [1, 0, 2]

		schultz_contour = contour.spc(nightingale_3)
		assert schultz_contour[0] == expected

	def test_nightingale_8_schultz(self):
		pitches = [81, 70, 70, 66, 79]
		nightingale_8 = [3, 1, 1, 0, 2, 2, 2, 2]

		expected = [2, 0, 1]

		schultz_contour = schultz.spc(nightingale_8)
		assert schultz_contour[0] == expected

	def test_nightingale_9_schultz(self):
		pitches = [68, 79, 68, 79, 68, 79, 68, 79, 68, 79, 68, 79]
		nightingale_9 = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]

		expected = [0, 1]

		schultz_contour = schultz.spc(nightingale_9)
		assert schultz_contour[0] == expected
	
	def test_nightingale_17_schultz(self):
		pitches = [73, 89, 86, 75, 75, 75, 75, 75, 75]
		nightingale_17 = [0, 3, 2, 1, 1, 1, 1, 1, 1]

		assert contour.pitch_contour(pitches) == nightingale_17

		expected = [0, 2, 1]
		schultz_contour = contour.spc(nightingale_17)
		assert schultz_contour[0] == expected

# From Wallentinsen PhD Thesis. See p. 15.
def test_wallentinsen_example():
	c = [2, 4, 1, 5, 0, 6, 3]
	calculated = schultz.spc(contour=c)

	assert calculated[0] == [1, 0, 3, 2]
	assert calculated[1] == 2

# class TestLongContour:

# 	def test_long_contour_b(self):
# 		c = [1, 4, 3, 6, 7, 5, 8, 5, 4, 0, 2, 1, 1, 1, 6, 1, 6, 3, 4, 1, 8, 0]
# 		calculated = schultz.spc(contour=c)
# 		assert calculated[0] == [1, 1, 2, 0]
		
# 	def test_long_contour_c(self):
# 		c = [1, 8, 6, 0, 8, 1, 4, 1, 7, 3, 4, 6, 2, 8, 6, 5, 1, 0]
# 		calculated = schultz.spc(contour=c)
# 		assert calculated[0] == [1, 1, 2, 0]

# def test_long_contour_a():
# 	c = [6, 1, 4, 4, 7, 0, 9, 8, 8, 1, 7, 3, 5, 0, 6, 1, 1, 0, 7, 2, 7, 6]
# 	calculated = schultz.spc(contour=c)
# 	assert calculated[0] == [1, 0, 2, 1]

# print(test_long_contour_a())

# # Unsure about this...
# def test_long_contour_d():
# 	c = [0, 1, 0, 0, 0, 2, 1, 0, 1, 0, 1, 0, 1, 1, 1, 2, 0, 2]
# 	calculated = schultz.spc(contour=c)
# 	return calculated

# def test_long_contour_e():
# 	c = [2, 4, 1, 3, 1, 5, 1, 6, 1, 1, 6, 7, 4, 1, 1, 1, 1, 0, 5, 1, 1, 7]
# 	calculated = schultz.spc(contour=c)
# 	return calculated

# print(test_long_contour_e())