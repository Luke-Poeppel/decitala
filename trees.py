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
NOTE:
TODO:
"""
################################# WINDOWS ###################################
def partitionByWindows(lst, partitionLengths = [], repeat = True):
	'''
	This function takes in a sequence and a list of partition lengths. It generates sub-lists,
	each with a length corresponding to the values in partitionLengths. If repeat is set to True,
	it will do so repeatedly. Given that there may be a remainder (modulus), the final subset 
	returned may be of a different size. 

	>>> s = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
	>>> for thisPartition in partitionByWindows(s, partitionLengths = [1, 2, 3]):
	...     print(thisPartition)
	[3]
	[1, 4]
	[1, 5, 9]
	[2]
	[6, 5]
	[3, 5]

	>>> s2 = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7]
	>>> partitionByWindows(s2, partitionLengths = [7, 4])
	[[3, 1, 4, 1, 5, 9, 2], [6, 5, 3, 5], [8, 9, 7]]
	'''
	it = iter(lst)

	numOfRepeats = (len(lst) // sum(partitionLengths)) + 1
	newPartitions = numOfRepeats * partitionLengths
	allSlices = [s for s in (list(itertools.islice(it, 0, i)) for i in newPartitions)]

	remainder = list(it)
	if remainder:
		allSlices.append(remainder)

	for thisSlice in allSlices:
		if len(thisSlice) == 0:
			allSlices.remove(thisSlice)

	return allSlices

def roll_window(lst, window):
	'''
	This function takes in a list and returns a list of all windows of a provided length, rolling
	from the starting index to the point at which the window hits the final value of the list. 

	>>> l = ['Mozart', 'Monteverdi', 'Messiaen', 'Mahler', 'MacDowell', 'Massenet']
	>>> for this in roll_window(l, 3):
	...     print(this)
	['Mozart', 'Monteverdi', 'Messiaen']
	['Monteverdi', 'Messiaen', 'Mahler']
	['Messiaen', 'Mahler', 'MacDowell']
	['Mahler', 'MacDowell', 'Massenet']
	'''
	if type(window) != int:
		raise Exception('The window must be an integer!')

	l = []

	iterable = iter(lst)
	win = []
	for _ in range(0, window):
		win.append(next(iterable))
	
	l.append(win)

	for thisElem in iterable:
		win = win[1:] + [thisElem]
		l.append(win)

	return l

#l = [(1.0, 'a'), (2.0, 'b'), (3.0, 'c'), (4.0, 'd'), (5.0, 'e'), (6.0, 'f')]
#print(roll_window(lst = l, window = 3))

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
	>>> for thisPath in TestTree.all_named_paths_of_length_n(length = 3):
	...     print(thisPath)
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
		A Node object stores an item and references its parent and children. In an nary tree, a parent
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
				raise Exception('Nodes must be contained in a list.')
			
			for this_child in children_nodes:
				self.add_child(this_child)
			return

		def add_path_of_children(self, path, final_node_name):
			"""
			Allows for the the addition of a path of values from a node down through its children. 
			"""
			if path[0] != self.value:
				raise Exception('First value in the path must be self.value.')

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
				raise Exception('This parent does not have that child!')
			self.children.remove(child_node.item.value)
			return

		def remove_children(self, children_nodes):
			for this_child in children_nodes:
				self.remove_child(this_child)
			return

		def get_child(self, node):
			"""
			Given a ``value``, returns the node in the set of children with that associated value. 
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

	def __init__(self):
		self.root = None

	def __repr__(self):
		return '<NaryTree: nodes={0}>'.format(self.size())

	def __iter__(self):
		"""
		Iterates through all named paths in the tree (not nodes), beginning with the 
		shortest paths (of length 2) and ending with paths from the root to the leaves. Ignores 
		paths that do not conclude with a labeled node. 
		"""
		for this_named_path in self.all_named_paths():
			yield this_named_path

	def _size_helper(self, node):
		"""
		Helper function for self.size()
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
		Helper function for self.all_possible_paths()
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
		Prints all possible paths from the root node, not all of which are necesarrily named. 
		"""
		return self._all_possible_paths_helper(self.root)

	################################################################################################
	def _all_named_paths_helper(self, node, path = []):
		"""
		Helper function for self.all_named_paths. 
		"""
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
				yield from self._all_named_paths_helper(child, path)

		path.pop()

	def all_named_paths(self):
		"""
		Returns all paths from the root that are named. Each path is returned as a tuple consisting
		of the path followed by its name, i.e., ([PATH], 'NAME'). 
		"""
		for this_named_path in self._all_named_paths_helper(self.root):
			yield this_named_path

	################################################################################################
	def _all_mamed_paths_of_length_n_helper(self, node, length_in, path = []):
		'''
		Helper function for self.all_named_paths_of_length_n
		'''
		path.append(node)

		if path[-1].name is not None:
			p = [node.value for node in path]
			if len(p) == length_in:
				yield path[-1].name
				#yield (path[-1].name, p)
		else:
			pass

		if len(node.children) == 0:
			pass
		else:
			for child in node.children:
				yield from self._all_mamed_paths_of_length_n_helper(child, length_in, path)

		path.pop()

	def all_named_paths_of_length_n(self, length):
		"""
		Returns all named paths from the root of provided length. 
		"""
		for this_named_path_of_length_n in self._all_mamed_paths_of_length_n_helper(node = self.root, length_in = length):
			yield this_named_path_of_length_n

	################################################################################################
	def search_for_path(self, path_from_root):
		"""
		Searches through the nary tree for a path consisting of the values in the path_from_root
		list. Note: the first value of the path must either be 1 (ratio representation search) or 
		0 (difference representation search). Call me old-fashioned, but I feel like there should be 
		a difference in output between a path being present but unnamed and path not existing. 
		"""
		#if pathFromRoot[0] != 1.0 or 0.0:
			#raise Exception('Path provided is invalid.')
		if len(path_from_root) <= 2:
			raise Exception('Path provided must be at least 3 values long.')

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

