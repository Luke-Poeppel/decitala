# -*- coding: utf-8 -*-
####################################################################################################
# File:     decitala_v2.py
# Purpose:  Version 2.0 of decitala.py. Dynamic functions for tala search (e.g. deçi-tâlas), primarily
#			in the music and birdsong transcriptions of Olivier Messiaen. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
'''
CODE SPRING TODO: 
- fix and shorten helper functions below.
- decide convention for kakpadam from Rowley.
- standardize fully to np.array(). Also matplotlib will be easier. 
'''
from __future__ import division, print_function, unicode_literals

import copy
import datetime
import fractions
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
import re
import statistics
import tqdm

from music21 import converter
from music21 import note
from music21 import pitch
from music21 import stream

decitala_path = '/Users/lukepoeppel/Decitalas'
greek_path = '/Users/lukepoeppel/Greek_Metrics/XML'

#Doesn't make much sense for these to be np.arrays because of the mixed types... 
carnatic_symbols = np.array([
	['Druta', 'o', 0.25],
	['Druta-Virama', 'oc', 0.375],
	['Laghu', '|', 0.5],
	['Laghu-Virama', '|c', 0.75],
	['Guru', 'S', 1.0],
	['Pluta', 'Sc', 1.5],           #Note: Normally a crescent moon superscript. Since it serves the same function as a virâma––we use the same notation. 
	#['kakapadam', '8X', 2.0]       #Decide what the appropriate convention is...
])

greek_diacritics = np.array([
	['breve', '⏑', 1.0],
	['macron', '––', 2.0]
])

multiplicative_augmentations = np.array([
	['Tiers', 4/3],
	['Un quart', 1.25],
	['Du Point', 1.5],
	['Classique', 2], 
	['Double', 3],
	['Triple', 4],
])

#rounded to 6 decimal places; add more as needed
fraction_dict = {
	0.166667 : fractions.Fraction(1, 6),
	0.333333 : fractions.Fraction(1, 3),
	0.666667 : fractions.Fraction(2, 3), 
	1.333333 : fractions.Fraction(4, 3),
	1.666667 : fractions.Fraction(5, 3)
}

#id_number(s) of decitalas with "subtalas"
subdecitala_array = np.array([26, 38, 55, 65, 68])

############ HELPER FUNCTIONS ############
#Notational Conversion Functions
def carnatic_string_to_ql_array(string):
	'''
	Converts a string of carnatic rhythmic values to a quarter length numpy array. Note that the carnatic characters 
	must have a spaces between them or the string will be converted incorrectly. 

	>>> carnatic_string_to_ql_array(string = 'oc o | | Sc S o o o')
	array([0.375, 0.25 , 0.5  , 0.5  , 1.5  , 1.   , 0.25 , 0.25 , 0.25 ])
	'''
	split_string = string.split()
	return np.array([float(this_carnatic_val[2]) for this_token in split_string for this_carnatic_val in carnatic_symbols if (this_carnatic_val[1] == this_token)])

def ql_array_to_carnatic_string(ql_array):
	'''
	Converts a list of quarter length values to a string of carnatic rhythmic values.
	
	>>> ql_array_to_carnatic_string([0.5, 0.25, 0.25, 0.375, 1.0, 1.5, 1.0, 0.5, 1.0])
	'| o o oc S Sc S | S'
	'''
	return ' '.join(np.array([this_carnatic_val[1] for this_val in ql_array for this_carnatic_val in carnatic_symbols if (float(this_carnatic_val[2]) == this_val)]))

def _ratio(array, start_index):
	'''
	Given an array and a starting index, returns the ratio of the element at the provided index 
	to the element at the following one. A ZeroDivision error will only occur if it encounters a 
	difference list.

	>>> _ratio(np.array([1.0, 0.5]), 0)
	0.5
	>>> _ratio(np.array([0.25, 0.25, 0.75]), 1)
	3.0
	>>> _ratio(np.array([1.5, 1.0]), 0)
	0.66667
	'''
	if not (0 <= start_index and start_index <= len(array) - 1):
		raise IndexError('Input ``start_index`` not in appropriate range!')
	try: 
		ratio = array[start_index + 1] / array[start_index]
		return round(ratio, 5)
	except ZeroDivisionError:
		raise Exception('Something is off...')

def _difference(array, start_index):
	'''
	Returns the difference between two elements. 
	'''
	try:
		difference = array[start_index + 1] - array[start_index]
		return difference
	except IndexError:
		pass

