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
import os
import natsort

from decitala import search
from decitala.path_finding import (
	path_finding_utils,
	dijkstra
)
from decitala.utils import get_logger

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

def _gif_from_source(fps, rate=None, save_path=None):
	if rate is not None:
		run_elems = ["convert", "-delay", f"{rate}", fps, "-loop", "0", save_path]
	else:
		run_elems = ["convert", fps, save_path]
	subprocess.run(_stupid_flatten(run_elems))

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

def _dijkstra_gif_animate_path(
		i,
		all_data,
		pair,
		cost_function,
		split_dict,
		dpi,
		title=None,
		save_path=None
	):
	path = dijkstra.naive_dijkstra_path(
		data=all_data,
		source=pair[0],
		target=pair[1]
	)
	path = sorted([x for x in all_data if x.id_ in path], key=lambda x: x.onset_range[0])
	path = path_finding_utils.split_extractions(
		data=path,
		split_dict=split_dict,
		all_res=all_data
	)
	net_cost = round(path_finding_utils.net_cost(path), 2)
	j = 0
	while j < len(path):
		plt.text(
			0.05,
			all_data[-2].onset_range[1] - 5,
			f"Pair {i}. Net Cost = {net_cost}",
			fontname="Times",
			fontsize=13,
			weight="bold"
		)
		_plot_base(all_data)
		plt.scatter(pair[0].onset_range[0], pair[0].onset_range[1], marker="d", s=25, color="g")
		plt.scatter(pair[1].onset_range[0], pair[1].onset_range[1], marker="d", s=25, color="g")

		xs = [x.onset_range[0] for x in path[0:j + 1]]
		ys = [x.onset_range[1] for x in path[0:j + 1]]
		plt.plot(xs, ys, "--o", color="r", markersize=3, linewidth=1)

		if title:
			plt.title(title, fontname="Times", fontsize=12)

		out = os.path.join(save_path, f"animate_path_{i}_elem{j}.png")
		plt.savefig(out, dpi=dpi)
		plt.clf()
		j += 1

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
		num_pairs=None,
		title=None,
		dpi=200,
		rate=20,
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
		raise Exception("No directory path provided.")

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
	################################################################################################
	# Plot each pair
	sources, sinks = path_finding_utils.sources_and_sinks(
		data=all_data,
		enforce_earliest_start=enforce_earliest_start
	)
	pairs = list(itertools.product(sources, sinks))
	random.shuffle(pairs)

	if num_pairs:
		pairs = pairs[:num_pairs]

	for i, pair in enumerate(pairs, start=1):
		logger.info(f"Writing pair {i}...")
		plt.clf()
		_dijkstra_gif_animate_path(i, all_data, pair, cost_function_class, split_dict, dpi=dpi, title=title, save_path=save_path) # noqa

	# ################################################################################################
	# Making the component GIFS:
	for i in range(1, len(pairs) + 1):
		curr_path_source = []
		for fp in os.listdir(save_path):
			if fp.startswith(f"animate_path_{i}"):
				curr_path_source.append(os.path.join(save_path, fp))
		curr_path_source = natsort.natsorted(curr_path_source)
		curr_gif_path = os.path.join(save_path, f"path_{i}.gif")
		_gif_from_source(fps=curr_path_source, rate=5, save_path=curr_gif_path)

	################################################################################################
	# Combining the component GIFS.
	final_filepath = os.path.join(save_path, "final.gif")
	curr_path_source_gifs = natsort.natsorted(
		[os.path.join(save_path, this_file) for this_file in os.listdir(save_path) if this_file.startswith("path_")] # noqa
	)
	components = [curr_path_source_gifs]
	_gif_from_source(fps=components, save_path=final_filepath)