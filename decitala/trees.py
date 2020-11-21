# -*- coding: utf-8 -*-
####################################################################################################
# File:     trees.py
# Purpose:  NAry Tree representation of Fragment Trees and Search algorithms.
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
import copy
import decimal
import itertools
import json
import math
import numpy as np
import os
import re

from music21 import converter
from music21 import stream

from fragment import Decitala

from tools import (
	_euclidian_norm,
	cauchy_schwartz,
	roll_window,
	get_indices_of_object_occurrence,
	successive_ratio_array,
	successive_difference_array
)

decitala_path = '/Users/lukepoeppel/decitala/Fragments/Decitalas'
greek_path = '/Users/lukepoeppel/decitala_v2/Greek_Metrics/XML'

############### EXCEPTIONS ###############
class TreeException(Exception):
	pass

class FragmentTreeException(TreeException):
	pass

############### EXCEPTIONS ###############
class NaryTree(object):
	"""
	A single-rooted nary tree for ratio and difference representations of rhythmic fragments. Nodes are 
	hashed by their value and are stored in a set. For demonstration, we will create the following tree: 
	(If a string appears next to a node value, this means the path from the root to that node is an encoded fragment.) 

	>>> root = NaryTree().Node(value = 1.0, name = None) # LEVEL 1
	>>> c1 = NaryTree().Node(value = 0.5, name = None) # LEVEL 2				
	>>> c2 = NaryTree().Node(value = 1.0, name = None)
	>>> c3 = NaryTree().Node(value = 3.0, name = 'A')
	>>> c3.value 
	3.0
	>>> gc1 = NaryTree().Node(value = 0.5, name = None) # LEVEL 3
	>>> gc2 = NaryTree().Node(value = 3.0, name = 'B')
	>>> gc3 = NaryTree().Node(value = 2.0, name = 'C')
	>>> ggc = NaryTree().Node(value = 1.0, name = 'D') # LEVEL 4
	>>> root.parent = None
	>>> root.children = {c1, c2, c3}
	>>> root.children
	{<NODE: value=0.5, name=None>, <NODE: value=1.0, name=None>, <NODE: value=3.0, name=A>}
	>>> c1 in root.children
	True
	>>> root.ordered_children()
	[<NODE: value=0.5, name=None>, <NODE: value=1.0, name=None>, <NODE: value=3.0, name=A>]
	>>> c1.add_children([gc1, gc2])
	>>> c1.num_children
	2
	>>> c2.add_child(gc3)
	>>> gc1.add_child(ggc)
	>>> root.add_path_of_children(path = [root.value, 4.0, 1.0, 0.5, 2.0], final_node_name = 'Full Path')
	>>> root.children
	{<NODE: value=0.5, name=None>, <NODE: value=1.0, name=None>, <NODE: value=3.0, name=A>, <NODE: value=4.0, name=None>}
	>>> # Check for overwriting data...
	>>> root.add_path_of_children(path = [root.value, 1.0, 2.0, 1.0], final_node_name = 'Test Overwrite')
	>>> # We can access children by referencing a node or by calling to its representative value. 
	>>> newValue = root.get_child_by_value(4.0)
	>>> newValue.children
	{<NODE: value=1.0, name=None>}
	>>> c2.get_child(gc3)
	<NODE: value=2.0, name=C>
	>>> c2.get_child_by_value(2.0)
	<NODE: value=2.0, name=C>
	>>> c2.get_child_by_value(4.0)
	>>> TestTree = NaryTree()
	>>> TestTree.root = root
	>>> TestTree
	<NaryTree: nodes=13>
	>>> TestTree.is_empty()
	False
	>>> # Calling the size returns the number of nodes in the tree. 
	>>> TestTree.size()
	13
	>>> TestTree.all_possible_paths()
	[1.0]
	[1.0, 0.5]
	[1.0, 0.5, 0.5]
	[1.0, 0.5, 0.5, 1.0]
	[1.0, 0.5, 3.0]
	[1.0, 1.0]
	[1.0, 1.0, 2.0]
	[1.0, 1.0, 2.0, 1.0]
	[1.0, 3.0]
	[1.0, 4.0]
	[1.0, 4.0, 1.0]
	[1.0, 4.0, 1.0, 0.5]
	[1.0, 4.0, 1.0, 0.5, 2.0]
	>>> # Get paths of a particular length:
	>>> for this_path in TestTree.all_named_paths(cutoff = 3):
	...     print(this_path)
	B
	C
	>>> # We can search for paths as follows. 
	>>> TestTree.search_for_path([1.0, 0.5, 0.5, 1.0])
	'D'
	>>> TestTree.search_for_path([1.0, 0.5, 3.0])
	'B'
	>>> TestTree.search_for_path([1.0, 2.0, 4.0])
	>>> TestTree.search_for_path([1.0, 1.0, 2.0])
	'C'
	>>> # Allow for unnamed paths to be found.
	>>> TestTree.search_for_path([1.0, 0.5, 0.5], allow_unnamed=True)
	[1.0, 0.5, 0.5]
	"""
	class Node(object):
		"""
		A Node object stores an item and references its parent and children. In an Nary tree, a parent
		may have any arbitrary number of children, but each child has only 1 parent. 
		"""
		def __init__(self, value, name = None, **kwargs):
			self.value = value
			self.name = name
			self.parent = None
			self.children = set()

		def __repr__(self):
			return '<NODE: value={0}, name={1}>'.format(self.value, self.name)

		def __hash__(self):
			return hash(self.value)

		def __eq__(self, other):
			"""
			Without this, you can add nodes with the same value to the set of children.
			"""
			return (self.value == other.value) 

		def __lt__(self, other):
			return (self.value < other.value)

		def __get__(self):
			"""
			TODO: index the node children? 
			"""
			raise NotImplementedError

		def add_child(self, child_node):
			self.children.add(child_node)
			return

		def add_children(self, children_nodes = []):
			if type(children_nodes) != list: 
				raise TreeException('Nodes must be contained in a list.')
			
			for this_child in children_nodes:
				self.add_child(this_child)
			return

		def add_path_of_children(self, path, final_node_name):
			"""
			Adds a path of Nodes through ``self.children``. 
			"""
			if path[0] != self.value:
				raise TreeException("First value in the path must be self.value.")

			curr = self
			i = 1
			while i < len(path):
				check = curr.get_child_by_value(path[i])
				if check is not None:
					curr = check
					i += 1
				else:
					if i == len(path) - 1:
							child = NaryTree().Node(value = path[i], name = final_node_name)
					else:
						child = NaryTree().Node(value = path[i])

					curr.add_child(child)
					curr = child
					i += 1

			return

		def remove_child(self, child_node):
			if child_node.item.value not in self.children:
				raise TreeException("This parent does not have that child!")
			self.children.remove(child_node.item.value)
			return

		def remove_children(self, children_nodes):
			for this_child in children_nodes:
				try:
					self.remove_child(this_child)
				except KeyError:
					raise TreeException("One of the values in children_nodes was not found.")
			return

		def get_child(self, node):
			"""Given another Node, returns the node in the set of children with the same value."""
			for this_child in self.children:
				if this_child.value == node.value:
					return this_child
			else:
				return None

		def get_child_by_value(self, value):
			for this_child in self.children:
				if this_child.value == value:
					return this_child
			else:
				return None

		@property
		def num_children(self) -> int:
			return len(self.children)

		@property
		def has_children(self) -> bool:
			return (self.num_children != 0)

		def ordered_children(self):
			"""Returns the children of a node in list format, ordered by value."""
			return sorted([child for child in self.children])

		def write_to_json(self):
			"""Used in the Treant.js visualization of Fragment trees."""
			net_children_data = []
			for this_child in self.children:
				data = {"info" : {"name" : this_child.name, "value" : this_child.value}}
				net_children_data.append(data)

			out = {'info' : {'name' : self.name, 'value' : self.value, 'children' : net_children_data}}
			return json.dumps(out)#, indent=4)

	def __init__(self):
		self.root = None

	def __repr__(self):
		return '<NaryTree: nodes={}>'.format(self.size())

	def __iter__(self):
		"""
		Iterates through all named paths in the tree (not nodes), beginning with the shortest paths 
		and ending with paths that end at the leaves. Ignores paths that do not end with a name. 
		"""
		for this_named_path in self.all_named_paths():
			yield this_named_path

	def _size_helper(self, node):
		"""Helper function for self.size()."""
		num_nodes = 1
		for child in node.children:
			num_nodes += self._size_helper(child)

		return num_nodes

	def size(self):
		"""Returns the number of nodes in the nary tree."""
		return self._size_helper(self.root)

	def is_empty(self) -> bool:
		return (self.size() == 0)

	################################################################################################
	def _all_possible_paths_helper(self, node, path = []):
		"""Helper function for self.all_possible_paths()."""
		path.append(node.value)
		print(path)
		if len(node.children) == 0:
			pass
		else:
			for child in node.children:
				self._all_possible_paths_helper(child, path)
		path.pop()

	def all_possible_paths(self):
		"""Returns all possible paths from the root node, not all of which are necesarrily named."""
		return self._all_possible_paths_helper(self.root)

	def _all_named_paths_helper(self, node, cutoff, path = []):
		"""Helper function for self.all_named_paths()."""
		path.append(node)

		if path[-1].name is not None:
			p = [node.value for node in path]
			if cutoff != 0:
				if len(p) == cutoff:
					yield path[-1].name
			else:
				if path[-1].name == 'ROOT':
					pass
				else:
					yield path[-1].name
		else:
			pass

		if len(node.children) == 0:
			pass
		else:
			for child in node.children:
				yield from self._all_named_paths_helper(node = child, cutoff = cutoff, path = path)

		path.pop()

	def all_named_paths(self, cutoff=0):
		"""
		Returns all named paths from the root. An optional ``cutoff`` parameter restricts to paths of 
		length :math:`n`.  
		"""
		for this_named_path in self._all_named_paths_helper(node = self.root, cutoff = cutoff):
			yield this_named_path

	# Sub and super paths
	# Should maybe also have sub/super paths by path. 
	def _subpaths_helper(self, node):
		raise NotImplementedError 

	def subpaths(self, name):
		"""Given a name (hopefully attached to a node), returns a list of the subpaths "below" that node."""
		raise NotImplementedError

	def _superpaths_helper(self, node):
		raise NotImplementedError

	def superpaths(self, name):
		"""Given a name (hopefully attached to a node), returns a list of the subpaths "above" that node."""
		raise NotImplementedError

	################################################################################################
	def search_for_path(self, path_from_root, allow_unnamed=False):
		"""
		Searches for ``path_from_root`` through the tree for a continuous path to a node. 
		:param numpy.array path_from_root: path to search in tree.
		:param bool allow_unnamed: whether or not to allow for unnamed paths to be found. 
		:return: either the name of the final node or, if ``allow_unnamed=True``, possibly ``path_from_root``.
		:raises `decitala.trees.TreeException`: when an invalid path or representation type is provided.
		"""
		assert path_from_root[0] == 0.0 or path_from_root[0] == 1.0
		if len(path_from_root) < 2:
			raise TreeException("Path provided must be at least 2 values long.")

		curr = self.root
		i = 1
		while i < len(path_from_root):
			try:
				curr = curr.get_child_by_value(value = path_from_root[i])
				if curr is None:
					return None
			except AttributeError:
				break
			
			if allow_unnamed == False:
				if (i == len(path_from_root) - 1) and len(curr.children) == 0:
					return curr.name
				elif (i == len(path_from_root) - 1) and curr.name is not None:
					return curr.name
				else:
					i += 1
			else:
				if (i == len(path_from_root) - 1):
					return path_from_root
				else:
					i += 1

	def ld_search(self, path_from_root, allow_unnamed=False):
		"""
		This is a special use case in :obj:`decitala.trees.get_by_ql_array` based on the observation 
		that the difference representation of mixed augmentations are linearly dependent. In this search
		tool, rather than checking if a path exists in a tree, we check on a level-order basis 
		for a node for which the input is linearly dependent. 
		"""
		raise NotImplementedError

