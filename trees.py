# -*- coding: utf-8 -*-
####################################################################################################
# File:     trees.py
# Purpose:  NAry Tree representation of Fragment Trees and Search algorithms.
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
This module holds the Nary tree representation of Fragment trees (both ratio and difference based).

NOTE:
TODO:
- The dot product and norm are built-in functions in numpy. Saves space and is cleaner. 
"""
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

from decitala import (
	Decitala,
	_ratio,
	_difference,
	successive_ratio_list,
	successive_difference_array
)

from tools import get_indices_of_object_occurrence

decitala_path = '/Users/lukepoeppel/decitala_v2/Decitalas'
greek_path = '/Users/lukepoeppel/decitala_v2/Greek_Metrics/XML'

############### EXCEPTIONS ###############
class TreeException(Exception):
	pass

class FragmentTreeException(Exception):
	pass

################################# WINDOWS ###################################
def roll_window(lst, window_length):
	'''
	Takes in a list and returns a list of lists that holds rolling windows of length window_length.

	>>> l = ['Mozart', 'Monteverdi', 'Messiaen', 'Mahler', 'MacDowell', 'Massenet']
	>>> for this in roll_window(lst=l, window_length=3):
	...     print(this)
	['Mozart', 'Monteverdi', 'Messiaen']
	['Monteverdi', 'Messiaen', 'Mahler']
	['Messiaen', 'Mahler', 'MacDowell']
	['Mahler', 'MacDowell', 'Massenet']
	'''
	assert type(window_length) == int

	l = []
	iterable = iter(lst)
	win = []
	for _ in range(0, window_length):
		win.append(next(iterable))
	
	l.append(win)

	for thisElem in iterable:
		win = win[1:] + [thisElem]
		l.append(win)

	return l

################################## MATH HELPERS ##################################

def dot_product(vector1, vector2):
	'''
	Returns the dot product (i.e. component by component product) of two vectors. 

	>>> v1 = [1.0, 2.0, 0.75]
	>>> v2 = [0.5, 0.5, 0.75]
	>>> dot_product(v1, v2)
	2.0625
	'''
	if len(vector1) != len(vector2):
		raise Exception('Vector dimensions do not match.')
	else:
		dot_product = 0
		for i in range(0, len(vector1)):
			dot_product += vector1[i] * vector2[i]

	return round(dot_product, 5)

def cauchy_schwartz(vector1, vector2):
	'''
	Tests the cauchy-schwartz inequality between two vectors. Namely, if the absolute value of 
	the dot product of the two vectors is less than the product of the norms, the vectors are 
	linearly independant (and the function returns True); if they are equal, they are dependant 
	(and the function returns False). 

	Linear Independence:
	>>> vectorI1 = [0.375, 1.0, 0.25]
	>>> vectorI2 = [1.0, 0.0, 0.5]
	>>> cauchy_schwartz(vectorI1, vectorI2)
	True

	Test:
	>>> cauchy_schwartz([0.75, 0.5], [1.5, 1.0])
	False

	Linear Dependance (D1 = 2D2):
	>>> vectorD1 = [1.0, 2.0, 4.0, 8.0]
	>>> vectorD2 = [0.5, 1.0, 2.0, 4.0]
	>>> cauchy_schwartz(vectorD1, vectorD2)
	False

	Direct Equality:
	>>> vectorE1 = [0.25, 0.25, 0.25, 0.25]
	>>> vectorE2 = [0.25, 0.25, 0.25, 0.25]
	>>> cauchy_schwartz(vectorE1, vectorE2)
	False
	'''
	def _euclidianNorm(vector):
		'''
		Returns the euclidian norm of a duration vector (rounded to 5 decimal places). Defined as the 
		square root of the inner product of a vector with itself.

		>>> euclidianNorm([1.0, 1.0, 1.0])
		Decimal('1.73205')
		>>> euclidianNorm([1, 2, 3, 4])
		Decimal('5.47722')
		'''
		norm_squared = dot_product(vector, vector)
		norm = decimal.Decimal(str(math.sqrt(norm_squared)))

		return norm.quantize(decimal.Decimal('0.00001'), decimal.ROUND_DOWN)

	if abs(dot_product(vector1, vector2)) <  (_euclidianNorm(vector1) * _euclidianNorm(vector2)):
		return True
	else:
		return False

################################### TREES ###################################

class NaryTree(object):
	"""
	A single-rooted nary tree for ratio and difference representations of rhythmic fragments. Nodes are 
	hashed by their value and are stored in a set. For demonstration, we will create the following tree: 
	(If a string appears next to a node value, this means the path from the root to that node is an encoded fragment.) 

										1.0				    |	(full path)				LEVEL 1
							0.5			1.0		    3.0A.   |		4.0					LEVEL 2
						0.5		3.0B		 2.0C		    |		1.0					LEVEL 3
						1.0D				 1.0 'Overwrite'|	0.5						LEVEL 4
															|		2.0 'Full Path'		LEVEL 5

	>>> root = NaryTree().Node(value = 1.0, name = None)			# LEVEL 1

	>>> c1 = NaryTree().Node(value = 0.5, name = None)					# LEVEL 2				
	>>> c2 = NaryTree().Node(value = 1.0, name = None)
	>>> c3 = NaryTree().Node(value = 3.0, name = 'A')
	>>> c3.value 
	3.0

	>>> gc1 = NaryTree().Node(value = 0.5, name = None)					# LEVEL 3
	>>> gc2 = NaryTree().Node(value = 3.0, name = 'B')
	>>> gc3 = NaryTree().Node(value = 2.0, name = 'C')

	>>> ggc = NaryTree().Node(value = 1.0, name = 'D')					# LEVEL 4

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

	We can also write the contents of a node to json format using c1.write_to_json() for use 
	in the treant.js visualization of fragment trees. Because of annoying whitespace errors, I'm 
	removed the docstring here.
	c1.write_to_json()
	{
        "info": {
            "name": null,
            "value": 0.5,
            "children": [
                {
                    "info": {
                        "name": null,
                        "value": 0.5
                    }
                },
                {
                    "info": {
                        "name": "B",
                        "value": 3.0
                    }
                }
            ]
        }
	}

	(January 16 Addition)
	I implemented an add_path_of_children() method. This allows for the creation of a path from
	a node through its children. 

	>>> root.add_path_of_children(path = [root.value, 4.0, 1.0, 0.5, 2.0], final_node_name = 'Full Path')
	>>> root.children
	{<NODE: value=0.5, name=None>, <NODE: value=1.0, name=None>, <NODE: value=3.0, name=A>, <NODE: value=4.0, name=None>}

	Check for overwriting data...
	>>> root.add_path_of_children(path = [root.value, 1.0, 2.0, 1.0], final_node_name = 'Test Overwrite')

	We can access children by referencing a node or by calling to its representative value. 

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

	Calling the size returns the number of nodes in the tree. 
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

	To iterate through named paths in the tree, we use the following. Note that in our application, the name
	is itself a Decitala object from which we can retrieve the path data. 
	>>> for this_named_path in TestTree:
	...     print(this_named_path)
	...
	D
	B
	C
	Test Overwrite
	A
	Full Path

	Get paths of a particular length:
	>>> for this_path in TestTree.all_named_paths_of_length_n(length = 3):
	...     print(this_path)
	B
	C

	We can search for paths as follows. 
	>>> TestTree.search_for_path([1.0, 0.5, 0.5, 1.0])
	'D'
	>>> TestTree.search_for_path([1.0, 0.5, 3.0])
	'B'
	>>> TestTree.search_for_path([1.0, 2.0, 4.0])
	>>> TestTree.search_for_path([1.0, 1.0, 2.0])
	'C'
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
			TODO: index the nodes children. 
			"""
			raise NotImplementedError

		def add_child(self, child_node):
			"""
			Adds a single child to the set of children in a node.
			"""
			self.children.add(child_node)
			return

		def add_children(self, children_nodes = []):
			"""
			Adds multiple children to self.children. 
			"""
			if type(children_nodes) != list: 
				raise TreeException('Nodes must be contained in a list.')
			
			for this_child in children_nodes:
				self.add_child(this_child)
			return

		def add_path_of_children(self, path, final_node_name):
			"""
			Adds a path of Nodes through self.children. 
			"""
			if path[0] != self.value:
				raise TreeException('First value in the path must be self.value.')

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
				raise TreeException('This parent does not have that child!')
			self.children.remove(child_node.item.value)
			return

		def remove_children(self, children_nodes):
			for this_child in children_nodes:
				try:
					self.remove_child(this_child)
				except KeyError:
					raise TreeException('One of the values in children_nodes was not found.')
			return

		def get_child(self, node):
			"""
			Given another Node, returns the node in the set of children with the same value. 
			"""
			for this_child in self.children:
				if this_child.value == node.value:
					return this_child
			else:
				return None

		def get_child_by_value(self, value):
			"""
			Same as the above, but allows for search just by value without Node object. 
			"""
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
			"""
			Returns the children of a node in list format, ordered by value. 
			"""
			return sorted([child for child in self.children])

		def write_to_json(self):
			"""
			Used in the Treant.js visualization of Fragment trees. 
			"""
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
		"""
		Helper function for self.size().
		"""
		num_nodes = 1
		for child in node.children:
			num_nodes += self._size_helper(child)

		return num_nodes

	def size(self):
		"""
		Returns the number of nodes in the nary tree. 
		"""
		return self._size_helper(self.root)

	def is_empty(self) -> bool:
		return (self.size() == 0)

	################################################################################################
	def _all_possible_paths_helper(self, node, path = []):
		"""
		Helper function for self.all_possible_paths().
		"""
		path.append(node.value)
		print(path)
		if len(node.children) == 0:
			pass
		else:
			for child in node.children:
				self._all_possible_paths_helper(child, path)
		path.pop()

	def all_possible_paths(self):
		"""
		Returns all possible paths from the root node, not all of which are necesarrily named. 
		"""
		return self._all_possible_paths_helper(self.root)

	def _all_named_paths_helper(self, node, cutoff, path = []):
		"""
		Helper function for self.all_named_paths(). 
		"""
		path.append(node)

		if path[-1].name is not None:
			p = [node.value for node in path]
			if cutoff != 0:
				if len(p) == cutoff:
					yield path[-1].name
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

	def all_named_paths(self, cutoff = 0):
		"""
		Returns all named paths from the root. An optional ``cutoff`` parameter restricts to paths of 
		length n.  
		"""
		for this_named_path in self._all_named_paths_helper(node = self.root, cutoff = cutoff):
			yield this_named_path

	################################################################################################
	def search_for_path(self, path_from_root):
		"""
		Searches through the tree for a continuous path *to a named node* consisting of the values in the path_from_root list. 
		NOTE: the first value of the path must either be 1 (ratio representation search) or 0 (difference 
		representation search). 

		TODO: create a method based on this one that searches for unnamed paths, as well. 
		"""
		if len(path_from_root) <= 2:
			raise TreeException('Path provided must be at least 3 values long.')

		curr = self.root
		i = 1
		
		while i < len(path_from_root):
			try:
				curr = curr.get_child_by_value(value = path_from_root[i])
				if curr is None:
					return None
			except AttributeError:
				break

			if (i == len(path_from_root) - 1) and len(curr.children) == 0:
				return curr.name
			elif (i == len(path_from_root) - 1) and curr.name is not None:
				return curr.name
			else:
				i += 1

	################################################################################################
	# Write tree to JSON
	def _node_list_to_json(self, node_list):
		"""
		Given a list of nodes, returns the information in JSON format. 
		NOTE: you probably need a bottom-up approach.

		>>> n1 = NaryTree().Node(value = 1.0, name = 'Root')
		>>> n2 = NaryTree().Node(value = 2.0, name = None)
		>>> n3 = NaryTree().Node(value = 1.0, name = None)
		>>> n4 = NaryTree().Node(value = 0.5, name = 'test')
		
		_nodes_to_json([n1, n2, n3, n4])
		"""
		i = len(node_list) - 2
		curr = node_list[i]
		curr.add_child(node_list[i + 1])
		children_1 = []
		for this_child in curr.children:
			json_data = {"info" : {"name" : this_child.name, "value" : this_child.value}}
			children_1.append(json_data)

		curr = node_list[i]
		full_2 = {'info' : {'name' : curr.name, 'value' : curr.value, 'children' : children_1}}
		out_this = [full_2]
		i -= 1

		curr = node_list[i]
		full_3 = {'info' : {'name' : curr.name, 'value' : curr.value, 'children' : out_this}}
		out_this_2 = [full_3]

		out = {'info' : {'name' : node_list[0].name, 'value' :node_list[0].value, 'children' : out_this_2}}
		return json.dumps(out, indent=4)

	def _join_json_at_intersection(self, json1, json2):
		"""
		Given two json paths from above, combines them at their intersection. 
		"""
		pass
	
	def write_to_json(self):
		"""
		Writes the entire tree as a JSON object. 

		TODO: get the json for every named path, then join at intersections.
		"""
		if root is None:
			raise TreeException('Cannot write to JSON without a root.')


'''
root = NaryTree().Node(value = 1.0, name = None)

c1 = NaryTree().Node(value = 0.5, name = None)	
c2 = NaryTree().Node(value = 1.0, name = None)
c3 = NaryTree().Node(value = 3.0, name = 'A')
'''
'''
gc1 = NaryTree().Node(value = 0.5, name = None)
gc2 = NaryTree().Node(value = 3.0, name = 'B')
gc3 = NaryTree().Node(value = 2.0, name = 'C')

ggc = NaryTree().Node(value = 1.0, name = 'D')

c1.add_children([gc1, gc2])
c2.add_child(gc3)
gc1.add_child(ggc)

root.parent = None
root.children = {c1, c2, c3}

root = NaryTree().Node(value = 1.0, name = 'Root')
n2 = NaryTree().Node(value = 2.0, name = None)
n3 = NaryTree().Node(value = 1.0, name = None)
n4 = NaryTree().Node(value = 0.5, name = 'test')

tree = NaryTree()
tree.root = root

print(tree._node_list_to_json([root, n2, n3, n4]))
'''

#print(tree.write_to_json())

############################### FRAGMENT TREES ##################################
class FragmentTree(NaryTree):
	"""
	Nary tree for holding ratio and different representation of rhythmic fragments. 

	TODO
	- Keep track of rests in all cases. The indices of occurrence can't be based
	upon placement of notes, but have to be based on placement of *all* musical objects. 
	- Cauchy-schwartz inequality is completely unnecessary (I think) since we're using ratio representations.
	not sure how this applies for difference representations. 
	- Decide on double-onset fragment convention. I'm leaning towards keep them since some of them are odd. 
	"""
	def __init__(self, root_path, frag_type, rep_type, **kwargs):
		if type(root_path) != str:
			raise FragmentTreeException('Path must be a string.')
		
		if rep_type.lower() not in ['ratio', 'difference']:
			raise FragmentTreeException('The only possible types are "ratio" and "difference"')
		
		self.root_path = root_path
		self.frag_type = frag_type
		self.rep_type = rep_type

		super().__init__()

		if frag_type.lower() == 'decitala':
			raw_data = []
			for this_file in os.listdir(root_path):
				x = re.search(r'\d+', this_file)
				try:
					span_end = x.span()[1] + 1
					raw_data.append(Decitala(name=this_file[span_end:]))
				except AttributeError:
					pass

			self.raw_data = raw_data
		elif frag_type.lower() == 'greek_foot':
			raw_data = []
			for this_file in os.listdir(root_path):
				raw_data.append(GreekFoot(this_file))
			self.raw_data = raw_data
		else:
			raw_data = []
			for this_file in os.listdir(root_path):
				raw_data.append(GeneralFragment(this_file))
			self.raw_data = raw_data

		def filter_data(raw_data):
			"""
			Given a list of decitala objects (i.e. converted to a matrix of duration vectors), 
			filter_data() removes:
			- Trivial fragments (single-onset fragments and double onset fragments, the latter 
			by convention). 
			- Duplicate fragments
			- Multiplicative Augmentations/Diminutions (by using the cauchy-schwarz inequality); if 
			two duration vectors are found to be linearly dependant, one is removed.

			Consider the following set of rhythmic fragments.
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
			This function reduces this list to:
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
					#if len(copied[i].ql_array()) < 2:
						#del copied[i]
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
	
			possible_num_onsets = [3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]
			i = 0
			while i < len(possible_num_onsets):
				curr_onset_list = []
				for thisTala in self.filtered_data:
					if len(thisTala.ql_array()) == possible_num_onsets[i]:
						curr_onset_list.append(thisTala)
				for thisTala in curr_onset_list:
					root_node.add_path_of_children(path = list(thisTala.successive_ratio_list()), final_node_name = thisTala)
				i += 1

			self.root = root_node
		
		if rep_type == 'difference':
			root_node = NaryTree().Node(value = 0.0, name = 'ROOT')

			possible_num_onsets = [3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]
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

