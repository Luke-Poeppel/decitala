version_file = "/Users/lukepoeppel/decitala/decitala/VERSION"
with open(version_file) as version:
	__version__ = version.readline()