####################################################################################################
class FragmentTree(NaryTree):
	"""
	NaryTree that holds multiplicative and additive representations of a rhythmic dataset. 

	:param str data_path: path to folder of music21-readable files.
	:param str frag_type: determines the class defining the set of fragments. 
					If the frag_type is `decitala`, creates :class:`decitala.fragment.Decitala` objects.
					If the frag_type is `greek_foot`, creates :class:`decitala.fragment.GreekFoot`.
					Otherwise creates :class:`decitala.fragment.GeneralFragment` objects.
	:param str rep_type: determines the representation of the fragment. Options are ``ratio`` and ``difference``.
	:raises `decitala.trees.FragmentTreeException`: when an invalid path or representation type is provided.

	>>> ratio_tree = FragmentTree(data_path=decitala_path, frag_type='decitala', rep_type='ratio')
	>>> ratio_tree.search_for_path([1.0, 1.0, 1.0, 1.0])
	<decitala.Decitala 84_Karanayati>
	"""
	def __init__(self, data_path, frag_type, rep_type, **kwargs):
		if type(data_path) != str:
			raise FragmentTreeException("Path must be a string.")
		
		if rep_type.lower() not in ['ratio', 'difference']:
			raise FragmentTreeException("The only possible types are `ratio` and `difference`")
		
		self.data_path = data_path
		self.frag_type = frag_type
		self.rep_type = rep_type

		super().__init__()

		if frag_type.lower() == 'decitala':
			raw_data = []
			for this_file in os.listdir(data_path):
				x = re.search(r'\d+', this_file)
				try:
					span_end = x.span()[1] + 1
					raw_data.append(Decitala(name=this_file[span_end:]))
				except AttributeError:
					pass

			self.raw_data = raw_data
		elif frag_type.lower() == 'greek_foot':
			raw_data = []
			for this_file in os.listdir(data_path):
				raw_data.append(GreekFoot(this_file))
			self.raw_data = raw_data
		else:
			raw_data = []
			for this_file in os.listdir(data_path):
				raw_data.append(GeneralFragment(this_file))
			self.raw_data = raw_data

		def filter_data(raw_data):
			"""
			Given a list of Decitala objects, filter_data() removes:
			- Single-onset fragments
			- Exact duplicate fragments
			- Multiplicative augmentation/diminution duplicates (using the Cauchy-Schwarz Inequality).

			For example, if we have the following set of fragments: 
			[3.0, 1.5, 1.5, 0.75, 0.75]
			[1.5, 1.0]
			[0.75, 0.5, 0.75]
			[0.25, 0.25, 0.5]
			[0.75, 0.5]
			[0.5, 1.0, 2.0, 4.0],
			[1.5, 1.0, 1.5],
			[1.0, 1.0, 2.0],
			[1.0, 0.5, 0.5, 0.25, 0.25],
			[0.25, 0.5, 1.0, 2.0]
			
			The function reduces this list to:
			[0.75, 0.5], 
			[0.75, 0.5, 0.75], 
			[0.25, 0.25, 0.5], 
			[0.25, 0.5, 1.0, 2.0], 
			[1.0, 0.5, 0.5, 0.25, 0.25]
			"""
			copied = copy.copy(raw_data)
			size = len(copied)

			i = 0
			while i < size:
				try:
					if len(copied[i].ql_array()) == 1:
						del copied[i]
					else:
						pass
				except IndexError:
					pass

				for j, _ in enumerate(copied):
					try: 
						if i == j:
							pass
						elif len(copied[i].ql_array()) != len(copied[j].ql_array()):
							pass
						elif cauchy_schwartz(copied[i].ql_array(), copied[j].ql_array()) == True:
							pass
						elif cauchy_schwartz(copied[i].ql_array(), copied[j].ql_array()) == False:
							firsti = copied[i].ql_array()[0]
							firstj = copied[j].ql_array()[0]

							#Equality removes the second one by convention
							if firsti == firstj:
								del copied[j]
							elif firsti > firstj:
								del copied[i]
							else:
								del copied[j]
						else:
							pass
					except IndexError:
						pass

				i += 1

			return copied

		self.filtered_data = filter_data(self.raw_data)

		if rep_type == 'ratio':
			root_node = self.Node(value = 1.0, name = 'ROOT')
	
			possible_num_onsets = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]
			i = 0
			while i < len(possible_num_onsets):
				curr_onset_list = []
				for thisTala in self.filtered_data:
					if len(thisTala.ql_array()) == possible_num_onsets[i]:
						curr_onset_list.append(thisTala)
				for thisTala in curr_onset_list:
					root_node.add_path_of_children(path = list(thisTala.successive_ratio_array()), final_node_name = thisTala)
				i += 1

			self.root = root_node
		
		if rep_type == 'difference':
			root_node = NaryTree().Node(value = 0.0, name = 'ROOT')

			possible_num_onsets = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]
			i = 0
			while i < len(possible_num_onsets):
				curr_onset_list = []
				for thisTala in self.filtered_data:
					if len(thisTala.ql_array()) == possible_num_onsets[i]:
						curr_onset_list.append(thisTala)
				for thisTala in curr_onset_list:
					root_node.add_path_of_children(path = thisTala.successive_difference_array(), final_node_name = thisTala)
				i += 1

			self.root = root_node

