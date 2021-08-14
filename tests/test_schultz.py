import doctest
import copy

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

# From Wallentinsen Masters Thesis. See p. 15.
def test_wallentinsen_example():
	c = [2, 4, 1, 5, 0, 6, 3]
	calculated = schultz.spc(contour=c)

	assert calculated[0] == [1, 0, 3, 2]
	assert calculated[1] == 2

def test_trivial():
	c = [0, 0, 0, 0, 0, 0]
	calculated = schultz.spc(contour=c)
	assert calculated[0] == [0, 0]

ROSSIGNOL_DATA = [
	[92, 90, 92, 90, 92, 90, 92, 90, 86, 93, 80],
	[92, 90, 92, 90, 92, 90, 92, 90, 86, 93, 80, 80, 80, 86, 93, 80, 80, 80],
	[80, 80, 91, 80, 80, 86, 78, 80, 93],
	[78, 78, 78, 78, 78, 78, 78, 78, 78, 78, 78, 89],
	[86, 92, 90, 84, 91, 91, 91, 78, 78, 78, 78, 78, 78, 78, 78, 78],
	[89, 78, 78, 78, 78, 78, 78, 78, 78, 86, 80, 93],
	[89, 83, 89, 83, 89, 83, 89, 83, 86, 80, 93],
	[93, 82, 82, 78, 91, 91, 91, 91],
	[80, 91, 80, 91, 80, 91, 80, 91, 80, 91, 80, 93],
	[93, 93, 93, 80, 80, 91, 80, 91, 80, 91, 80, 91, 80, 91, 80, 91, 80, 91],
	[89, 89, 89, 89, 89, 89, 89, 78, 80, 93],
	[83, 89, 83, 89, 89, 78, 78, 78],
	[80, 86, 88, 88, 88, 88, 88, 78, 78, 78, 78, 78, 78, 78, 78, 78, 78, 91],
	[93, 93, 93, 80, 86, 93],
	[80, 91, 78, 78, 78, 78, 78, 78, 78, 78, 78, 78],
	[91, 91, 81, 86, 89, 78, 84, 86, 75, 92, 78, 89, 78, 78, 78, 78, 78, 78, 78, 78, 78, 92],
	[73, 89, 86, 75, 75, 75, 75, 75, 75]
]

class TestSchultzNightingle:

	def test_nightingale_3_schultz(self):
		pitches = [68, 68, 79, 68, 68, 74, 66, 68, 81]
		nightingale_3 = [1, 1, 3, 1, 1, 2, 0, 1, 4]

		expected = [1, 0, 2]

		schultz_contour = contour.spc(nightingale_3)
		assert schultz_contour[0] == expected
	
	def test_nightingale_6_shultz():
		pitches = [89, 78, 78, 78, 78, 78, 78, 78, 78, 86, 80, 93]
		nightingale_6 = contour.pitch_contour(pitches)

		expected = [1, 0, 2]

		schultz_contour = schultz.spc(nightingale_6)
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
	
	def test_nightingale_13_schultz(self):
		pitches = [80, 86, 88, 88, 88, 88, 88, 78, 78, 78, 78, 78, 78, 78, 78, 78, 78, 91]
		nightingale_13 = contour.pitch_contour(pitches)
		expected = [1, 0, 2]

		calculated = schultz.spc(nightingale_13)[0]
		assert calculated == expected
	
	def test_nightingale_17_schultz(self):
		pitches = [73, 89, 86, 75, 75, 75, 75, 75, 75]
		nightingale_17 = [0, 3, 2, 1, 1, 1, 1, 1, 1]
		
		assert contour.pitch_contour(pitches) == nightingale_17

		expected = [0, 2, 1]
		schultz_contour = contour.spc(nightingale_17)
		assert schultz_contour[0] == expected

class TestLongContour:
	def test_long_contour_a(self):
		c = [6, 1, 4, 4, 7, 0, 9, 8, 8, 1, 7, 3, 5, 0, 6, 1, 1, 0, 7, 2, 7, 6]
		calculated = schultz.spc(contour=c)
		assert calculated[0] == [1, 0, 2, 1]
		
	def test_long_contour_b(self):
		c = [1, 4, 3, 6, 7, 5, 8, 5, 4, 0, 2, 1, 1, 1, 6, 1, 6, 3, 4, 1, 8, 0]
		calculated = schultz.spc(contour=c)
		assert calculated[0] == [1, 2, 2, 0]
		
	def test_long_contour_c(self):
		c = [1, 8, 6, 0, 8, 1, 4, 1, 7, 3, 4, 6, 2, 8, 6, 5, 1, 0]
		calculated = schultz.spc(contour=c)
		assert calculated[0] == [1, 2, 2, 0]

	def test_long_contour_d(self):
		c = [0, 1, 0, 0, 0, 2, 1, 0, 1, 0, 1, 0, 1, 1, 1, 2, 0, 2]
		calculated = schultz.spc(contour=c)[0]
		assert calculated == [0, 1]

	def test_long_contour_e(self):
		c = [2, 4, 1, 3, 1, 5, 1, 6, 1, 1, 6, 7, 4, 1, 1, 1, 1, 0, 5, 1, 1, 7]
		calculated = schultz.spc(contour=c)[0]
		assert calculated == [1, 0, 2]