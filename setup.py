####################################################################################################
# File:     setup.py
# Purpose:  Setup of the package. 
# 
# Author:   Luke Poeppel
#
# Location: Frankfurt, DE 2020
####################################################################################################
import os

from setuptools import setup, find_packages, Command

####################################################################################################
"""
Unfortunately, setuptools doesn't clean itself up after big changes. This function clears all of the 
build information/logs. 
"""
# Super useful helper function. https://stackoverflow.com/questions/3779915/why-does-python-setup-py-sdist-create-unwanted-project-egg-info-in-project-r
class CleanCommand(Command):
	"""Custom clean command to tidy up the project root."""
	user_options = []
	def initialize_options(self):
		self.cwd = None
	def finalize_options(self):
		self.cwd = os.getcwd()
	def run(self):
		assert os.getcwd() == self.cwd, 'Must be in package root: %s' % self.cwd
		os.system('rm -vrf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info')
####################################################################################################

__VERSION__ = "0.1.0"

# Can eventually replace this with a loop through os.listdir.
__MODULES__ = ["decitala.fragment", "decitala.utils"] #"decitala.trees", #"decitala.pofp", "decitala.database", "decitala.utils"]

setup(
	name="decitala",
	version=__VERSION__, 
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
		"kdtree",
		"numpy",
	],
	cmdclass={
		'clean': CleanCommand,
	}
)