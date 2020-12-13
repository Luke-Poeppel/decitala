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

class CleanCommand(Command):
	"""
	setuptools doesn't always clean itself up after big changes. This useful function clears all of the 
	build information/logs. https://stackoverflow.com/questions/3779915/why-does-python-setup-py-sdist-create-unwanted-project-egg-info-in-project-r
	"""
	user_options = []
	def initialize_options(self):
		self.cwd = None
	def finalize_options(self):
		self.cwd = os.getcwd()
	def run(self):
		assert os.getcwd() == self.cwd, 'Must be in package root: %s' % self.cwd
		os.system('rm -vrf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info')

__MODULES__ = [
	"decitala.cli", 
	"decitala.database", 
	"decitala.fragment", 
	"decitala.paths",
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
		"ast",
		"click",
		"collections",
		"itertools",
		"more-itertools",
		"jsonpickle",
		"numpy",
		"sqlite3",
		"matplotlib"
	],
	cmdclass={
		'clean': CleanCommand,
	},
	entry_points={
		"console_scripts": [
			"decitala = decitala.cli:decitala"
		]
	}
)