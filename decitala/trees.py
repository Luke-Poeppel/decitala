####################################################################################################
# File:     trees.py
# Purpose:  NAry Tree representation of Fragment Trees and Search algorithms.
# 
# Author:   Luke Poeppel
#
# Location: Kent, 2020 / Frankfurt, 2020
####################################################################################################
import copy
import json
import jsonpickle
import numpy as np
import os
import re
import pytest

from collections import deque

from .fragment import (
	Decitala,
	GreekFoot,
	GeneralFragment
)

from .utils import (
	cauchy_schwartz,
	roll_window,
	get_object_indices,
	successive_ratio_array,
	successive_difference_array,
	find_possible_superdivisions,
	contiguous_summation,
	frame_to_ql_array
)

import logging
logging.basicConfig(level=logging.INFO)

here = os.path.abspath(os.path.dirname(__file__))
decitala_path = os.path.dirname(here) + "/Fragments/Decitalas"
greek_path = os.path.dirname(here) + "/Fragments/Greek_Metrics/XML"

############### EXCEPTIONS ###############
class TreeException(Exception):
	pass

class FragmentTreeException(TreeException):
	pass

class SearchException(Exception):
	pass

####################################################################################################
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
	<trees.NaryTree: nodes=13>
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
	>>> # Level order traversal
	>>> TestTree.level_order_traversal()
	[[1.0], [0.5, 1.0, 3.0, 4.0], [0.5, 3.0, 2.0, 1.0], [1.0, 1.0, 0.5], [2.0]]
	>>> # We can serialize an NaryTree as either a native Python type or Javascript type (for using Treant.js).
	>>> TestTree.serialize()
	'{"root": {"value": 1.0, "name": null, "parent": null, "children": [{"value": 0.5, "name": null, "parent": null, "children": [{"value": 0.5, "name": null, "parent": null, "children": [{"value": 1.0, "name": "D", "parent": null, "children": []}]}, {"value": 3.0, "name": "B", "parent": null, "children": []}]}, {"value": 1.0, "name": null, "parent": null, "children": [{"value": 2.0, "name": "C", "parent": null, "children": [{"value": 1.0, "name": "Test Overwrite", "parent": null, "children": []}]}]}, {"value": 3.0, "name": "A", "parent": null, "children": []}, {"value": 4.0, "name": null, "parent": null, "children": [{"value": 1.0, "name": null, "parent": null, "children": [{"value": 0.5, "name": null, "parent": null, "children": [{"value": 2.0, "name": "Full Path", "parent": null, "children": []}]}]}]}]}}'
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
		return '<trees.NaryTree: nodes={}>'.format(self.size())

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
	def serialize(self, for_treant=False):
		"""tree=pickled tree will not be needed in the actual tree."""
		def encapsulate(d):
			rv = {}
			value, name, parents, children = d.values()
			# Javascript's JSON.parse has a hard time with nulls. 
			if name == None:
				name = ""
			if parents == None:
				parents = ""
			rv['text'] = {'value': value, 'name': name, 'parents': parents}
			rv['children'] = [encapsulate(c) for c in children]
			return rv

		pickled = jsonpickle.encode(self, unpicklable=False)

		if not for_treant:
			loaded = json.loads(pickled)
			return json.dumps(loaded)
		else:
			loaded = json.loads(pickled)
			w_text_field = {"nodeStructure" : encapsulate(loaded["root"])}
			return json.dumps(w_text_field)

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
		"""Returns all possible paths from the root node, not all of which are necesarrily named.
		Currently returns a numpy error."""
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

	def _subpaths(self, name):
		"""Given a name (hopefully attached to a node), returns a list of the subpaths "below" that node."""
		raise NotImplementedError

	def _superpaths_helper(self, node):
		raise NotImplementedError

	def _superpaths(self, name):
		"""Given a name (hopefully attached to a node), returns a list of the subpaths "above" that node."""
		raise NotImplementedError

	################################################################################################
	# Level-Order Traversal
	def level_order_traversal(self):
		"""Returns the level order traversal of an NaryTree."""
		if not self.root:
			return []
		queue = deque([self.root])
		result = []
		while len(queue):
			level_result = []
			for i in range(len(queue)):
				node = queue.popleft()
				level_result.append(node.value) # or just the node...? 
				for child in node.children:
					queue.append(child)
			result.append(level_result)
		
		return result

	################################################################################################
	def search_for_path(self, path_from_root, allow_unnamed=False):
		"""
		Searches for ``path_from_root`` through the tree for a continuous path to a node. 
		
		:param numpy.array path_from_root: path to search in tree.
		:param bool allow_unnamed: whether or not to allow for unnamed paths to be found. 
		:return: either the name of the final node or, if ``allow_unnamed=True``, possibly ``path_from_root``.
		:raises `~decitala.trees.TreeException`: when an invalid path or representation type is provided.
		"""
		assert path_from_root[0] == 0.0 or path_from_root[0] == 1.0, TreeException("{} is an invalid root value.".format(path_from_root[0]))
		assert len(path_from_root) >= 2, TreeException("Path provided must be at least 2 values long.")

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
		This is a special use-case in :obj:`~decitala.trees.get_by_ql_array` based on the observation 
		that the difference representation of mixed augmentations are linearly dependent. In this search
		tool, rather than checking if a path exists in a tree, we check on a level-order basis 
		for a node for which the input is linearly dependent. 

		:raises `NotImplementedError`:
		"""
		raise NotImplementedError

####################################################################################################
def filter_data(raw_data):
	"""
	This function is used in the instantiation of the :class:`~decitala.trees.FragmentTree`.

	:param list raw_data: a list of :class:`~decitala.fragment.Decitala`, :class:`~decitala.fragment.GreekFoot`, or 
						:class:`~decitala.fragment.GeneralFragment` objects. 
	:return: a filtered list that removes single-onset fragments and fragments with equivalent 
			successive difference representations (see :meth:`~decitala.utils.successive_ratio_array`) 
			using the Cauchy-Schwartz inequality.
	:rtype: list
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

