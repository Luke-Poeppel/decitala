import os
version_file = os.path.abspath("VERSION")
with open(version_file) as version:
	__version__ = version.readline()