import doctest
import os

from decitala.hm import molt
from decitala.database.db import Transcription, Species

def test_doctests():
	assert doctest.testmod(molt, raise_on_error=True)