############################### FRAGMENT TREES ##################################
class FragmentTree(NaryTree):
	"""
	Nary tree for holding ratio and different representation of rhythmic fragments. 

	TODO
	- keep track of rests in all cases. The indices of occurrence can't be based
	upon placement of notes, but have to be based on placement of *all* musical objects. 
	- cauchy-schwartz inequality is completely unnecessary (I think) since we're using ratio representations.
	not sure how this applies for difference representations. 
	- decide on double-onset fragment convention. I'm leaning towards keep them since some of them are odd. 
	"""
	def __init__(self, root_path, frag_type, rep_type, **kwargs):
		if type(root_path) != str:
			raise Exception('Path must be a string.')
		
		if rep_type.lower() not in ['ratio', 'difference']:
			raise Exception('The only possible types are "ratio" and "difference"')
		
		self.root_path = root_path
		self.frag_type = frag_type
		self.rep_type = rep_type

		super().__init__()

		if frag_type.lower() == 'decitala':
			raw_data = []
			for this_file in os.listdir(root_path):
				raw_data.append(Decitala(this_file))
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
	
	def get_by_ql_list(self, ql_list, try_all_methods = True):
		'''
		Given a quarter length list, returns whether the fragment is found in the tree. If
		try_all_methods is set to true, searches the tree for the exact ratio/difference representation. 
		Otherwise, checks in the following order. 

		NOTE: want ql -> retro -> ratio/difference! 

		1.) Check ratio/difference tree normal.
		2.) Check ratio/difference tree retrograde.
		4.) Checks all permutations of added values removed. 
		'''
		retrograde = ql_list[::-1]
		ratio_list = successive_ratio_list(ql_list)
		difference_list = successive_difference_array(ql_list)
		retrograde_ratio_list = successive_ratio_list(retrograde)
		retrograde_difference_list = successive_difference_array(retrograde)

		if self.rep_type == 'ratio':
			if not (try_all_methods):
				return self.search_for_path(ratio_list)
			else:
				ratio_search = self.search_for_path(ratio_list)
				if ratio_search is None:
					retrograde_ratio_search = self.search_for_path(retrograde_ratio_list)
					if retrograde_ratio_search is None:
						#ADDED VALUE PERMUTATIONS
						return None	
					else:
						ratio = _ratio(retrograde_ratio_search.ql_array(), 0)
						return (retrograde_ratio_search, ('retrograde', ratio))
				else:
					ratio = _ratio(ratio_search.ql_array(), 0)
					return (ratio_search, ('ratio', ratio))

		if self.rep_type == 'difference':
			if not (try_all_methods):
				return self.search_for_path(difference_list)
			else:
				difference_search = self.search_for_path(difference_list)
				if difference_search is None:
					retrograde_difference_search = self.search_for_path(retrograde_difference_list)
					if retrograde_difference_search is None:
						#ADDED VALUE PERMUTATIONS
						return None	
					else:
						return retrograde_difference_search, '(retrograde)'
				else:
					return difference_search, '(difference)'
	
	def search_with_added_values_removed(self, ql_list):
		'''
		Given a quarter length list, checks if there are any added values in it. If so, removes them 
		and searches the tree. One important thing to note is that some of the fragments already have
		added values in them; as such, we first check the tree with the input fragment before removing
		any values. 
		
		We generate the 'power list' (length 2^n - 1) of the set of indices where added values have been found. 
		We then run the standard search with all possible combinations of indices included/removed. There
		may be several options, so this function returns a generator. 
		'''
		indices = get_added_values(ql_list, print_type=False)
		all_combinations = powerList(lst = indices)

		for thisCombination in all_combinations:
			asLst = list(thisCombination)
			newQlList = copy.copy(ql_list)
			for thisIndex in sorted(asLst, reverse = True):
				del newQlList[thisIndex]

			x = self.get_by_ql_list(ql_list = newQlList)
			if x is not None:
				yield x
			else:
				continue
	
	def get_by_num_onsets(self, num_onsets):
		"""
		Searches the ratio tree for all paths of length numOnsets. 
		"""
		for thisTala in self.all_named_paths_of_length_n(length = num_onsets):
			yield thisTala
	
	############################# Search #############################

	def _getStrippedQlListOfStream(self, filePath, part):
		'''
		Returns the quarter length list of an input stream (with all ties removed).  
		'''
		fullScore = converter.parse(filePath)
		part = fullScore.parts[part]

		flattenedAndStripped = part.flat.stripTies()

		qlList = []
		for thisNote in flattenedAndStripped.notes:
			qlList.append(thisNote.quarterLength)

		return qlList
	
	def _getStrippedObjectList(self, f, p = 0):
		'''
		Returns the quarter length list of an input stream (with ties removed), but also includes 
		spaces for rests! 

		NOTE: this used to be .iter.notesAndRest, but I took it away, for now, to avoid complications.
		'''
		score = converter.parse(f)
		partIn = score.parts[p]
		objLst = []

		stripped = partIn.stripTies(retainContainers = True)
		for thisObj in stripped.recurse().iter.notes: 
			objLst.append(thisObj)

		return objLst
	
	def get_indices_of_object_occurrence(self, file_path, part_num):
		'''
		Given a file path and part number, returns a list containing tuples

		[(OBJ, (start, end))]
		'''
		indices = []
		strippedObjects = self._getStrippedObjectList(f = file_path, p = part_num)
		for thisObj in strippedObjects:
			indices.append((thisObj, (thisObj.offset, thisObj.offset + thisObj.quarterLength)))

		return indices
	
	def partitionSearch(self, filePath, pathToWrite, part, partitions = [], showScore = False):
		"""
		This method of search is not as comprehensive as rollingSearch, but it still has useful 
		applications. 

		TODO: implement the set check. If tala is not found, try the translational augmentation and 
		then the retrograde. 
		TODO: If the fragment is not found on partition, lyric shouldn't be STOP, it should be nff or 
		something similar.
		TODO: Data should have a count under every tala. 
		TODO: Since the hashing algorithm has been improved (should this be in Decitala...?), after 
		a fragment has been found, add it to a set. Before searching the tree for a fragment, check
		for inclusion in the set. 
		"""
		fullScore = converter.parse(filePath)
		p = fullScore.parts[part]
		objectList = []
		qlList = []

		title = fullScore.metadata.title
		pName = p.partName

		foundTalas = set()

		#TOP OF FILE
		current = datetime.datetime.now()
		currStr = current.strftime('%Y-%m-%d_%H:%M')
		fileName = 'Tala_Data_{}'.format(currStr)
		complete = os.path.join(pathToWrite, fileName+ '.txt')
		data = open(complete, 'w+')
		data.write('DECITALA DATA: ' + title + '\n')
		data.write('PART: ' + pName + ' ({0})'.format(str(part)) + '\n')
		data.write('SEARCH TYPE: Partition \n')
		data.write('Partition Lengths: ' + str(partitions) + '\n')
		data.write('--------------------------------------------------------- \n')

		#--------------------------------------
		#QL-LIST
		'''
		Double for loop for ql list and min-offset. Can they be combined?
		'''
		for thisObj in p.recurse().iter.notes:
			objectList.append(thisObj)

		for i, thisObj in enumerate(objectList):
			if thisObj.tie is not None:
				nextObj = objectList[i + 1]
				qlList.append(thisObj.duration.quarterLength + nextObj.duration.quarterLength)
				del objectList[i + 1]
			else:
				qlList.append(thisObj.duration.quarterLength)

		#--------------------------------------
		#MIN OFFSET
		for thisObj in p.recurse().iter.notes:
			try:
				if thisObj.isNote:
					minMusOffset = thisObj.offset
					break
				elif thisObj.isChord:
					minMusOffset = thisObj.offset
					break
			except AttributeError:
				break

		data.write('[0.0-{0}]: Empty\n'.format(str(minMusOffset)))

		partitions = partitionByWindows(lst = qlList, partitionLengths = partitions)
		partitions_copy = copy.copy(partitions)
		offsets = [minMusOffset]
		netSum = sum(qlList)

		i = minMusOffset
		talas = []

		while (i < netSum):
			for j, thisChunk in enumerate(partitions_copy):
				if len(thisChunk) < 3:
					pass
				else:
					x = self.get_by_ql_list(ql_list = thisChunk)
				if x is not 'Tala Not Found in Search Tree.': # not None? 
					foundTalas.add(x)
					talas.append(x)

					sumTo = sum(partitions_copy[j][0:-1]) + i
					try: 
						offsets.append(sumTo)
						data.write('[{0}-{1}]: '.format(str(i), str(sumTo)))
						data.write(x.name + '\n')
					except (IndexError, AttributeError) as e:
						pass

					offsets.append(sum(partitions_copy[j]) + i)
					i += sum(partitions_copy[j])
				else:
					pass

		#ADD TEXT
		for thisObj in p.recurse().iter.notes:
			for thisOffset, thisTala in zip(offsets[0::2], talas):
				try:
					if thisOffset == thisObj.offset:
						thisObj.lyric = thisTala.name
						thisObj.style.color = 'green'
				except AttributeError:
					pass
			for thisOffset in offsets[1::2]:
				try:
					if thisOffset == thisObj.offset:
						thisObj.lyric = 'STOP'
						thisObj.style.color = 'red'
				except AttributeError:
					pass

		if showScore == True:
			p.show()
		else:
			return

	def rolling_search(self, path, part_num, possible_windows = [3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]):
		"""
		Runs a windowed search on an input stream and path number. Returns the decitalas found and the 
		indices of occurrence. 
		"""
		object_list = self.get_indices_of_object_occurrence(file_path = path, part_num = part_num)
		fragments_found = []
		frames = []

		for this_win in possible_windows:
			for this_frame in roll_window(lst = object_list, window = this_win):
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

			searched = self.get_by_ql_list(ql_list = as_quarter_lengths, try_all_methods=True)
			if searched is not None:
				offset_1 = this_frame[0][0]
				offset_2 = this_frame[-1][0]

				fragments_found.append((searched, (offset_1.offset, offset_2.offset + offset_2.quarterLength)))
				#fragments_found.append((searched, (thisFrame[0][0].offset, thisFrame[0][-1].offset))) #SUM OVER FOR RANGE!#

		return fragments_found

'''
t = FragmentTree(root_path = decitala_path, frag_type = 'decitala', rep_type = 'ratio')

decitala_path = '/Users/lukepoeppel/decitala_v2/Decitalas'
sept_haikai_path = '/Users/lukepoeppel/Desktop/Messiaen/Sept_Haikai/1_Introduction.xml'

for this_tala in t.rolling_search(sept_haikai_path, 1):
	print(this_tala)

'''