####################################################################################################
class SearchConfig():
	"""
	Messiaen alters rhythms in a complex and systemized way. We are often interested in restricting 
	the realm of search to specific modifications. As such, we supply the main search 
	function, :meth:`decitala.trees.get_by_ql_array`, with a config that dictates how to conduct
	the search. 
	"""
	def __init__(self, ql_array, ratio_tree, difference_tree, modifications):
		self.ql_array = ql_array
		self.ratio_tree = ratio_tree
		self.difference_tree = difference_tree
		self.modifications = modifications
		
	def __getitem__(self, modification):
		if modification not in self.modifications:
			raise Exceptions("'{0}' is not in '{1}'".format(modification, self.modifications))
	
		retrograde = self.ql_array[::-1]
		ratio_array = successive_ratio_array(self.ql_array)
		difference_array = successive_difference_array(self.ql_array)
		retrograde_ratio_array = successive_ratio_array(retrograde)
		retrograde_difference_array = successive_difference_array(retrograde)
		
		if modification == "ratio":
			return (self.ratio_tree, ratio_array)
		elif modification == "retrograde-ratio":
			return (self.ratio_tree, retrograde_ratio_array)
		elif modification == "difference":
			return (self.difference_tree, difference_array)
		elif modification == "retrograde-difference":
			return (self.difference_tree, retrograde_difference_array)
		else:
			return None
			
