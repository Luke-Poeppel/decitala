import doctest
import os

from decitala.hm import molt
from decitala.database.db import Transcription, Species

here = os.path.abspath(os.path.dirname(__file__))
filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

def test_doctests():
	assert doctest.testmod(molt, raise_on_error=True)

def test_pc_counter_no_normalization():
	predicted = {
		0: 0,
		1: 2,
		2: 0,
		3: 1,
		4: 2,
		5: 3,
		6: 2,
		7: 0,
		8: 4,
		9: 2,
		10: 0,
		11: 0
	}
	calculated = molt.pc_counter(filepath, 0, normalize_over_duration=False)
	assert predicted == calculated