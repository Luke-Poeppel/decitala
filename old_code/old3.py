		def filterData(rawData):
			"""
			Given a list of decitala or greek foot objects, removes:
			- single and double-onset fragments and double onset fragments.
			- duplicate fragments
			- fragments that are multiplicative augmentations/diminutions of others; this is accomplished
			with the cauchy-schwarz inequality; if two ql_arrays are linearly dependant, one is removed.

			Consider the following set of rhythmic fragments.
			[3.0, 1.5, 1.5, 0.75, 0.75]
			[1.5, 1.0]
			[0.75, 0.5, 0.75]
			[0.25, 0.25, 0.5]
			[0.75, 0.5]
			[0.5, 1.0, 2.0, 4.0]
			[1.5, 1.0, 1.5]
			[1.0, 1.0, 2.0]
			[1.0, 0.5, 0.5, 0.25, 0.25]
			[0.25, 0.5, 1.0, 2.0]

			This function reduces this list to:
			[0.75, 0.5]
			[0.75, 0.5, 0.75]
			[0.25, 0.25, 0.5]
			[0.25, 0.5, 1.0, 2.0]
			[1.0, 0.5, 0.5, 0.25, 0.25]

			NOTE: this function is one of the many reasons I should have the Greek Metric and Decitala
			classes inherit from some greater class RhythmicFragment. I wouldn't have to have the data
			be a list of decitalas, but instead a list of RhythmicFragments
			"""
			copied = copy.copy(rawData)
			size = len(copied)

			i = 0
			while i < size:
				try:
					if len(copied[i].qlList()) <= 2:
						del copied[i]
					else:
						pass
				except IndexError:
					pass

				for j, cursor_vector in enumerate(copied):
					try: 
						if i == j:
							pass
						elif len(copied[i].qlList()) != len(copied[j].qlList()):
							pass
						elif cauchy_schwartz(copied[i].qlList(), copied[j].qlList()) == True:
							pass
						elif cauchy_schwartz(copied[i].qlList(), copied[j].qlList()) == False:
							firsti = copied[i].qlList()[0]
							firstj = copied[j].qlList()[0]

							#Equality removes the second one; random choice. 
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

		self.filteredData = filterData(self.rawData)

		def ratio_tree():
			'''
			Given the filtered data, constructs a ratio tree. For some strange reason, it won't allow 
			me to create the tree in one simple loop. So, this is how we have to do it (for now). 
			'''
			ratio_tree = NaryTree()
			root_node = NaryTree().Node(value = 1.0, name = 'ROOT')

			possible_num_onsets = [3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]
			i = 0
			while i < len(possible_num_onsets):
				currOnsetList = []
				for thisTala in self.filteredData:
					if len(thisTala.qlList()) == possible_num_onsets[i]:
						currOnsetList.append(thisTala)
				for thisTala in currOnsetList:
					root_node.addPathOfChildren(path = successiveRatioList(thisTala.qlList()), finalNodeName = thisTala)
				i += 1

			ratio_tree.root = root_node

			return ratio_tree

		self.ratio_tree = ratio_tree()
	
		def constructDifferenceTree():
			'''
			Given the filtered data, constructs a difference tree.
			'''
			differenceTree = NAryTree()
			rootNode = NAryTree().Node(value = 0.0, name = 'ROOT')

			possibleOnsetNums = [3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]
			i = 0
			while i < len(possibleOnsetNums):
				currOnsetList = []
				for thisTala in self.filteredData:
					if len(thisTala.qlList()) == possibleOnsetNums[i]:
						currOnsetList.append(thisTala)
				for thisTala in currOnsetList:
					rootNode.addPathOfChildren(path = successiveDifferenceList(thisTala.qlList()), finalNodeName = thisTala)
				i += 1

			differenceTree.root = rootNode

			return differenceTree

		self.differenceTree = constructDifferenceTree()

f = FragmentTree(root_path = '/Users/lukepoeppel/decitala_v.2.0/Decitalas')