def _get_ratio_or_difference(input_fragment, found_fragment, modification):
	split_mod = modification.split("-")
	if "ratio" in split_mod:
		ratio = abs(input_fragment[0] / found_fragment.ql_array()[0])
		return (modification, ratio)
	else:
		difference = abs(input_fragment[0] - found_fragment.ql_array()[0])
		return (modification, difference)

def get_by_ql_array(
		ql_array,
		ratio_tree,
		difference_tree,
		allowed_modifications=["ratio", "retrograde-ratio", "difference", "retrograde-difference"],
		allow_unnamed=False
	):
	"""
	:param numpy.array ql_array: fragment to be searched.
	:param fragment.FragmentTree ratio_tree: tree storing ratio representations.
	:param fragment.FragmentTree difference_tree: tree storing difference representations.
	:param list allowed_modifications: possible ways for a fragment to be modified. 
									Current possibilities are ``ratio``, ``retrograde-ratio``, ``difference``, and ``retrograde-difference``.
									*NOTE*: the order of ``allowed_modifications`` is the order of the search. 
	:param bool allow_unnamed: whether or not to allow the retrieval of unnamed paths. Default is ``False``.
	
	>>> fragment = np.array([0.5, 0.5, 1.0, 1.0])
	>>> ratio_tree = FragmentTree(data_path=decitala_path, frag_type='decitala', rep_type='ratio')
	>>> difference_tree = FragmentTree(data_path=decitala_path, frag_type='decitala', rep_type='difference')
	>>> allowed_modifications = ["ratio", "retrograde-ratio"]
	>>> get_by_ql_array(fragment, ratio_tree, difference_tree, allowed_modifications)
	(<decitala.Decitala 32_Kudukka>, ('ratio', 2.0))
	"""
	tala = None
	config = SearchConfig(ql_array=ql_array, ratio_tree=ratio_tree, difference_tree=difference_tree, modifications=allowed_modifications)
	i = 0
	while i < len(allowed_modifications):
		curr_modification = allowed_modifications[i]
		search_tree, search_ql_array = config[curr_modification]
		search = search_tree.search_for_path(search_ql_array, allow_unnamed)
		if search is not None:
			tala = search
			change = _get_ratio_or_difference(ql_array, tala, curr_modification)
			break
		else:
			i += 1

	if tala:
		return (tala, change)
	else:
		return None

