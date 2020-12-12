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

from progress.bar import Bar

from decitala import __version__
from .vis import make_tree_diagram
from .trees import FragmentTree

@click.group()
@click.version_option(__version__, "--version", "-v", message="%(version)s")
def decitala():
	"""
	Returns the version of the module
	"""
	pass

@decitala.command()
@click.option('--verbose', is_flag=True, help="Will print verbose messages.")
@click.option('--name', default='', help="What's ur name?")
def cli(verbose, name):
	if verbose:
		click.echo("You are in verbose mode.")
	click.secho("Hello, World!", fg="blue", bold=True)
	click.secho("This is a command line tool test.")
	click.echo(":-) {}".format(name))

@decitala.command()
@click.option("--path", default="", help="Path to filepath parsed for the database.")
@click.option("--part", default=0, help="Part number.")
@click.option("--mods", default=["ratio", "retrograde"], help="Allowed modifications of fragments in the database.")
@click.option("--filt1", default=True, help="Whether or not to filter single-anga class talas.")
@click.option("--filt2", default=True, help="Whether or not to filter subtalas.")
def create_db(path, part, mods, filt1, filt2):
	"""
	Creates a database in the current working directory. 
	"""
	click.secho("Creating sqlite database...", fg="blue", bold=True)
	filename_w_extension = path.split('/')[-1]
	filename_wo_extension = filename_w_extension[:-4]
	db_filepath = os.getcwd() + '/filename_wo_extension' + '.db'
	click.secho("Database location: {}".format(db_filepath))
	
	# create_database(path, part, mods, db_filepath, filt1, filt2)
	
	click.secho("Finished creating database.", fg="blue", bold=True)

#"/Users/lukepoeppel/moiseaux/Europe/I_La_Haute_Montagne/La_Niverolle/XML/niverolle_3e_example.xml"

@decitala.command()
@click.option("--data", default="", help="Path to database of rhythmic fragments.")
@click.option("--frag_type", default="", help="Type of fragment; either `decitala` or `greek_foot`.")
@click.option("--rep_type", default="", help="Representation of fragment; `ratio` or `difference`.")
@click.option("--destination", default="", help="Destination of tree diagram.")
def draw_tree(data, destination, frag_type, rep_type):
	fragment_tree = FragmentTree(data, frag_type, rep_type)
	make_tree_diagram(fragment_tree, destination)