def get_by_ql_array(ql_array, ratio_tree, difference_tree):
	"""
	I don't think it makes sense to have stuff like rolling_search as part of the tree class...
	It definitely makes sense to have *some* get_by_ql thing in the tree, but what? We need to be 
	able to search the difference tree, so maybe I should have get_by_ql_array() be a method that searches
	for exact instances of the ql array. Then rolling_search and get_by_ql_array_all_methods() 
	are separate methods.
	"""
	retrograde = ql_array[::-1]
	ratio_list = successive_ratio_list(ql_array)
	difference_list = successive_difference_array(ql_array)
	retrograde_ratio_list = successive_ratio_list(retrograde)
	retrograde_difference_list = successive_difference_array(retrograde)

	ratio_search = ratio_tree.search_for_path(ratio_list)
	if ratio_search is None:
		retrograde_ratio_search = ratio_tree.search_for_path(retrograde_ratio_list)
		if retrograde_ratio_search is None:
			difference_search = difference_tree.search_for_path(difference_list)
			if difference_search is None:
				retrograde_difference_search = difference_tree.search_for_path(retrograde_difference_list)
				if retrograde_difference_search is None:
					return None
				else:
					difference = _difference(retrograde_difference_search.ql_array(), 0)
					return (retrograde_difference_search, ('retrograde difference', difference))
			else:
				difference = _difference(difference_search.ql_array(), 0)
				return (difference_search, ('difference', difference))
		else:
			ratio = _ratio(retrograde_ratio_search.ql_array(), 0)
			return (retrograde_ratio_search, ('retrograde ratio', ratio))
	else:
		ratio = _ratio(ratio_search.ql_array(), 0)
		return (ratio_search, ('ratio', ratio))

