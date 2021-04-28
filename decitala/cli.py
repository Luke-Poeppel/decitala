####################################################################################################
# File:     cli.py
# Purpose:  Command line interface for the decitala package.
#
# Author:   Luke Poeppel
#
# Location: Frankfurt, DE 2020 / NYC, 2020 / Kent, 2020
####################################################################################################
import click
import json

from decitala import __version__
from .search import path_finder
from .fragment import FragmentEncoder
from .utils import get_logger
from .hash_table import DecitalaHashTable, GreekFootHashTable

logger = get_logger(name=__file__)

@click.group()
@click.version_option(__version__, "--version", "-v", message="%(version)s")
def decitala():
	"""Returns the version of the module."""
	pass

@decitala.command()
@click.option("--filepath", default="", help="Path to filepath parsed for analysis.")
@click.option("--part_num", default=0, help="Part number.")
@click.option("--frag_type", default="greek_foot")
@click.option("--verbose", default=True)
def path_finder(filepath, part_num, frag_type, verbose):
	if frag_type == "decitala":
		table = DecitalaHashTable()
	elif frag_type == "greek_foot":
		table = GreekFootHashTable()
	
	best_path = path_finder(
		filepath=filepath,
		part_num=part_num,
		table=table,
		verbose=verbose
	)
	json_dumped_res = json.dumps(obj=best_path, cls=FragmentEncoder, indent=4)
	logger.info(json_dumped_res)
	filename = filepath.split("/")[-1][:-4] + f"_part_num={part_num}_frag_type={frag_type}.json"
	with open(filename, "w") as output:
		json.dump(obj=best_path, fp=output, cls=FragmentEncoder, indent=4)
	logger.info(f"Result saved in: {filename}")


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