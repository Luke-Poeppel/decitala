####################################################################################################
# File:     setup.py
# Purpose:  Setup of the package.
#
# Author:   Luke Poeppel
#
# Location: Frankfurt, DE 2020 / NYC, 2020 / Kent, CT 2020
####################################################################################################
import os

from setuptools import setup, find_packages

with open(os.path.join("decitala", "VERSION")) as version:
	__version__ = version.readline()

setup(
	name="decitala",
	version=__version__,
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
	package_data={"decitala": ["VERSION"]},
	install_requires=[
		"click",
		"flake8",
		"jsonpickle",
		"matplotlib",
		"more-itertools",
		"music21>=6.5.0",
		"numpy>=1.16.5",
		"pandas",
		"progress",
		"pre-commit",
		"pytest",
		"sqlalchemy",
		"scipy",
		"sphinx_rtd_theme",
		"Wand",
		"natsort",
	],
	entry_points={
		"console_scripts": [
			"decitala = decitala.cli:decitala"
		]
	},
)