############ HELPER FUNCTIONS ############
class Decitala(object):
	'''    
	Class that stores Decitala data. Reads from a folder containing all Decitala XML files.

	>>> ragavardhana = Decitala('Ragavardhana')
	>>> ragavardhana
	<decitala.Decitala 93_Ragavardhana>
	>>> ragavardhana.filename
	'93_Ragavardhana.xml'
	>>> ragavardhana.name
	'93_Ragavardhana'
	>>> ragavardhana.id_num
	93
	>>> ragavardhana.num_onsets
	4

	>>> ragavardhana.ql_array()
	array([0.25 , 0.375, 0.25 , 1.5  ])
	>>> ragavardhana.successive_ratio_list()
	array([1.     , 1.5    , 0.66667, 6.     ])
	>>> ragavardhana.carnatic_string
	'o oc o Sc'

	>>> ragavardhana.dseg(as_str = True)
	'<0 1 0 2>'
	>>> ragavardhana.std()
	0.52571

	>>> ragavardhana.morris_symmetry_class()
	'VII. Stream'

	>>> Decitala('Jaya').ql_array()
	array([0.5 , 1.  , 0.5 , 0.5 , 0.25, 0.25, 1.5 ])

	>>> for this_cycle in Decitala('Jaya').get_cyclic_permutations():
	...     print(this_cycle)
	...
	[0.5  1.   0.5  0.5  0.25 0.25 1.5 ]
	[1.   0.5  0.5  0.25 0.25 1.5  0.5 ]
	[0.5  0.5  0.25 0.25 1.5  0.5  1.  ]
	[0.5  0.25 0.25 1.5  0.5  1.   0.5 ]
	[0.25 0.25 1.5  0.5  1.   0.5  0.5 ]
	[0.25 1.5  0.5  1.   0.5  0.5  0.25]
	[1.5  0.5  1.   0.5  0.5  0.25 0.25]
	
	Decitala.getByidNum(idNum) retrieves a Decitala based on an input identification number. These 
	numbers are listed in the Lavignac Encyclopédie and Messiaen Traité.
	
	>>> Decitala.get_by_id(89)
	<decitala.Decitala 89_Lalitapriya>
	''' 
	def __init__(self, name = None):
		if name:
			if name.endswith('.xml'):
				searchName = name
			elif name.endswith('.mxl'):
				searchName = name
			else:
				searchName = name + '.xml'
					
			for thisFile in os.listdir(decitala_path):
				x = re.search(searchName, thisFile)
				if bool(x) == True:
					self.name = os.path.splitext(thisFile)[0]
					self.filename = thisFile
					self.stream = converter.parse(decitala_path + '/' + thisFile)
	  
	def __repr__(self):
		return '<decitala.Decitala {}>'.format(self.name)

	def __hash__(self):
		return hash(self.name)

	@property
	def id_num(self):
		if self.name:
			idValue = re.search(r'\d+', self.name)
			return int(idValue.group(0))

	@classmethod
	def get_by_id(cls, input_id):
		'''
		INPUTS
		*-*-*-*-*-*-*-*-
		input_id : type = ``int`` in range 1-120

		TODO: if I want to be more sophisticated, use subdecitala_array to (in one of those cases)
		return the appropriate tala. 
		TODO: what happens with 'Jaya' versus 'Jayacri,' for example? Simple conditional to add if 
		problematic.
		'''
		assert type(input_id) == int
		if input_id > 120 or input_id < 1:
			raise Exception('Input must be between 1 and 120!')

		for thisFile in os.listdir(decitala_path):
			x = re.search(r'\d+', thisFile)
			try:
				if int(x.group(0)) == input_id:
					return Decitala(thisFile)
			except AttributeError:
				pass
	
	@property
	def num_onsets(self):
		count = 0
		for _ in self.stream.flat.getElementsByClass(note.Note):
			count += 1
		return count
	  
	def ql_array(self, retrograde=False):
		'''
		INPUTS
		*-*-*-*-*-*-*-*-
		retrograde : type = ``bool``
		'''
		if not(retrograde):
			return np.array([this_note.quarterLength for this_note in self.stream.flat.getElementsByClass(note.Note)])
		else:
			return np.flip(np.array([this_note.quarterLength for this_note in self.stream.flat.getElementsByClass(note.Note)]))

	@property
	def carnatic_string(self):
		return ql_array_to_carnatic_string(self.ql_array())

	@property
	def ql_duration(self):
		return sum(self.ql_array())

	@property
	def numMatras(self):
		return (self.ql_duration / 0.5)

	def dseg(self, as_str=False):
		'''
		Marvin's d-seg as introducted in "The perception of rhythm in non-tonal music" (1991). Maps a fragment
		into a sequence of relative durations. This allows cross comparison of rhythmic fragments beyond 
		exact augmentation; we may, for instance, filter rhythms by similar the familiar dseg <1 0 0> which 
		corresponds to long-short-short (e.g. dactyl). 

		INPUTS
		*-*-*-*-*-*-*-*-
		as_str : type = ``bool``

		>>> raya = Decitala('Rayavankola')
		>>> raya.ql_array()
		array([1.  , 0.5 , 1.  , 0.25, 0.25])
		>>> raya.dseg(as_str = False)
		array([2, 1, 2, 0, 0])
		>>> raya.dseg(as_str = True)
		'<2 1 2 0 0>'
		'''
		dseg_vals = copy.copy(self.ql_array())
		valueDict = dict()

		for i, thisVal in zip(range(0, len(sorted(set(dseg_vals)))), sorted(set(dseg_vals))):
			valueDict[thisVal] = str(i)

		for i, thisValue in enumerate(dseg_vals):
			for thisKey in valueDict:
				if thisValue == thisKey:
					dseg_vals[i] = valueDict[thisKey]

		if as_str == True:
			return '<' + ' '.join([str(int(val)) for val in dseg_vals]) + '>'
		else:
			return np.array([int(val) for val in dseg_vals])

	def reduced_dseg(self, as_str=False):
		'''
		Technique used in this paper. Takes a dseg and returns a new dseg where contiguous values are removed. 

		INPUTS
		*-*-*-*-*-*-*-*-
		as_str : type = ``bool``
		'''
		def _remove_adjacent_equal_elements(array):
			as_lst = list(array)
			filtered = [a for a, b in zip(as_lst, as_lst[1:] + [not as_lst[-1]]) if a != b]
			return np.array(filtered)

		orig = self.dseg(as_str = False)
		as_array = _remove_adjacent_equal_elements(array = orig)

		if not(as_str):
			return np.array([int(val) for val in as_array])
		else:
			return '<' + ' '.join([str(int(val)) for val in as_array]) + '>'

	def successive_ratio_list(self):
		'''
		Returns an array of the successive duration ratios. By convention, we set the first value to 1.0. 
		'''
		ratio_array = [1.0] #np.array([1.0])
		i = 0
		while i < len(self.ql_array()) - 1:
			ratio_array.append(_ratio(self.ql_array(), i))
			#np.concatenate(ratio_array, _ratio(self.ql_array(), i))
			i += 1

		return np.array(ratio_array)

	def get_cyclic_permutations(self):
		'''
		Returns all cyclic permutations. 
		'''
		return np.array([np.roll(self.ql_array(), -i) for i in range(self.num_onsets)])

	################ ANALYSIS ################
	def is_non_retrogradable(self):
		return self.ql_array(retrograde = False) == self.ql_array(retrograde = True)

	def morris_symmetry_class(self):
		'''
		Robert Morris (year?) notes 7 kinds of interesting rhythmic symmetries. I provided the names.

		I.) Maximally Trivial:				of the form X (one onset, one anga class)
		II.) Trivial Symmetry: 				of the form XXXXXX (multiple onsets, same anga class)
		III.) Trivial Dual Symmetry:  		of the form XY (two onsets, two anga classes)
		IV.) Maximally Trivial Palindrome: 	of the form XXX...XYX...XXX (multiple onsets, two anga classes)
		V.) Trivial Dual Palindromic:		of the form XXX...XYYYX...XXX (multiple onsets, two anga classes)
		VI.) Palindromic: 					of the form XY...Z...YX (multiple onsets, n/2 anga classes)
		VII.) Stream:						of the form XYZ...abc... (n onsets, n anga classes)
		'''
		dseg = self.dseg(as_str = False)
		reduced_dseg = self.reduced_dseg(as_str = False)

		if len(dseg) == 1:
			return 'I. Maximally Trivial'
		elif len(dseg) > 1 and len(np.unique(dseg)) == 1:
			return 'II. Trivial Symmetry'
		elif len(dseg) == 2 and len(np.unique(dseg)) == 2:
			return 'III. Trivial Dual Symmetry'
		elif len(dseg) > 2 and len(np.unique(dseg)) == 2:
			return 'IV. Maximally Trivial Palindrome'
		elif len(dseg) > 2 and len(reduced_dseg) == 3:
			return 'V. Trivial Dual Palindrome'
		elif len(dseg) > 2 and len(np.unique(dseg)) == len(dseg) // 2:
			return 'VI. Palindrome'
		else:
			return 'VII. Stream'

	def std(self):
		return round(np.std(self.ql_array()), 5)

	def cscore(self):
		'''
		Povel and Essens (1985) C-Score.
		'''
		raise NotImplementedError

	def show(self):
		if self.stream:
			return self.stream.show()