"""
ratio_tree = FragmentTree(data_path=decitala_path, frag_type='decitala', rep_type='ratio')
difference_tree = FragmentTree(data_path=decitala_path, frag_type='decitala', rep_type='difference')

frag = [0.125, 0.25, 0.125]
print(get_by_ql_array(frag, ratio_tree, difference_tree))"""

def rolling_search(
		filepath, 
		part_num, 
		ratio_tree, 
		difference_tree,
		windows=[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]
	):
	"""
	Rolling search on a music21-readable file on a given part. For search types, see 
	documentation for :func:`decitala.trees.get_by_ql_array`. The given window lengths 
	are the lengths of all the talas in the dataset. 

	:param str filepath: path to file to be searched.
	:param int part_num: part in the file to be searched (0-indexed).
	:param fragment.FragmentTree ratio_tree: tree storing ratio representations.
	:param fragment.FragmentTree difference_tree: tree storing difference representations.
	:param list windows: possible length of the search frame. 
	:return: list holding fragments in the array present in the trees.
	:rtype: list

	>>> ratio_tree = FragmentTree(data_path=decitala_path, frag_type='decitala', rep_type='ratio')
	>>> difference_tree = FragmentTree(data_path=decitala_path, frag_type='decitala', rep_type='difference')
	>>> ex = '/Users/lukepoeppel/moiseaux/Europe/I_La_Haute_Montagne/La_Niverolle/XML/niverolle_3e_example.xml'
	>>> for tala_data in rolling_search(ex, 0, ratio_tree, difference_tree)[0:5]:
	... 	print(tala_data)
	((<decitala.Decitala 5_Pancama>, ('ratio', 1.0)), (0.0, 0.5))
	((<decitala.Decitala 17_Yatilagna>, ('retrograde-ratio', 1.0)), (0.25, 0.625))
	((<decitala.Decitala 5_Pancama>, ('ratio', 0.5)), (0.5, 0.75))
	((<decitala.Decitala 17_Yatilagna>, ('ratio', 0.5)), (0.625, 1.0))
	((<decitala.Decitala 5_Pancama>, ('ratio', 1.0)), (0.75, 1.25))
	"""
	assert ratio_tree.rep_type == 'ratio'
	assert difference_tree.rep_type == 'difference'

	object_list = get_indices_of_object_occurrence(filepath = filepath, part_num = part_num)
	fragments_found = []
	for this_win in windows:
		for this_frame in roll_window(array = object_list, window_length = this_win):
			as_quarter_lengths = []
			for this_obj, thisRange in this_frame:
				if this_obj.isRest:
					if this_obj.quarterLength == 0.25: # zis iz a prroblem. 
						as_quarter_lengths.append(this_obj)
					else:
						pass
				as_quarter_lengths.append(this_obj.quarterLength)

			searched = get_by_ql_array(as_quarter_lengths, ratio_tree, difference_tree)
			if searched is not None:
				offset_1 = this_frame[0][0]
				offset_2 = this_frame[-1][0]

				fragments_found.append((searched, (offset_1.offset, offset_2.offset + offset_2.quarterLength)))
		
	return fragments_found

