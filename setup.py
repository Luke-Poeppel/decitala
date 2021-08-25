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
		"jsonpickle",
		"matplotlib",
		"more-itertools",
		"music21>=6.5.0",
		"natsort",
		"numpy>=1.16.5",
		"pandas",
		"progress",
		"sqlalchemy",
		"scipy",
		"tqdm",
		"treeplotter==0.4.3",
		"unidecode",
		"Wand",
		"librosa"
	],
	extras_require={
		"dev": [
			"flake8",
			"pre-commit",
			"pytest",
			"sphinx_rtd_theme",
		]
	},
	entry_points={
		"console_scripts": [
			"decitala = decitala.cli:decitala"
		]
	},
)