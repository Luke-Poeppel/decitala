####################################################################################################
# File:     cli.py
# Purpose:  Command line interface for the decitala package. 
# 
# Author:   Luke Poeppel
#
# Location: Frankfurt, DE 2020 / NYC, 2020 / Kent, 2020
####################################################################################################
import click
import os
import pathlib

from progress.bar import Bar

from decitala import __version__
from .vis import make_tree_diagram
from .trees import FragmentTree
from .database import create_database

@click.group()
@click.version_option(__version__, "--version", "-v", message="%(version)s")
def decitala():
	"""Returns the version of the module."""
	pass

@decitala.command()
@click.option('--verbose', is_flag=True, help="Will print verbose messages.")
@click.option('--name', default='', help="What's your name?")
def cli(verbose, name):
	if verbose:
		click.echo("You are in verbose mode.")
	click.secho("Hello, World!", fg="blue", bold=True)
	click.secho("This is a command line tool test.")
	click.echo(":-) {}".format(name))

@decitala.command()
@click.option("--filepath", default="", help="Path to filepath parsed for the database.")
@click.option("--part", default=0, help="Part number.")
@click.option("--fragtype", default=["decitala"])
@click.option("--mods", default=["ratio", "retrograde"], help="Allowed modifications of fragments in the database.")
@click.option("--verbose", default=True)
def make_db(filepath, part, fragtype, mods, verbose):
	"""Creates a database in your home directory."""
	filename = filepath.split('/')[-1][:-4]
	create_database(
		db_path=str(pathlib.Path.home()) + "/" + filename, 
		filepath=filepath,
		part_num=part, 
		frag_types=fragtype,
		allowed_modifications=mods,
		verbose=verbose,
	)
	
# @decitala.command()
# @click.option("--data", default="", help="Path to database of rhythmic fragments.")
# @click.option("--frag_type", default="", help="Type of fragment; either `decitala` or `greek_foot`.")
# @click.option("--rep_type", default="", help="Representation of fragment; `ratio` or `difference`.")
# @click.option("--destination", default="", help="Destination of tree diagram.")
# def draw_tree(data, destination, frag_type, rep_type):
# 	fragment_tree = FragmentTree(data, frag_type, rep_type)
# 	make_tree_diagram(fragment_tree, destination)