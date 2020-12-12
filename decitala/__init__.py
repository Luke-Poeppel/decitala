import os
with open(os.path.join("decitala", "VERSION")) as version:
	__version__ = version.readline()