"""ratio_tree = FragmentTree(data_path=decitala_path, frag_type='decitala', rep_type='ratio')
difference_tree = FragmentTree(data_path=decitala_path, frag_type='decitala', rep_type='difference')

ex = '/Users/lukepoeppel/moiseaux/Europe/I_La_Haute_Montagne/La_Niverolle/XML/niverolle_3e_example.xml'
for tala_data in rolling_search(ex, 0, ratio_tree, difference_tree)[0:5]:
	print(tala_data)"""

def rolling_search_on_array(
		ql_array, 
		ratio_tree, 
		difference_tree, 
		windows=[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]
	):
	"""
	Rolling search for a fragment in a ratio and difference tree. For search types, 
	see documentation for :func:`decitala.trees.get_by_ql_array`. 

	:param numpy.array ql_array: fragment to be searched.
	:param fragment.FragmentTree ratio_tree: tree storing ratio representations.
	:param fragment.FragmentTree difference_tree: tree storing difference representations.
	:param list windows: possible length of the search frame. 
	:return: list holding fragments in the array present in the trees.
	:rtype: list

	>>> ratio_tree = FragmentTree(data_path=decitala_path, frag_type='decitala', rep_type='ratio')
	>>> difference_tree = FragmentTree(data_path=decitala_path, frag_type='decitala', rep_type='difference')
	>>> example_fragment = np.array([0.25, 0.5, 0.25, 0.5])
	>>> fragments_found = rolling_search_on_array(ql_array=example_fragment, ratio_tree=ratio_tree, difference_tree=difference_tree)
	>>> for x in fragments_found:
	...     print(x, x[0].ql_array())
	(<decitala.Decitala 17_Yatilagna>, ('ratio', 1.0)) [0.25 0.5 ]
	(<decitala.Decitala 17_Yatilagna>, ('retrograde-ratio', 2.0)) [0.25 0.5 ]
	(<decitala.Decitala 17_Yatilagna>, ('ratio', 1.0)) [0.25 0.5 ]
	(<decitala.Decitala 58_Dhenki>, ('ratio', 0.5)) [1.  0.5 1. ]
	"""
	assert ratio_tree.rep_type == 'ratio'
	assert difference_tree.rep_type == 'difference'
	assert len(windows) == len(set(windows)) # ensures unique windows

	fragments_found = []
	frames = []
	max_window_size = min(windows, key = lambda x: abs(x - len(ql_array)))
	max_index = windows.index(max_window_size)
	windows = windows[0:max_index + 1]
	for this_win in windows:
		for this_frame in roll_window(array = ql_array, window_length = this_win):
			searched = get_by_ql_array(this_frame, ratio_tree, difference_tree)
			if searched is not None:
				fragments_found.append(searched)

	return fragments_found

####################################################################################################

if __name__ == '__main__':
	import doctest
	doctest.testmod()

