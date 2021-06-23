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

from decitala.fragment import (
	Decitala,
	GreekFoot,
	GeneralFragment,
	get_all_decitalas,
	get_all_greek_feet

)
from decitala.utils import (
	roll_window,
	get_object_indices,
)
from decitala.database.corpora_models import (
	DecitalaData,
	GreekFootData
)
from decitala import vis

class TreeException(Exception):
	pass

class FragmentTreeException(TreeException):
	pass

####################################################################################################
# KD-Tree (TODO)
class KDTree:
	class Node:
		def __init__(self):
			pass

	def __init__(self):
		pass

class FragmentTree(Tree):
	"""
	NaryTree that holds multiplicative or additive representations of a rhythmic dataset.

	:param str data: either a frag_type/rep_type combo, a path to folder of music21-readable files,
					or a list of fragments.
	:param str rep_type: determines the representation of the fragment. Options are ``ratio`` (default)
						and ``difference``.
	:param str name: optional name of the Fragment Tree.
	:raises `~decitala.trees.FragmentTreeException`: if an invalid path or rep_type is given.

	>>> ratio_tree = FragmentTree.from_frag_type(frag_type='greek_foot', rep_type='ratio')
	>>> ratio_tree
	<trees.FragmentTree greek_foot_ratio: nodes=36>
	>>> ratio_tree.search_for_path([1.0, 2.0, 0.5, 1.0]).name
	<fragment.GreekFoot Peon_II>
	>>> # We can also give it a name.
	>>> g1 = GeneralFragment([1.0, 1.0, 1.0, 1.0, 1.0], name="myfragment")
	>>> g2 = Decitala("Ragavardhana")
	>>> g3 = GreekFoot("Ionic_Major")
	>>> data = [g1, g2, g3]
	>>> mytree = FragmentTree(data = data, rep_type="difference", name="MyCoolTree")
	>>> mytree
	<trees.FragmentTree MyCoolTree: nodes=10>
	>>> for frag in sorted(mytree.all_named_paths(), key=lambda x: x.name):
	...     print(frag)
	<fragment.Decitala 93_Ragavardhana>
	<fragment.GreekFoot Ionic_Major>
	<fragment.GeneralFragment myfragment: [1. 1. 1. 1. 1.]>
	"""
	def __init__(self, data, rep_type, name=None, **kwargs):
		assert rep_type.lower() in ["ratio", "difference"], FragmentTreeException("The only possible rep_types are `ratio` and `difference`") # noqa

		self.rep_type = rep_type.lower()
		self.name = name

		if isinstance(data, str):
			assert os.path.isdir(data), FragmentTreeException("Invalid path provided.")
			new_data = []
			for this_file in os.listdir(self.data):
				new_data.append(GeneralFragment(data=this_file))

			self.data = data

		if isinstance(data, list):
			assert all(type(x).__name__ in ["GeneralFragment", "Decitala", "GreekFoot"] for x in data), FragmentTreeException("The elements of data must be GeneralFragment, \
																																Decitala, or GreekFoot objects.") # noqa
			self.data = data

		super().__init__()

		self.depth = max([len(x.ql_array()) for x in self.data])
		self.sorted_data = sorted(self.data, key=lambda x: len(x.ql_array()))

		if self.rep_type == "ratio":
			root_node = Node(value=1.0, name="ROOT")
			for this_fragment in self.sorted_data:
				path = list(this_fragment.successive_ratio_array())
				root_node.add_path_of_children(path=path, final_node_name=this_fragment)
			self.root = root_node

		if self.rep_type == "difference":
			root_node = Node(value=0.0, name="ROOT")
			for this_fragment in self.sorted_data:
				path = list(this_fragment.successive_difference_array())
				root_node.add_path_of_children(path=path, final_node_name=this_fragment)
			self.root = root_node

	def __repr__(self):
		if self.name:
			return '<trees.FragmentTree {0}: nodes={1}>'.format(self.name, self.size())
		else:
			return '<trees.FragmentTree: nodes={}>'.format(self.size())

	@classmethod
	def from_frag_type(
			cls,
			frag_type,
			rep_type
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
		assert frag_type.lower() in ["decitala", "greek_foot"], FragmentTreeException("The only \
																					possible frag_types are `decitala` and `greek_foot`.")
		assert rep_type.lower() in ["ratio", "difference"], FragmentTreeException("The only possible \
																				rep_types are `ratio` and `difference`")

		if frag_type == "decitala":
			data = get_all_decitalas()
		elif frag_type == "greek_foot":
			data = get_all_greek_feet()

		return FragmentTree(
			data=data,
			rep_type=rep_type,
			name="{0}_{1}".format(frag_type, rep_type),
		)

	@classmethod
	def from_composition(
			cls,
			filepath,
			part=0,
			rep_type="ratio",
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
		assert type(part) == int

		object_list = get_object_indices(filepath=filepath, part_num=part)
		data = []
		for this_window in windows:
			frames = roll_window(array=object_list, window_length=this_window)
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

		return FragmentTree(data=data, rep_type=rep_type)

	@classmethod
	def from_multiple_paths(
			self,
			paths,
			rep_type,
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

		return FragmentTree(data=data, rep_type=rep_type, name=name)

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