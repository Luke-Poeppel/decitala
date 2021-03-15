####################################################################################################
# File:     cli.py
# Purpose:  Command line interface for the decitala package.
#
# Author:   Luke Poeppel
#
# Location: Frankfurt, DE 2020 / NYC, 2020 / Kent, 2020
####################################################################################################
import click
import pathlib
import json

from decitala import __version__
from .database import create_database
from .fragment import FragmentEncoder, FragmentDecoder
from .hash_table import DecitalaHashTable, GreekFootHashTable
from .search import path_finder
from .path_finding import floyd_warshall

@click.group()
@click.version_option(__version__, "--version", "-v", message="%(version)s")
def decitala():
	"""Returns the version of the module."""
	pass

@decitala.command()
@click.option("--filepath", default="", help="Path to filepath parsed for analysis.")
@click.option("--part_num", default=0, help="Part number.")
@click.option("--frag_type", default="greek_foot")
def pathfinder(filepath, part_num, frag_type):
	best_path = path_finder(
		filepath,
		part_num,
		frag_type
	)

	filename = filepath.split("/")[-1][:-4] + "_part_num={0}_frag_type={1}.txt".format(part_num, frag_type)
	analysis = open(filename, "w")
	analysis.write(str(best_path))  # json.dumps(json.loads(data_dumped, cls=FragmentDecoder), cls=FragmentEncoder, indent=4))
	analysis.close()

# @decitala.command()
# @click.option("--filepath", default="", help="Path to filepath parsed for the database.")
# @click.option("--part", default=0, help="Part number.")
# @click.option("--fragtype", default=["decitala"])
# @click.option("--mods", default=["ratio", "retrograde"], help="Allowed modifications of fragments in the database.") # noqa
# @click.option("--verbose", default=True)
# def create_db(filepath, part, fragtype, mods, verbose):
# 	"""Creates a database in your home directory."""
# 	filename = filepath.split('/')[-1][:-4]
# 	create_database(
# 		db_path=str(pathlib.Path.home()) + "/" + filename,
# 		filepath=filepath,
# 		part_num=part,
# 		frag_types=fragtype,
# 		allowed_modifications=mods,
# 		verbose=verbose,
# 	)