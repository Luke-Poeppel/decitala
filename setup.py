import setuptools

__VERSION__ = "0.1.0"

__MODULES__ = ["decitala.decitala", "decitala.trees"]

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
		"numpy"
	]
)