class NaryTree(object):
	'''
	A single-rooted nary tree for ratio and difference representations of rhythmic fragments. Nodes are 
	hashed by their value and are stored in a set. For demonstration, we will create the following tree: 
	(If a string appears next to a node value, this means the path from the root to that node is an encoded fragment.) 

										1.0				    |	(full path)				LEVEL 1
							0.5			1.0		    3.0A.   |		4.0					LEVEL 2
						0.5		3.0B		 2.0C		    |		1.0					LEVEL 3
						1.0D				 1.0 'Overwrite'|	0.5						LEVEL 4
														    |		2.0 'Full Path'		LEVEL 5

	>>> rootNode = NaryTree().Node(value = 1.0, name = None)			# LEVEL 1

	>>> c1 = NaryTree().Node(value = 0.5, name = None)					# LEVEL 2				
	>>> c2 = NaryTree().Node(value = 1.0, name = None)
	>>> c3 = NaryTree().Node(value = 3.0, name = 'A')
	>>> c3.value 
	3.0

	>>> gc1 = NaryTree().Node(value = 0.5, name = None)					# LEVEL 3
	>>> gc2 = NaryTree().Node(value = 3.0, name = 'B')
	>>> gc3 = NaryTree().Node(value = 2.0, name = 'C')

	>>> ggc = NaryTree().Node(value = 1.0, name = 'D')					# LEVEL 4

	>>> rootNode.parent = None
	>>> rootNode.children = {c1, c2, c3}
	>>> rootNode.children
	{<NODE: value=0.5, name=None>, <NODE: value=1.0, name=None>, <NODE: value=3.0, name=A>}
	>>> c1 in rootNode.children
	True
	
	>>> rootNode.orderedChildren()
	[<NODE: value=0.5, name=None>, <NODE: value=1.0, name=None>, <NODE: value=3.0, name=A>]

	>>> c1.addChildren([gc1, gc2])
	>>> c1.numChildren
	2
	>>> c2.addChild(gc3)
	>>> gc1.addChild(ggc)

	(January 16 Addition)
	We have also implemented the addPathOfChildren() method. This allows the creation of a path from
	a node through its children. 

	>>> rootNode.addPathOfChildren(path = [rootNode.value, 4.0, 1.0, 0.5, 2.0], finalNodeName = 'Full Path')
	>>> rootNode.children
	{<NODE: value=0.5, name=None>, <NODE: value=1.0, name=None>, <NODE: value=3.0, name=A>, <NODE: value=4.0, name=None>}

	Check for overwriting data...
	>>> rootNode.addPathOfChildren(path = [rootNode.value, 1.0, 2.0, 1.0], finalNodeName = 'Test Overwrite')

	We can access children by referencing a node or by calling to its representative value. 

	>>> newValue = rootNode.getChildByValue(4.0)
	>>> newValue.children
	{<NODE: value=1.0, name=None>}

	>>> c2.getChild(gc3)
	<NODE: value=2.0, name=C>

	>>> c2.getChildByValue(2.0)
	<NODE: value=2.0, name=C>
	>>> c2.getChildByValue(4.0)

	>>> TestTree = NaryTree()

	>>> TestTree.root = rootNode
	>>> TestTree
	<NaryTree: nodes=13>
	>>> TestTree.isEmpty()
	False

	Calling the size returns the number of nodes in the tree. 
	>>> TestTree.size()
	13

	>>> TestTree.allPossiblePaths()
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

	To iterate through named paths in the tree...
	>>> for thisNamedPath in TestTree:
	...     print(thisNamedPath)
	...
	('D', [1.0, 0.5, 0.5, 1.0])
	('B', [1.0, 0.5, 3.0])
	('C', [1.0, 1.0, 2.0])
	('Test Overwrite', [1.0, 1.0, 2.0, 1.0])
	('A', [1.0, 3.0])
	('Full Path', [1.0, 4.0, 1.0, 0.5, 2.0])

	Get paths of a particular length:
	>>> for thisPath in TestTree.allNamedPathsOfLengthN(n = 3):
	...     print(thisPath)
	('B', [1.0, 0.5, 3.0])
	('C', [1.0, 1.0, 2.0])

	We can search for paths as follows. 

	>>> TestTree.searchForPath([1.0, 0.5, 0.5, 1.0])
	'D'
	>>> TestTree.searchForPath([1.0, 0.5, 3.0])
	'B'
	>>> TestTree.searchForPath([1.0, 2.0, 4.0])
	>>> TestTree.searchForPath([1.0, 1.0, 2.0])
	'C'

	To have an insight into what the tree looks like, run the following.
	TestTree.stupidVisualizer()
	'''
	class Node(object):
		'''
		A Node object stores an item and references its parent and children. In an nary tree, a parent
		may have any arbitrary number of children, but each child has only 1 parent. 
		'''
		def __init__(self, value, name = None):
			self.value = value
			self.name = name
			self.parent = None
			self.children = set()

		def __repr__(self):
			return '<NODE: value={0}, name={1}>'.format(self.value, self.name)

		def __hash__(self):
			return hash(self.value)

		def __eq__(self, other):
			'''
			You need this function! Without this, you can add nodes with the same value to the set 
			of children!
			'''
			return (self.value == other.value) 

		def __lt__(self, other):
			'''
			Implementation of a 'less-than' relation between nodes. The standard relation based on 
			the value of two nodes.  
			'''
			return (self.value < other.value)

		def addChild(self, childNode):
			'''
			Adds a single child to the set of children in a node.
			'''
			self.children.add(childNode)
			return

		def addChildren(self, childrenNodes = []):
			'''
			Adds multiple children to self.children. 
			'''
			if type(childrenNodes) != list: raise Exception('Nodes must be contained in a list!')
			for thisChild in childrenNodes:
				self.addChild(thisChild)
			return

		def addPathOfChildren(self, path, finalNodeName):
			'''
			This is kind of a funny, but a pretty convenient idea! Allows the addition of a path of 
			values from a node down through its children. Include the value of the node from which 
			the path is starting (i.e. self.value). By doing this, we can just run a for loop over 
			the reduced set of fragments to generate the ratio tree and, for each fragment, just run 
			addPathOfChildren(thisFragment, finalName = thisFragment). 
			'''
			if path[0] != self.value:
				raise Exception('First value in the path must be self.value.')

			curr = self
			i = 1
			while i < len(path):
				check = curr.getChildByValue(path[i])
				if check is not None:
					curr = check
					i += 1
				else:
					if i == len(path) - 1:
							child = NaryTree().Node(value = path[i], name = finalNodeName)
					else:
						child = NaryTree().Node(value = path[i])

					curr.addChild(child)
					curr = child
					i += 1

			return

		def removeChild(self, childNode):
			'''
			Removes a single child from self.children. 
			'''
			if childNode.item.value not in self.children:
				raise Exception('This parent does not have that child!')
			self.children.remove(childNode.item.value)
			return

		def removeChildren(self, childrenNodes):
			'''
			Removes multiple children from self.children.
			'''
			for thisChild in childrenNodes:
				self.removeChild(thisChild)
			return

		def getChild(self, node):
			'''
			Given a value, returns the node in the set of children with the associated value. 
			'''
			for thisChild in self.children:
				if thisChild.value == node.value:
					return thisChild
			else:
				return None

		def getChildByValue(self, value):
			'''
			Given a value, returns the node in the set of children with the associated value. 
			'''
			for thisChild in self.children:
				if thisChild.value == value:
					return thisChild
			else:
				return None

		@property
		def numChildren(self) -> int:
			'''
			Returns the number of children that a node holds. 
			'''
			return len(self.children)

		@property
		def hasChildren(self) -> bool:
			'''
			Is the above notation old-fashioned? I don't think I've seen this before for a bool
			return type... 
			'''
			return (self.numChildren != 0)

		def orderedChildren(self):
			'''
			Returns the children of a node in list format, ordered by value. 
			'''
			return sorted([child for child in self.children])

	def __init__(self):
		self.root = None

	def __repr__(self):
		return '<NaryTree: nodes={0}>'.format(self.size())

	def __iter__(self):
		'''
		Iterates through all concluding *paths* in the tree (not nodes), beginning with the 
		shortest paths (of length 2) and ending with paths from the root to the leaves. Ignores 
		paths that do not correspond to a tala. For example, [1.0, 1.0, 1.0, 0.5, 0.75, 0.5] will 
		appear in the iteration of the decitalas (it is Varied_Ragavardhana), but the path 
		[1.0, 1.0, 1.0, 0.5, 0.75] will not. 
		'''
		for thisNamedPath in self.allNamedPaths():
			yield thisNamedPath

	def _sizeHelper(self, node):
		'''
		Helper function for self.size()
		'''
		numNodes = 1
		for child in node.children:
			numNodes += self._sizeHelper(child)

		return numNodes

	def size(self):
		'''
		Returns the number of nodes in the nary tree. 
		'''
		return self._sizeHelper(self.root)

	def isEmpty(self) -> bool:
		return (self.size() == 0)

	################################################################################################
	def _allPossiblePathsHelper(self, node, path = []):
		'''
		Helper function for self.allPossiblePaths()
		'''
		path.append(node.value)
		print(path)
		if len(node.children) == 0:
			pass
		else:
			for child in node.children:
				self._allPossiblePathsHelper(child, path)
		path.pop()

	def allPossiblePaths(self):
		'''
		Prints all possible paths from the root node, all unnamed. 
		'''
		return self._allPossiblePathsHelper(self.root)

	################################################################################################
	def _allNamedPathsHelper(self, node, path = []):
		'''
		Helper function for self.allNamedPaths. 
		'''
		path.append(node)

		if path[-1].name is not None:
			p = [node.value for node in path]
			yield (path[-1].name, p)
		else:
			pass

		if len(node.children) == 0:
			pass
		else:
			for child in node.children:
				yield from self._allNamedPathsHelper(child, path)

		path.pop()

	def allNamedPaths(self):
		'''
		Returns all paths from the root that have names. Each path is returned as a tuple consisting
		of the path followed by its name, i.e., ([PATH], 'NAME'). 
		'''
		for thisNamedPath in self._allNamedPathsHelper(self.root):
			yield thisNamedPath

	def _allNamedPathsOfLengthNHelper(self, node, nIn, path = []):
		'''
		Helper function for allNamedPathsOfLengthN
		'''
		path.append(node)

		if path[-1].name is not None:
			p = [node.value for node in path]
			if len(p) == nIn:
				yield (path[-1].name, p)
		else:
			pass

		if len(node.children) == 0:
			pass
		else:
			for child in node.children:
				yield from self._allNamedPathsOfLengthNHelper(child, nIn, path)

		path.pop()

	def allNamedPathsOfLengthN(self, n):
		'''
		Returns all named paths from the root of provided length. 
		'''
		for thisNamedPathOfLengthN in self._allNamedPathsOfLengthNHelper(node = self.root, nIn = n):
			yield thisNamedPathOfLengthN

	################################################################################################
	def searchForPath(self, pathFromRoot):
		'''
		Searches through the nary tree for a path consisting of the values in the pathFromRoot
		list. Note: the first value of the path must either be 1 (ratio representation search) or 
		0 (difference representation search). Call me old-fashioned, but I feel like there should be 
		a difference in output between a path being present but unnamed and path not existing. 
		'''
		#if pathFromRoot[0] != 1.0 or 0.0:
			#raise Exception('Path provided is invalid.')
		if len(pathFromRoot) <= 2:
			raise Exception('Path provided must be at least 3 values long.')

		curr = self.root
		i = 1
		
		while i < len(pathFromRoot):
			try:
				curr = curr.getChildByValue(value = pathFromRoot[i])
				if curr is None:
					return None
			except AttributeError:
				break

			if (i == len(pathFromRoot) - 1) and len(curr.children) == 0:
				return curr.name
			elif (i == len(pathFromRoot) - 1) and curr.name is not None:
				return curr.name
			else:
				i += 1

	def stupidVisualizer(self):
		'''
		TODO
		'''
		raise NotImplementedError

if __name__ == '__main__':
	import doctest
	doctest.testmod()