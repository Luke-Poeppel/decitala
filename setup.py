"""
# https://stackoverflow.com/questions/27784271/how-can-i-use-setuptools-to-generate-a-console-scripts-entry-point-which-calls

entry_points = {
	"console_scripts": [
		"decitala = decitala.database:cli",
	]
}
"""
import setuptools

__VERSION__ = "0.1.0"

# Can eventually replace this with a loop through os.listdir.
__MODULES__ = ["decitala.fragment", "decitala.trees", "decitala.pofp", "decitala.database"]

setuptools.setup(
	name="decitala",
	version=__VERSION__, 
	py_modules=__MODULES__,
	author="Luke Poeppel",
	author_email="luke.poeppel@gmail.com",
	description="Automated ethnological analysis of Olivier Messiaen's music.",
	long_description="Automated ethnological analysis of Olivier Messiaen's music.",
	long_description_content_type="text/markdown",
	url="https://github.com/Luke-Poeppel/decitala",
	packages=setuptools.find_packages(),
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
)