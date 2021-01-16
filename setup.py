####################################################################################################
# File:     setup.py
# Purpose:  Setup of the package. 
# 
# Author:   Luke Poeppel
#
# Location: Frankfurt, DE 2020 / NYC, 2020 / Kent, CT 2020
####################################################################################################
import os

from setuptools import setup, find_packages, Command

with open(os.path.join("decitala", "VERSION")) as version:
	__version__ = version.readline()

__MODULES__ = [
	"decitala.cli", 
	"decitala.database", 
	"decitala.fragment", 
	"decitala.pofp",
	"decitala.trees", 
	"decitala.utils", 
	"decitala.vis",
]

setup(
	name="decitala",
	version=__version__, 
	py_modules=__MODULES__,
	author="Luke Poeppel",
	author_email="luke.poeppel@gmail.com",
	description="Automated ethnological analysis of Olivier Messiaen's music.",
	long_description="Automated ethnological analysis of Olivier Messiaen's music.",
	long_description_content_type="text/markdown",
	url="https://github.com/Luke-Poeppel/decitala",
	packages=find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	python_requires='>=3.7',
	include_package_data=True,
	install_requires=[
		"click",
		"collections",
		"itertools",
		"jsonpickle",
		"matplotlib",
		"more-itertools",
		"numpy",
		"pandas",
		"progress",
		"pytest",
		"pre-commit",
		"sqlite3",
		"timeout-decorator",
	],
	entry_points={
		"console_scripts": [
			"decitala = decitala.cli:decitala"
		]
	}
)