def rolling_search(path, part_num, ratio_tree, difference_tree):
	"""
	TODO: I could consider doing a set check for each search for recyclability reasons... Not
	very pressing, but is more efficient. 

	Runs a windowed search on an input stream and path number. Returns the decitalas found and the 
	indices of occurrence. 
	"""
	possible_windows = [3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]
	object_list = ratio_tree.get_indices_of_object_occurrence(file_path = path, part_num = part_num)
	fragments_found = []
	frames = []

	for this_win in possible_windows:
		for this_frame in roll_window(lst = object_list, window_length = this_win):
			frames.append(this_frame)

	for this_frame in frames:
		as_quarter_lengths = []
		for this_obj, thisRange in this_frame:
			if this_obj.isRest:
				if this_obj.quarterLength == 0.25:
					as_quarter_lengths.append(this_obj)
				else:
					pass
			as_quarter_lengths.append(this_obj.quarterLength)

		searched = get_by_ql_list2(as_quarter_lengths, ratio_tree, difference_tree)
		if searched is not None:
			offset_1 = this_frame[0][0]
			offset_2 = this_frame[-1][0]

			fragments_found.append((searched, (offset_1.offset, offset_2.offset + offset_2.quarterLength)))

	return fragments_found

'''
ratio_tree = FragmentTree(root_path=decitala_path, frag_type='decitala', rep_type = 'ratio')
difference_tree = FragmentTree(root_path=decitala_path, frag_type='decitala', rep_type = 'difference')

livre_dorgue_1 = np.array([1.0, 0.5, 1.5, 1.5, 1.5, 1.0, 1.5, 0.25, 0.25, 0.25])
livre_dorgue_2 = np.array([0.125, 0.125, 0.125, 0.125, 0.25, 0.25, 0.375])
livre_dorgue_3 = np.array([0.75, 1.25, 1.25, 1.75, 1.25, 1.25, 1.25, 0.75])
print(get_by_ql_array(livre_dorgue_1, ratio_tree, difference_tree))
print(get_by_ql_array(livre_dorgue_2, ratio_tree, difference_tree))
print(get_by_ql_array(livre_dorgue_3, ratio_tree, difference_tree))
'''

'''
sept_haikai_path = '/Users/lukepoeppel/Desktop/Messiaen/Sept_Haikai/1_Introduction.xml'
livre_dorgue_path = "/Users/lukepoeppel/Desktop/Messiaen/Livre_d\'Orgue/V_Piece_En_Trio.xml"
found = []
for this_tala in rolling_search2(sept_haikai_path, 1, ratio_tree, difference_tree):
	found.append(this_tala)
sorted_talas = sorted(found, key = lambda x: x[1][0])
for x in sorted_talas:
	print(x)
'''
'''
t = FragmentTree(root_path = decitala_path, frag_type = 'decitala', rep_type = 'ratio')

found = []
for this_tala in t.rolling_search(sept_haikai_path, 0):
	found.append(this_tala)
for x in set(found):
	print(x)
'''

if __name__ == '__main__':
	import doctest
	#doctest.testmod()

