####################################################################################################
# File:     trees.py
# Purpose:  NAry Tree representation of Fragment Trees and Search algorithms.
#
# Author:   Luke Poeppel
#
# Location: Kent, 2020 / Frankfurt, 2020
####################################################################################################
import os

from treeplotter.tree import (
	Node,
	Tree
)
from wand.image import Image

from .fragment import (
	GeneralFragment,
	get_all_decitalas,
	get_all_greek_feet
)
from .utils import (
	roll_window,
	get_object_indices,
)
from . import vis

class TreeException(Exception):
	pass

class FragmentTreeException(TreeException):
	pass

####################################################################################################
class FragmentTree(Tree):
	"""
	NaryTree that holds multiplicative or additive representations of a rhythmic dataset.
	This is just the parent class and shouldn't be called; instead, use the
	:obj:`decitala.trees.RatioTree` or :obj:`decitala.trees.DifferenceTree` classes.

	:param data: either a path to folder of music21-readable files or a list of
				:obj:`decitala.fragment.GeneralFragment` objects (or its subclasses).
	:param str name: optional name of the Fragment Tree.
	:raises `~decitala.trees.FragmentTreeException`: if an invalid path or list is provided
														to the ``data``.
	"""
	rep_type = None

	def __init__(self, data, name=None, **kwargs):
		self.name = name

		if isinstance(data, str):
			assert os.path.isdir(data), FragmentTreeException("Invalid path provided.")
			new_data = []
			for this_file in os.listdir(self.data):
				new_data.append(GeneralFragment(data=this_file))
			self.data = new_data
		elif isinstance(data, list):
			assert all(type(x).__name__ in ["GeneralFragment", "Decitala", "GreekFoot"] for x in data), FragmentTreeException("The elements of data must be GeneralFragment, \
																																Decitala, or GreekFoot objects.") # noqa
			self.data = data

		self.depth = max([len(x.ql_array()) for x in self.data])
		self.sorted_data = sorted(self.data, key=lambda x: len(x.ql_array()))

	@classmethod
	def from_frag_type(
			cls,
			frag_type,
		):
		"""
		Create a fragment tree from the data in fragment_database.db in the databases directory.

		:param str frag_type: determines the class defining the set of fragments.
							If the ``frag_type=='decitala'``, creates
							:obj:`~decitala.fragment.Decitala` objects; if
							``frag_type=='greek_foot'``,
							creates :obj:`~decitala.fragment.GreekFoot`.
							Otherwise creates
							:obj:`~decitala.fragment.GeneralFragment`
							(default) objects.
		"""
		if frag_type == "decitala":
			data = get_all_decitalas()
		elif frag_type == "greek_foot":
			data = get_all_greek_feet()

		return FragmentTree(
			data=data,
			name=f"{frag_type}"
		)

	@classmethod
	def from_composition(
			cls,
			filepath,
			part_num=0,
			windows=list(range(2, 10))
		):
		"""
		Class method for generating a FragmentTree from a composition.

		:param str filepath: path to file.
		:param int part: part number.
		:return: a FragmentTree made from a rolling window of a part in a composition.
		:rtype: :obj:`~decitala.trees.FragmentTree`
		"""
		assert os.path.isfile(filepath)
		assert type(part_num) == int

		object_list = get_object_indices(filepath=filepath, part_num=part_num)
		data = []
		for this_window in windows:
			frames = roll_window(array=object_list, window_size=this_window)
			for this_frame in frames:
				objects = [x[0] for x in this_frame]
				indices = [x[1] for x in this_frame]
				if any(x.isRest for x in objects):  # Skip any window that has a rest in it.
					continue
				else:
					as_quarter_lengths = []
					for this_obj, this_range in this_frame:
						as_quarter_lengths.append(this_obj.quarterLength)
					name = str(indices[0][0]) + "-" + str(indices[-1][-1])
					data.append(GeneralFragment(as_quarter_lengths, name=name))

		return FragmentTree(data=data)

	@classmethod
	def from_multiple_paths(
			self,
			paths,
			name=None
		):
		"""
		Create a FragmentTree from a list of paths (each a directory of music21-readable files).

		:param list paths: list of paths (each a string), each a directory of music21-readable
						files of rhythmic fragments.
		:return: a Fragment tree holding multiple paths of data.
		:rtype: :obj:`~decitala.trees.FragmentTree`
		"""
		assert all(os.path.isdir(path) for path in paths), TreeException("Not all provided paths \
																		are valid.")

		data = []
		for this_path in paths:
			for this_file in os.listdir(this_path):
				data.append(GeneralFragment(data=this_file))

		return FragmentTree(data=data, name=name)

	def show(self, save_path=None, verbose=False):
		"""
		The vis module uses the Treant.js library to create a tree diagram. The diagram is
		stored in an HTML file, but is saved as a PDF using the R webshot package. This function
		does not save the directory, but returns a wand.Image object (with optionally saving it).
		"""
		pdf_filepath = vis.create_tree_diagram(FragmentTree=self, verbose=verbose)
		img = Image(filename=pdf_filepath)

		if save_path is not None:
			img.save(filename=save_path)
		else:
			return img