class FragmentTree(NaryTree):
	"""
	NaryTree that holds multiplicative or additive representations of a rhythmic dataset. 

	:param str data: path to folder of music21-readable files.
	:param str frag_type: determines the class defining the set of fragments. 
					If the ``frag_type=='decitala'``, creates :class:`~decitala.fragment.Decitala` objects;
					if ``frag_type=='greek_foot'``, creates :class:`~decitala.fragment.GreekFoot`.
					Otherwise creates :class:`~decitala.fragment.GeneralFragment` (default) objects.
	:param str rep_type: determines the representation of the fragment. Options are ``ratio`` (default) and ``difference``.
	:raises `~decitala.trees.FragmentTreeException`: when an invalid path or representation type is provided.

	>>> ratio_tree = FragmentTree(frag_type='greek_foot', rep_type='ratio')
	>>> ratio_tree
	<trees.FragmentTree: nodes=31>
	>>> ratio_tree.search_for_path([1.0, 2.0, 0.5, 1.0])
	<fragment.GreekFoot Peon_II>
	>>> # We can also create a FragmentTree object from either a list of GeneralFragment, Decitala, and GreekFoot objects or from a directory of files using the `data` parameter.
	>>> # We can also give it a name. 
	>>> g1 = GeneralFragment([1.0, 1.0, 1.0, 1.0, 1.0], name="myfragment")
	>>> g2 = Decitala("Ragavardhana")
	>>> g3 = GreekFoot("Ionic_Major")
	>>> data = [g1, g2, g3]
	>>> mytree = FragmentTree(data = data, rep_type="difference", name="MyCoolTree")
	>>> mytree
	<trees.FragmentTree MyCoolTree: nodes=10>
	>>> for path in mytree.all_named_paths():
	...     print(path)
	<fragment.Decitala 93_Ragavardhana>
	<fragment.GeneralFragment myfragment: [1. 1. 1. 1. 1.]>
	<fragment.GreekFoot Ionic_Major>
	"""
	def __init__(self, data=None, frag_type="general_fragment", rep_type="ratio", name=None, **kwargs):
		assert frag_type.lower() in ["decitala", "greek_foot", "general_fragment"], FragmentTreeException("The only possible frag_types are `decitala`, `greek_foot`, and `general_fragment`.")
		assert rep_type.lower() in ["ratio", "difference"], FragmentTreeException("The only possible rep_types are `ratio` and `difference`")

		self.data = data
		self.frag_type = frag_type.lower()
		self.rep_type = rep_type.lower()
		self.name = name

		raw_data = []
		if (frag_type == "decitala" or frag_type == "greek_foot"):
			if data is None:
				if self.frag_type == "decitala":
					for this_file in os.listdir(decitala_path):
						x = re.search(r'\d+', this_file)
						try:
							span_end = x.span()[1] + 1
							raw_data.append(Decitala(name=this_file[span_end:]))
						except AttributeError: # Is this ok...?
							pass
					self.raw_data = raw_data

				if self.frag_type == "greek_foot":
					for this_file in os.listdir(greek_path):
						raw_data.append(GreekFoot(this_file[:-4]))
					self.raw_data = raw_data

			else:
				raise FragmentTreeException("To use the {} frag_type, you may not provide data.".format(frag_type))
		else:
			if isinstance(data, str):
				assert os.path.isdir(data), FragmentTreeException("Invalid path provided.")
				for this_file in os.listdir(self.data):
					raw_data.append(GeneralFragment(this_file))
				self.raw_data = raw_data

			if isinstance(data, list):
				assert all(type(x).__name__ in ["GeneralFragment", "Decitala", "GreekFoot"] for x in data), FragmentTreeException("The elements of data must be GeneralFragment, Decitala, or GreekFoot objects.")
				self.raw_data = data
		
		super().__init__()

		self.filtered_data = filter_data(self.raw_data)
		self.raw_data = None # Free up memory

		self.depth = max([len(x.ql_array()) for x in self.filtered_data])
		self.sorted_data = sorted(self.filtered_data, key = lambda x: len(x.ql_array()))
		self.filtered_data = None # Free up memory

		if self.rep_type == "ratio":
			root_node = NaryTree().Node(value = 1.0, name = 'ROOT')
			for this_fragment in self.sorted_data:
				root_node.add_path_of_children(path = list(this_fragment.successive_ratio_array()), final_node_name = this_fragment)
			self.root = root_node
		
		if self.rep_type == "difference":
			root_node = NaryTree().Node(value = 0.0, name = 'ROOT')
			for this_fragment in self.sorted_data:
				root_node.add_path_of_children(path = list(this_fragment.successive_difference_array()), final_node_name = this_fragment)
			self.root = root_node
		
		# self.sorted_data = None # Free up memory
	
	def __repr__(self):
		if self.name:
			return '<trees.FragmentTree {0}: nodes={1}>'.format(self.name, self.size())
		else:
			return '<trees.FragmentTree: nodes={}>'.format(self.size())
	
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

		:param str filepath: path to file 
		:param int part: part number
		"""
		assert os.path.isfile(filepath)
		assert type(part) == int
		
		object_list = get_object_indices(filepath = filepath, part_num = part)
		data = []
		for this_window in windows:
			frames = roll_window(array = object_list, window_length = this_window)
			for this_frame in frames:
				objects = [x[0] for x in this_frame]
				indices = [x[1] for x in this_frame]
				if any(x.isRest for x in objects): # Skip any window that has a rest in it.
					continue
				else:
					as_quarter_lengths = []
					for this_obj, this_range in this_frame:
						as_quarter_lengths.append(this_obj.quarterLength)
					name = str(indices[0][0]) + "-" + str(indices[-1][-1])
					data.append(GeneralFragment(as_quarter_lengths, name=name))

		return FragmentTree(data=data, rep_type=rep_type)

####################################################################################################
# Search
class _SearchConfig():
	"""Helper class for managing relationship between search ql_arrays and search trees."""
	def __init__(self, ql_array, ratio_tree=None, difference_tree=None, modifications=[]):
		self.ql_array = ql_array
		
		if ratio_tree is None and difference_tree is None:
			raise SearchException("You need to provide at least one tree.")
		
		self.ratio_tree = ratio_tree
		self.difference_tree = difference_tree

		# Check agreement between provided FragmentTree(s) and provided modifications.
		assert set(modifications).issubset({"r", "rr", "d", "rd", "sr", "rsr"}), SearchException("Current supported searches are r, rr, d, rd, sr, rsr.")
		assert len(set(modifications)) == len(modifications), SearchException("You have a duplicate element in your allowed modifications.")
		self.modifications = modifications

		if (len(set(self.modifications).intersection({"r", "rr", "sr", "rsr"})) != 0) and self.ratio_tree is None:
			raise SearchException("You did not provide a ratio FragmentTree.")
		if (len(set(self.modifications).intersection({"d", "rd"})) != 0) and self.difference_tree is None:
			raise SearchException("You did not provide a difference FragmentTree.") 

	def __repr__(self):
		return "<_SearchConfig: {}>".format(self.modifications)

	def __getitem__(self, modification):
		if modification not in self.modifications:
			raise Exceptions("'{0}' is not in '{1}'".format(modification, self.modifications))
	
		retrograde = self.ql_array[::-1]
		
		ratio_array = successive_ratio_array(self.ql_array)
		difference_array = successive_difference_array(self.ql_array)
		retrograde_ratio_array = successive_ratio_array(retrograde)
		retrograde_difference_array = successive_difference_array(retrograde)
		
		all_superdivisions = find_possible_superdivisions(self.ql_array)
		superdivisions_ratio = [successive_ratio_array(x) for x in all_superdivisions]
		retrograde_superdivisions_pre = [x[::-1] for x in all_superdivisions]
		retrograde_superdivisions_ratio = [successive_ratio_array(x) for x in retrograde_superdivisions_pre]

		if modification == "r":
			return (self.ratio_tree, ratio_array)
		elif modification == "rr":
			return (self.ratio_tree, retrograde_ratio_array)
		elif modification == "d":
			return (self.difference_tree, difference_array)
		elif modification == "rd":
			return (self.difference_tree, retrograde_difference_array)
		elif modification == "sr":
			return (self.ratio_tree, superdivisions_ratio[1:]) # exclude original 
		elif modification == "rsr":
			return (self.ratio_tree, retrograde_superdivisions_ratio[1:]) # exclude original

	def _get_modification_data(self, found_fragment, modification):
		"""Helper function for retrieving the modifier between the input & founds fragments."""
		if modification == "r":
			ratio = abs(self.ql_array[0] / found_fragment.ql_array()[0])
			return (modification, ratio)
		elif modification == "rr":
			flipped = self.ql_array[::-1]
			ratio = abs(flipped[0] / found_fragment.ql_array()[0])
			return (modification, ratio)
		elif modification == "d":
			difference = abs(self.ql_array[0] - found_fragment.ql_array()[0])
			return (modification, difference)
		elif modification == "rd":
			flipped = self.ql_array[::-1]
			difference = abs(flipped[0] - found_fragment.ql_array()[0])
			return (modification, difference)
		elif modification == "sr":
			# How can I get the superdivision information easily...?
			ratio = abs(self.ql_array[0] / found_fragment.ql_array()[0])
			return (modification, ratio)
		elif modification == "rsr":
			# See the above. 
			flipped = self.ql_array[::-1]
			ratio = abs(flipped[0] / found_fragment.ql_array()[0])
			return (modification, ratio)

def get_by_ql_array(
		ql_array,
		ratio_tree=None,
		difference_tree=None,
		allowed_modifications=[
			"r", 
			"rr", 
			"d", 
			"rd", 
			"sr",
			"rsr"
		],
		allow_unnamed=False
	):
	"""
	Searches a given ratio and/or difference tree for a given fragment. Supports fragments with grace notes. 

	:param numpy.array ql_array: fragment to be searched.
	:param fragment.FragmentTree ratio_tree: tree storing ratio representations.
	:param fragment.FragmentTree difference_tree: tree storing difference representations.
	:param list allowed_modifications: possible ways for a fragment to be modified. 
									Current possibilities are ``r``, ``rr``, ``d``, ``rd``, ``sr``, and ``rsr``.
									*NOTE*: the order of ``allowed_modifications`` is the order of the search. 
	:param bool allow_unnamed: whether or not to allow the retrieval of unnamed paths. Default is ``False``.

	>>> fragment = np.array([3.0, 1.5, 1.5, 3.0])
	>>> ratio_tree = FragmentTree(frag_type='greek_foot', rep_type='ratio')
	>>> difference_tree = FragmentTree(frag_type='greek_foot', rep_type='difference')
	>>> allowed_modifications = ["r", "rr"]
	>>> get_by_ql_array(fragment, ratio_tree, difference_tree, allowed_modifications)
	(<fragment.GreekFoot Choriamb>, ('r', 1.5))
	"""
	assert type(allowed_modifications) == list
	
	# Remove any grace notes.
	ql_array = [val for val in ql_array if val != 0]

	fragment = None
	config = _SearchConfig(ql_array=ql_array, ratio_tree=ratio_tree, difference_tree=difference_tree, modifications=allowed_modifications)
	i = 0
	while i < len(allowed_modifications):
		curr_modification = allowed_modifications[i]
		search_tree, search_ql_array = config[curr_modification]

		if curr_modification in {"sr", "rsr"}:
			for this_array in search_ql_array:
				if len(this_array) < 2:
					pass
				else:
					search = search_tree.search_for_path(this_array, allow_unnamed)

				if search is not None:
					break
		else:
			search = search_tree.search_for_path(search_ql_array, allow_unnamed)

		if search is not None:
			fragment = search
			change = config._get_modification_data(fragment, curr_modification)
			break
		else:
			i += 1

	if fragment:
		return (fragment, change)
	else:
		return None

####################################################################################################
def rolling_search(
		filepath, 
		part_num, 
		ratio_tree=None, 
		difference_tree=None,
		allowed_modifications=[
			"r", 
			"rr", 
			"d", 
			"rd", 
			"sr",
			"rsr"
		],
		try_contiguous_summation=True,
		windows=list(range(2, 20)),
		allow_unnamed=False,
		verbose=True
	):
	"""
	Rolling search on a music21-readable file on a given part. For search types, see 
	documentation for :func:`~decitala.trees.get_by_ql_array`. The default window lengths 
	are the lengths of fragments in the decitala dataset.

	:param str filepath: path to file to be searched.
	:param int part_num: part in the file to be searched (0-indexed).
	:param fragment.FragmentTree ratio_tree: tree storing ratio representations.
	:param fragment.FragmentTree difference_tree: tree storing difference representations.
	:param allowed_modifications list: see :func:`decitala.trees.get_by_ql_array`.
	:param try_contiguous_summation bool: ties together all elements of equal pitch and duration and searches. 
	:param list windows: possible length of the search frame. 
	:param bool allow_unnamed: whether or not to allow unnamed fragments found to be returned.
	:param verbose bool: whether or not to log results in real time. 

	:return: list holding fragments in the array, along with the modification and the offset region in which it occurs. 
	:rtype: list

	>>> ratio_tree = FragmentTree(frag_type='greek_foot', rep_type='ratio')
	>>> difference_tree = FragmentTree(frag_type='greek_foot', rep_type='difference')
	>>> ex = '/Users/lukepoeppel/moiseaux/Europe/I_La_Haute_Montagne/La_Niverolle/XML/niverolle_3e_example.xml'
	>>> for tala_data in rolling_search(ex, 0, ratio_tree, difference_tree)[0:5]:
	... 	print(tala_data)
	((<fragment.GreekFoot Spondee>, ('r', 0.125)), (0.0, 0.5))
	((<fragment.GreekFoot Trochee>, ('r', 0.125)), (0.25, 0.625))
	((<fragment.GreekFoot Spondee>, ('r', 0.0625)), (0.5, 0.75))
	((<fragment.GreekFoot Iamb>, ('r', 0.125)), (0.625, 1.0))
	((<fragment.GreekFoot Spondee>, ('r', 0.125)), (0.75, 1.25))
	"""
	try:
		assert ratio_tree.rep_type == "ratio"
		assert difference_tree.rep_type == "difference"
	except AttributeError:
		pass

	depths = []
	if ratio_tree is not None:
		depths.append(ratio_tree.depth)
	if difference_tree is not None:
		depths.append(difference_tree.depth)

	object_list = get_object_indices(filepath = filepath, part_num = part_num)
	
	max_window_size = min(max(depths), len(object_list))
	closest_window = min(windows, key=lambda x: abs(x - max_window_size))
	index_of_closest = windows.index(closest_window)
	windows = windows[0:index_of_closest+1]

	fragments_found = []
	for this_win in windows:
		if verbose:
			logging.info("\n")
			logging.info("Searching window of size {}.".format(this_win))
		frames = roll_window(array = object_list, window_length = this_win)
		for this_frame in frames:
			objects = [x[0] for x in this_frame]
			if any(x.isRest for x in objects): # Skip any window that has a rest in it.
				continue
			else:
				ql_array = frame_to_ql_array(this_frame)
				if len(ql_array) < 2:
					continue
			
				searched = get_by_ql_array(ql_array, ratio_tree, difference_tree, allowed_modifications, allow_unnamed)
				if searched is not None:
					offset_1 = this_frame[0][0]
					offset_2 = this_frame[-1][0]

					fragments_found.append((searched, (offset_1.offset, offset_2.offset + offset_2.quarterLength)))
					if verbose:
						logging.info("{0}, {1}".format(searched, (offset_1.offset, offset_2.offset + offset_2.quarterLength)))

				if try_contiguous_summation:
					new_frame = contiguous_summation(this_frame)
					contiguous_summation_ql_array = frame_to_ql_array(new_frame)

					if len(contiguous_summation_ql_array) < 2 or np.array_equal(ql_array, contiguous_summation_ql_array):
						continue

					searched = get_by_ql_array(contiguous_summation_ql_array, ratio_tree, difference_tree, allowed_modifications, allow_unnamed)
					if searched is not None:
						rewritten_search = [searched[0]] + [list(x) for x in searched[1:]] # fragment + modification data
						rewritten_search[1][0] = rewritten_search[1][0] + "-cs"
						frag = rewritten_search[0]
						mod = rewritten_search[1]
						rewritten_search = (frag, tuple(mod))

						offset_1 = this_frame[0][0]
						offset_2 = this_frame[-1][0]

						result = (rewritten_search, (offset_1.offset, offset_2.offset + offset_2.quarterLength))		
						fragments_found.append(result)
						if verbose:
							logging.info("{0}, {1}".format(result[0], result[1]))
	
	return fragments_found

def rolling_search_on_array(
		ql_array, 
		ratio_tree=None, 
		difference_tree=None,
		allowed_modifications=[
			"r", 
			"rr", 
			"d", 
			"rd", 
			"sr",
			"rsr"
		],
		windows=[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19],
		allow_unnamed=False,
	):
	"""
	Rolling search on an array (useful for quick checks in a score). For search types, 
	see documentation for :func:`~decitala.trees.get_by_ql_array`. 

	:param numpy.array ql_array: fragment to be searched.
	:param fragment.FragmentTree ratio_tree: tree storing ratio representations.
	:param fragment.FragmentTree difference_tree: tree storing difference representations.
	:param list windows: possible length of the search frame. 
	:return: list holding fragments in the array present in the trees.
	:rtype: list

	>>> greek_ratio_tree = FragmentTree(frag_type='greek_foot', rep_type='ratio')
	>>> greek_difference_tree = FragmentTree(frag_type='greek_foot', rep_type='difference')
	>>> example_fragment = np.array([0.25, 0.5, 0.25, 0.5])
	>>> for x in rolling_search_on_array(ql_array=example_fragment, ratio_tree=greek_ratio_tree, difference_tree=greek_difference_tree):
	...     print(x)
	(<fragment.GreekFoot Iamb>, ('r', 0.25))
	(<fragment.GreekFoot Trochee>, ('r', 0.25))
	(<fragment.GreekFoot Iamb>, ('r', 0.25))
	(<fragment.GreekFoot Amphibrach>, ('r', 0.25))
	(<fragment.GreekFoot Amphimacer>, ('r', 0.25))
	"""
	assert ratio_tree.rep_type == "ratio"
	assert difference_tree.rep_type == "difference"

	fragments_found = []
	max_window_size = min(windows, key = lambda x: abs(x - len(ql_array)))
	max_index = windows.index(max_window_size)
	windows = windows[0:max_index + 1]
	for this_window in windows:
		for this_frame in roll_window(array = ql_array, window_length = this_window):
			searched = get_by_ql_array(this_frame, ratio_tree, difference_tree, allowed_modifications, allow_unnamed)
			if searched is not None:
				fragments_found.append(searched)

	return fragments_found

if __name__ == '__main__':
	import doctest
	doctest.testmod()