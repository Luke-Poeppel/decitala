####################################################################################################
# File:     dijkstra_gif.py
# Purpose:  Scripts for generating the core databases in the package.
#
# Author:   Luke Poeppel
#
# Location: Kent, 2021
####################################################################################################
import matplotlib.pyplot as plt
import matplotlib as mpl
import subprocess
import itertools
import random
import shutil
import os
import natsort

from decitala import search
from decitala.path_finding import (
	path_finding_utils,
	dijkstra
)
from decitala.utils import get_logger
from decitala.hash_table import DecitalaHashTable

mpl.style.use("bmh")

def _stupid_flatten(data):
	"""
	Little utility function used in the GIF maker from imagemagick.
	"""
	out = []
	for val in data:
		if isinstance(val, list):
			out.extend(_stupid_flatten(val))
		else:
			out.append(val)
	return out

def _plot_base(all_data, title=None):
	"""
	Plots the base data.
	"""
	xs = [x.onset_range[0] for x in all_data]
	ys = [x.onset_range[1] for x in all_data]
	plt.scatter(xs, ys, s=5, color="k")

	plt.xticks(fontname="Times")
	plt.xlabel("Offset Start", fontname="Times", fontsize=12)
	plt.yticks(fontname="Times")
	plt.ylabel("Offset End", fontname="Times", fontsize=12)

	if title:
		plt.title(title, fontname="Times", fontsize=14)

def _dijkstra_gif_pair(i, data, pair, title=None, save_path=None):
	plt.text(0.05, pair[1].onset_range[1], f"Pair {i}...", fontname="Times")
	_plot_base(data)

	plt.scatter(pair[0].onset_range[0], pair[0].onset_range[1], marker="d", s=25, color="g")
	plt.scatter(pair[1].onset_range[0], pair[1].onset_range[1], marker="d", s=25, color="g")

	curr_path = save_path + f"/f{(5 * i) + 1}.png"
	plt.savefig(curr_path, dpi=150)
	for j in range(4):
		shutil.copyfile(curr_path, save_path + f"/f{(5 * i) + 2 + j}.png")

def _dijkstra_gif_animate_path(i, all_data, pair, cost_function, title=None, save_path=None):
	path = dijkstra.naive_dijkstra_path(
		data=all_data,
		source=pair[0],
		target=pair[1]
	)
	path = sorted([x for x in all_data if x.id_ in path], key=lambda x: x.onset_range[0])
	j = 0
	while j < len(path):
		plt.text(0.05, pair[1].onset_range[1], f"Pair {i}...", fontname="Times")
		_plot_base(all_data)
		plt.scatter(pair[0].onset_range[0], pair[0].onset_range[1], marker="d", s=25, color="g")
		plt.scatter(pair[1].onset_range[0], pair[1].onset_range[1], marker="d", s=25, color="g")

		xs = [x.onset_range[0] for x in path[0:j + 1]]
		ys = [x.onset_range[1] for x in path[0:j + 1]]
		plt.plot(xs, ys, "--o", color="r", markersize=3, linewidth=1)

		out = os.path.join(save_path, f"animate_path_{i}_elem{j}.png")
		plt.savefig(out, dpi=150)
		plt.clf()
		j += 1

def _gif_from_source(fps, rate, save_path, logger):
	run_elems = [
		"convert",
		"-delay",
		f"{rate}",
		fps,
		"-loop",
		"0",
		save_path,
	]
	logger.info("Creating component GIF...")
	subprocess.run(_stupid_flatten(run_elems))

def dijkstra_gif(
		filepath,
		part_num,
		table,
		windows=list(range(2, 19)),
		allow_subdivision=False,
		allow_contiguous_summation=False,
		cost_function_class=path_finding_utils.CostFunction3D(),
		split_dict=None,
		slur_constraint=False,
		enforce_earliest_start=False,
		title=None,
		rate=20,
		show=False,
		save_path=None
	):
	"""
	Function for creating a GIF file of the Dijkstra algorithm for a given
	filepath-part-num combination using imagemagick. Only supports animation
	for Dijkstra at the moment (not Floyd-Warshall).

	:param str save_path: path to a folder that will be created. This folder will contain the
							GIF file along with a subfolder containing the source images for
							the GIF.
	"""
	if not(save_path):
		raise Exception("No path provided.")

	logger = get_logger(name=__file__)

	os.mkdir(save_path)
	################################################################################################
	# Base Plot.
	all_data = search.rolling_hash_search(
		filepath=filepath,
		part_num=part_num,
		table=table,
		windows=windows,
		allow_subdivision=allow_subdivision,
		allow_contiguous_summation=allow_contiguous_summation
	)
	xs = [x.onset_range[0] for x in all_data]
	ys = [x.onset_range[1] for x in all_data]
	plt.scatter(xs, ys, s=5, color="k")

	plt.xticks(fontname="Times")
	plt.xlabel("Offset Start", fontname="Times", fontsize=12)
	plt.yticks(fontname="Times")
	plt.ylabel("Offset End", fontname="Times", fontsize=12)

	if title:
		plt.title(title, fontname="Times", fontsize=14)
	plt.tight_layout()

	logger.info("Saving base image...")
	base_path = save_path + "/f1.png"
	plt.savefig(base_path, dpi=150)
	for i in range(2, 6):
		shutil.copyfile(base_path, save_path + f"/f{i}.png")

	plt.clf()
	################################################################################################
	# Plot each pair
	sources, sinks = path_finding_utils.sources_and_sinks(
		data=all_data,
		enforce_earliest_start=enforce_earliest_start
	)
	pairs = list(itertools.product(sources, sinks))
	random.shuffle(pairs)

	# REMOVE –– JUST FOR TESTING
	pairs = pairs[0:2]

	for i, pair in enumerate(pairs, start=1):
		logger.info(f"Writing pair {i}")
		_dijkstra_gif_pair(i, all_data, pair, title, save_path)
		plt.clf()
		_dijkstra_gif_animate_path(i, all_data, pair, cost_function_class, title=title, save_path=save_path) # noqa

	################################################################################################
	# Making the component GIFS:
	for i in range(1, len(pairs) + 1):
		curr_path_source = []
		for fp in os.listdir(save_path):
			if fp.startswith(f"animate_path_{i}"):
				curr_path_source.append(os.path.join(save_path, fp))
		curr_path_source = natsort.natsorted(curr_path_source)
		curr_gif_path = os.path.join(save_path, f"path_{i}_gif.gif")
		_gif_from_source(fps=curr_path_source, rate=5, save_path=curr_gif_path, logger=logger)

	# gif_filepath = os.path.join(save_path, "final.gif")
	# file_order = [os.path.join(save_path, f"f{i}.png") for i in range(1, len(os.listdir(save_path)) + 1)] # noqa

	################################################################################################
	# Combining the component GIFS.

	################################################################################################
	if show:
		plt.show()

def test_dijkstra_gif():
	fp = "/Users/lukepoeppel/Messiaen/Encodings/Sept_Haikai/1_Introduction.xml"
	import uuid
	dijkstra_gif(
		filepath=fp,
		part_num=0,
		table=DecitalaHashTable(),
		allow_subdivision=True,
		title="Iterated Dijkstra on Sept Haïkaï (Bois)",
		save_path=f"/Users/lukepoeppel/decitala/tests/dijkstra_gif_tests/dijkstra_{uuid.uuid4().hex}",
		show=False
	)

# print(test_dijkstra_gif())