class RatioTree(FragmentTree):
	"""
	A FragmentTree with a ``"ratio"`` representation. In this case, every fragment is
	represented by the ratio between all contiguous elements (normalized to start at 1).
	See :obj:`decitala.trees.FragmentTree` for the relevant methods.

	>>> ratio_tree = RatioTree.from_frag_type(frag_type="greek_foot")
	>>> ratio_tree
	<trees.FragmentTree greek_foot_ratio: nodes=35>
	>>> ratio_tree.search_for_path([1.0, 2.0, 0.5, 1.0]).name
	<fragment.GreekFoot Peon_II>
	"""
	rep_type = "ratio"

	def __init__(self, data, name=None, **kwargs):
		root_node = Node(value=1.0, name="ROOT")
		for this_fragment in self.sorted_data:
			path = list(this_fragment.successive_ratio_array())
			root_node.add_path_of_children(path=path, final_node_name=this_fragment)

		self.root = root_node
		super().__init__(data=data, name=name)

	def __repr__(self):
		if self.name:
			return '<trees.RatioTree {0}: nodes={1}>'.format(self.name, self.size())
		else:
			return '<trees.RatioTree: nodes={}>'.format(self.size())

class DifferenceTree(FragmentTree):
	"""
	A FragmentTree with a ``"difference"`` representation. In this case, every fragment is
	represented by its first-order differences, i.e. the differences between all contiguous
	elements (normalized to start at 0).
	See :obj:`decitala.trees.FragmentTree` for the relevant methods.

	>>> from decitala.fragment import Decitala, GreekFoot, GeneralFragment
	>>> g1 = GeneralFragment([1.0, 1.0, 1.0, 1.0, 1.0], name="myfragment")
	>>> g2 = Decitala("Ragavardhana")
	>>> g3 = GreekFoot("Ionic_Major")
	>>> data = [g1, g2, g3]
	>>> diff_tree = DifferenceTree(data=data, name="MyCoolDifferenceTree")
	>>> diff_tree
	<trees.DifferenceTree MyCoolDifferenceTree: nodes=10>
	>>> for frag in sorted(diff_tree.all_named_paths(), key=lambda x: x.name):
	...     print(frag)
	<fragment.Decitala 93_Ragavardhana>
	<fragment.GreekFoot Ionic_Major>
	<fragment.GeneralFragment myfragment: [1. 1. 1. 1. 1.]>
	"""
	rep_type = "difference"

	def __init__(self, data, name=None, **kwargs):
		super().__init__(data=data, name=name)
		root_node = Node(value=0.0, name="ROOT")
		for this_fragment in self.sorted_data:
			path = list(this_fragment.successive_difference_array())
			root_node.add_path_of_children(path=path, final_node_name=this_fragment)
		self.root = root_node

	def __repr__(self):
		if self.name:
			return '<trees.DifferenceTree {0}: nodes={1}>'.format(self.name, self.size())
		else:
			return '<trees.DifferenceTree: nodes={}>'.format(self.size())