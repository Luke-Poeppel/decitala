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
import sys
import doctest

from decitala import __version__
from . import (
	search,
	fragment,
	utils,
	hash_table,
	database,
	trees
)

from .path_finding import (
	dijkstra,
	floyd_warshall,
	path_finding_utils,
	pofp
)
from .hm import (
	contour,
	molt,
	hm_utils,
	schultz
)

ALL_MODULES = [
	contour,
	database,
	fragment,
	utils,
	trees,
	search,
	hash_table,
	dijkstra,
	floyd_warshall,
	path_finding_utils,
	pofp,
	schultz,
	molt,
	hm_utils
]

logger = utils.get_logger(name=__file__)

@click.group()
@click.version_option(__version__, "--version", "-v", message="%(version)s")
def decitala():
	"""Returns the version of the module."""
	pass

def doctest_runner(module=None):
	if module:
		logger.info("Testing: {}".format(module))
		logger.info(doctest.testmod(module))
	else:
		logger.info("Running all doctests...")
		for this_module in ALL_MODULES:
			logger.info("Testing: {}".format(this_module))
			logger.info(doctest.testmod(this_module))

@decitala.command()
@click.option("--module", default="", help="A module in the decitala package to doctest")
def dtest(module):
	if module:
		arg_in = sys.argv[-1]
		if arg_in:
			mod = globals()[arg_in]
			doctest_runner(module=mod)
	else:
		doctest_runner()

@decitala.command()
@click.option("--filepath", default="", help="Path to filepath parsed for analysis.")
@click.option("--part_num", default=0, help="Part number.")
@click.option("--frag_type", default="greek_foot")
@click.option("--verbose", default=True)
def path_finder(filepath, part_num, frag_type, verbose): # noqa
	if frag_type == "decitala":
		table = hash_table.DecitalaHashTable()
	elif frag_type == "greek_foot":
		table = hash_table.GreekFootHashTable()

	best_path = path_finder(
		filepath=filepath,
		part_num=part_num,
		table=table,
		verbose=verbose
	)
	json_dumped_res = json.dumps(obj=best_path, cls=fragment.FragmentEncoder, indent=4)
	logger.info(json_dumped_res)
	filename = filepath.split("/")[-1][:-4] + f"_part_num={part_num}_frag_type={frag_type}.json"
	with open(filename, "w") as output:
		json.dump(obj=best_path, fp=output, cls=fragment.FragmentEncoder, indent=4)
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