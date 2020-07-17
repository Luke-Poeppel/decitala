
# From https://rigtorp.se/2011/01/01/rolling-statistics-numpy.html
def rolling_window(a, window):
	shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
	strides = a.strides + (a.strides[-1],)
	
	return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

#---------------------------------------------------------------------------------------------------
								####### OCCURRENCE OVERLAP ########
'''
Given a list of tuples containging the name of a decitala and their occurrence, returns the list 
of the best fit. This is actually an example of the Range Non-Overlapping Index Problem. I'm 
currently searching iteratively to find the 'next value' in the list. It would be far quicker 
to run a binary search algorithm that checks all values *after* the current one. 

(If you hold the indices in tuples rather than list, you can use the in method because tuples are 
hashable.) 
'''
def binary_search(lst, searchVal):
	'''
	>>> l = [5, 1, 2, 6, 20, 8]
	>>> l.sort()
	>>> binary_search(lst = l, searchVal = 2)
	True
	'''
	def _checkSorted(lstIn):
		if len(lstIn) == 1:
			return True
		else:
			remainder = _checkSorted(lstIn[1:])
			return lstIn[0] <= lstIn[1] and remainder

	startIndex = 0
	endIndex = len(lst) - 1
	found = False

	if _checkSorted(lst) == False:
		raise Exception('Input list is not sorted.')

	while startIndex <= endIndex and not found:
		midpoint = (startIndex + endIndex) // 2
		if lst[midpoint] == searchVal:
			found = True 
		else:
			if lst[midpoint] > searchVal:
				endIndex = midpoint - 1
			else:
				startIndex = midpoint + 1

	return found

def _checkTupleContainment(lstIn, curr):
	'''
	Given two lists of tuples, returns whether the first is contained by the second. 

	>>> l = [(1.0, 2.0), (1.5, 3.5), (2.0, 2.5)]
	>>> tuplesIn = [(1.0, 2.0), (2.0, 2.5)]
	>>> _checkTupleContainment(tuplesIn, l)
	True
	>>> _checkTupleContainment([(2.0, 2.25)], l)
	False
	'''
	return all(elem in curr for elem in lstIn)

def _removeSubsets(collection):
	'''
	_removeSubsets([[(6.0, 7.25)], [(4.0, 5.5)], [(4.0, 5.5), (6.0, 7.25)]])
	[[(4.0, 5.5), (6.0, 7.25)]]
	'''
	newCollection = copy.copy(collection)
	i = 0
	while i < len(newCollection):
		i += 1

def getAllEndOverlappingIndices(lst, i, out):
	'''
	This is a work in progress. The range non-overlapping index problem requires checking all 
	possible contiguous values; but searching linearly is *far* too slow! 

	Possible paths: 
	[(0.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
	[(0.0, 2.0), (2.5, 4.5), (6.0, 7.25)]
	[(0.0, 2.0), (2.0, 5.75), (6.0, 7.25)]
	[(0.0, 2.0), (2.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
	'''
	allPossibilities = []

	def _getAllEndOverlappingIndices_helper(listIn, i, out):
		#_getAllEndOverlappingIndices_helper.count += 1
		#if _getAllEndOverlappingIndices_helper.count % 10000 == 0:
			#print(_getAllEndOverlappingIndices_helper.count)

		r = -1
		if i == len(listIn):
			if out:
				if len(allPossibilities) == 0:
					allPossibilities.append(out)
				else:						
					allPossibilities.append(out)

			return 

		n = i + 1

		while n < len(listIn) and r > listIn[n][0]:
			n += 1
		_getAllEndOverlappingIndices_helper(listIn, n, out)

		r = listIn[i][1]

		n = i + 1
		while n < len(listIn) and r > listIn[n][0]:
			n += 1

		_getAllEndOverlappingIndices_helper(listIn, n, out + [listIn[i]])

	_getAllEndOverlappingIndices_helper.count = 0
	lst.sort()
	_getAllEndOverlappingIndices_helper(listIn = lst, i = 0, out = [])
	
	#print('final tracker:', _getAllEndOverlappingIndices_helper.count)
	#print('')
	return allPossibilities

indices = [(0.0, 2.0), (0.0, 4.0), (2.5, 4.5), (2.0, 5.75), (2.0, 4.0), (6.0, 7.25), (4.0, 5.5)]
indices.sort()
print(getAllEndOverlappingIndices(lst = indices, i = 0, out = []))
#for this in getAllEndOverlappingIndices(lst = indices, i = 0, out = []):
	#print(this)

#iterative solution
def _isInRange(num, tupleRange) -> bool:
	'''
	Given an input number and a tuple representing a range (i.e. from startVal to endVal), returns
	whether or not the input number is in that range. 

	>>> _isInRange(2.0, (2.0, 2.0))
	True
	>>> _isInRange(3.0, (2.0, 4.0))
	True
	>>> _isInRange(4.0, (2.0, 2.5))
	False
	>>> _isInRange(4.0, (3.0, 4.0))
	True
	'''
	if tupleRange[0] > tupleRange[1]:
		raise Exception('Invalid Range')
	elif tupleRange[0] == tupleRange[1] and num == tupleRange[0]:
		return True
	elif tupleRange[0] == tupleRange[1] and num != tupleRange[0]:
		return False
	else:
		if num > tupleRange[0] or num == tupleRange[0]:
			if num < tupleRange[1] or num == tupleRange[1]:
				return True
			else:
				return False
		else:
			return False

def _checkTupleContainment(lstIn, curr):
	'''
	Given two lists of tuples, returns whether the first is contained by the second. 

	>>> l = [(1.0, 2.0), (1.5, 3.5), (2.0, 2.5)]
	>>> tuplesIn = [(1.0, 2.0), (2.0, 2.5)]
	>>> _checkTupleContainment(tuplesIn, l)
	True
	>>> _checkTupleContainment([(2.0, 2.25)], l)
	False
	'''
	return all(elem in curr for elem in lstIn)

def getAllLongestEndOverlappingIndices(lst):
	'''
	Binary search in iterative solution would be the fastest. 

	Given list of tuples containing indices, returns the longest possible paths that overlap only 
	by final/starting points. 

	Since it's sorted by first, look for the closest value that satisfies the range requirement. 
	If the next closest path is good, continue the search through the end of the list. 

	>>> indices = [(0.0, 2.0), (0.0, 4.0), (2.5, 4.5), (2.0, 5.75), (2.0, 4.0), (6.0, 7.25), (4.0, 5.5)]

	[(0.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
	[(0.0, 2.0), (2.5, 4.5), (6.0, 7.25)]
	[(0.0, 2.0), (2.0, 5.75), (6.0, 7.25)]
	[(0.0, 2.0), (2.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
	'''
	lst.sort(key = lambda x: x[0])
	longestPossibilites = []

	currIndex = 0
	while currIndex < len(lst):
		curr = lst[currIndex]
		start = curr[0]
		end = curr[1]

		i += 1

	return longestPossibilites

'''
Testing:
#for this in getAllEndfOverlappingIndices(indices, i = 0, out = []):
	#print(this)

We need to change the above function to eliminate waste. We generate the following output for this
list:
l = [(0.0, 2.0), (0.0, 4.0), (2.5, 4.5), (2.0, 5.75), (2.0, 4.0), (6.0, 7.25), (4.0, 5.5)]

[(6.0, 7.25)]
[(4.0, 5.5)]
[(4.0, 5.5), (6.0, 7.25)]
[(2.5, 4.5)]
[(2.5, 4.5), (6.0, 7.25)]
[(2.0, 5.75)]
[(2.0, 5.75), (6.0, 7.25)]
[(2.0, 4.0)]
[(2.0, 4.0), (6.0, 7.25)]
[(2.0, 4.0), (4.0, 5.5)]
[(2.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
[(0.0, 4.0)]
[(0.0, 4.0), (6.0, 7.25)]
[(0.0, 4.0), (4.0, 5.5)]
[(0.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
[(0.0, 2.0)]
[(0.0, 2.0), (6.0, 7.25)]
[(0.0, 2.0), (4.0, 5.5)]
[(0.0, 2.0), (4.0, 5.5), (6.0, 7.25)]
[(0.0, 2.0), (2.5, 4.5)]
[(0.0, 2.0), (2.5, 4.5), (6.0, 7.25)]
[(0.0, 2.0), (2.0, 5.75)]
[(0.0, 2.0), (2.0, 5.75), (6.0, 7.25)]
[(0.0, 2.0), (2.0, 4.0)]
[(0.0, 2.0), (2.0, 4.0), (6.0, 7.25)]
[(0.0, 2.0), (2.0, 4.0), (4.0, 5.5)]
[(0.0, 2.0), (2.0, 4.0), (4.0, 5.5), (6.0, 7.25)]

But if one possibility contains another one, this should be eliminated!
'''

#---------------------------------------------------------------------------------------------------
############ HELPER FUNCTIONS ############



class FragmentTree(object):
	'''
	Class for the ratio and different representation of rhythmic fragments in n-ary tree format. 
	The input must be a path to a directory of XML/MXL files. In creating the tree, it automatically
	creates a list that holds Decitala(fileName) for each filename in the directory. It also creates
	a folder that holds the reduced data. 

	TODO: I need to be keeping track of rests in all cases! The indices of occurrence can't be based
	upon placement of notes, but have to be based on placement of all musical objects. 
	'''
	def __init__(self, directory):
		if type(directory) != str:
			raise Exception('Path to directory must be a string.')
		else:
			self.directory = directory

		rawData = []
		for thisFile in os.listdir(directory):
			rawData.append(Decitala(thisFile))

		self.rawData = rawData

		def filterData(rawData):
			'''
			Given a list of decitala objects (i.e. converted to a matrix of duration vectors), 
			filterData() removes:
			- Trivial fragments (single-onset fragments and double onset fragments, the latter 
			by convention). 
			- Duplicate fragments
			- Multiplicative Augmentations/Diminutions (by using the cauchy-schwarz inequality); if 
			two duration vectors are found to be linearly dependant, one is removed.

			Consider the following set of rhythmic fragments.
			[3.0, 1.5, 1.5, 0.75, 0.75],
			1.5, 1.0],
			[0.75, 0.5, 0.75],
			[0.25, 0.25, 0.5],
			[0.75, 0.5],
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

			NOTE: this function is one of the many reasons I should have the Greek Metric and Decitala
			classes inherit from some greater class RhythmicFragment. I wouldn't have to have the data
			be a list of decitalas, but instead a list of RhythmicFragments
			'''
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
		self.size = len(self.filteredData)

		def constructRatioTree():
			'''
			Given the filtered data, constructs a ratio tree. For some strange reason, it won't allow 
			me to create the tree in one simple loop. So, this is how we have to do it (for now). 
			'''
			ratioTree = NAryTree()
			rootNode = NAryTree().Node(value = 1.0, name = 'ROOT')

			possibleOnsetNums = [3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]
			i = 0
			while i < len(possibleOnsetNums):
				currOnsetList = []
				for thisTala in self.filteredData:
					if len(thisTala.qlList()) == possibleOnsetNums[i]:
						currOnsetList.append(thisTala)
				for thisTala in currOnsetList:
					rootNode.addPathOfChildren(path = successiveRatioList(thisTala.qlList()), finalNodeName = thisTala)
				i += 1

			ratioTree.root = rootNode

			return ratioTree

		self.ratioTree = constructRatioTree()

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

	def __repr__(self):
		return '<FRAGMENT-TREE: rawSize={0}, reducedSize={1}>'.format(len(self.rawData), len(self.filteredData))

	def __iter__(self):
		'''
		Iteration defaults to the talas in the ratio tree. 
		'''
		for thisFragment in self.ratioTree:
			yield thisFragment

	def getByQlList(self, qlList, tryAllMethods = True):
		'''
		Given a quarter length list, returns whether the fragment is found in either the ratio or 
		difference tree. 

		1.) Check ratio tree normal.
		2.) Check ratio tree retrograde.
		3.) Check difference tree.
		4.) Check difference tree retrograde.
		4.) Check added values. (Function that takes in qlList, searches and removes all found 
		added values and then searches again.) 
		'''
		retrograde = qlList[::-1]

		ratioList = successiveRatioList(qlList)
		differenceList = successiveDifferenceList(qlList)

		retrogradeRatioList = successiveRatioList(retrograde)
		retrogradeDifferenceList = successiveDifferenceList(retrograde)

		if tryAllMethods == False:
			return self.ratioTree.searchForPath(ratioList)
		else:
			ratioSearch = self.ratioTree.searchForPath(ratioList)
			if ratioSearch is None:
				retrogradeRatioSearch = self.ratioTree.searchForPath(retrogradeRatioList)
				if retrogradeRatioSearch is None:
					differenceSearch = self.differenceTree.searchForPath(differenceList)
					if differenceSearch is None:
						retrogradeDifferenceSearch = self.differenceTree.searchForPath(retrogradeDifferenceList)
						if retrogradeDifferenceSearch is None:
							return None
							# Trigger valeur ajoutee function? 
							# removedAddedValues = removeAddedValues(qlList)
							# if not None: return removedAddedValues, 'added value(s) removed'
						else:
							return retrogradeDifferenceSearch, 'retrograde difference'
					else:
						return differenceSearch, 'difference'
				else:
					return retrogradeRatioSearch, 'retrograde ratio'
			else:
				return ratioSearch, 'ratio'

	def _searchWithAddedValuesRemoved(self, qlList):
		'''
		Given a qlList, checks if there are any added values in it. If so, removes them and searches
		the tree. One *very* important thing to note is that some of the fragments do, in fact, have
		added values in them –– we must be sure not to remove any added values that already belong 
		to the fragment... 

		We generate the 'power list' of the set of indices where added values have been found. We 
		then run the standard search with all possible combinations of indices included/removed. 
		There will be 2^n - 1 possible combinations of indices to remove. 
		'''
		indices = getAddedValues(qlList, printType = False)
		allCombinations = powerList(lst = indices)

		print(allCombinations)

		for thisCombination in allCombinations:
			asLst = list(thisCombination)
			newQlList = copy.copy(qlList)
			for thisIndex in sorted(asLst, reverse = True):
				del newQlList[thisIndex]

			x = self.getByQlList(qlList = newQlList)
			if x is not None:
				return x
			else:
				continue
				'''
				if thisCombiation is allCombinations[-1]:
					return None
				else:
					continue
				'''

	def searchDifferenceTree(self, qlList):
		differenceList = successiveDifferenceList(qlList)
		return self.differenceTree.searchForPath(differenceList)

#---------------------------------------------------------------------------------------------------
							####### SCORE SEARCH DECEMBER 28 2019 ########
	'''
	NOTE: In the searching algorithms, there should be some checkUsedCatalogue option.
	'''
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
		'''
		score = converter.parse(f)
		partIn = score.parts[p]
		objLst = []

		stripped = partIn.stripTies(retainContainers = True)
		for thisObj in stripped.recurse().iter.notesAndRests:
			objLst.append(thisObj)

		return objLst

	def getIndicesOfObjectOccurrence(self, filePath, partNum):
		'''
		Given a file path and part number, returns a list containing tuples

		[(OBJ, (start, end))]
		'''
		indices = []
		strippedObjects = self._getStrippedObjectList(f = filePath, p = partNum)
		for thisObj in strippedObjects:
			indices.append((thisObj, (thisObj.offset, thisObj.offset + thisObj.quarterLength)))

		return indices

	def getByNumOnsets(self, numOnsets):
		'''
		Searches the ratio tree for all paths of length numOnsets. 
		'''
		for thisTala in self.ratioTree.allNamedPathsOfLengthN(n = numOnsets):
			yield thisTala

	def getMatchesByQlList(self, qlList, startOn = False, tryRetrograde = False):
		raise NotImplementedError

	def getMatchesBySuccessiveRatioList(self, successiveRatioList):
		raise NotImplementedError

	def getMatchesByCarnaticString(self, carnaticString):
		raise NotImplementedError

	def getMatchesByGreekString(self, greekString):
		raise NotImplementedError

	def partitionSearch(self, filePath, pathToWrite, part, partitions = [], showScore = False):
		'''
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
		'''
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
					x = self.getByQlList(qlList = thisChunk)
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

	def rollingSearch(self, filePath, partNum, possibleWindows = [3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]):
		'''
		Given a filepath and a part number, runs a rolling search algorithm on the part that 
		returns all decitalas found in the tree. Returns a list of tuples that holds the name of 
		the tala and the indices of occurrence. 

		TODO: include the pathToWrite input –– easier for data processing. 
		TODO: time this function with a function that ALSO checks a catalogue. See which is faster. 
		TODO: add restrictWindow that only searches windows of length n. 
		'''
		qlList = self._getStrippedQlListOfStream(filePath, part = partNum)

		lists = []
		for thisWin in possibleWindows:
			for thisFrame in rollWindow(qlList, thisWin):
				lists.append(thisFrame)

		#append to list and add indicies of occurrence. 
		for thisList in lists:
			searched = self.getByQlList(qlList = thisList, tryAllMethods = True)
			if searched is not None:
				print(searched[0], searched[0].qlList())

		return

	def rollingSearch2(self, filePath, partNum, possibleWindows = [3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]):
		'''
		Returns the decitalas found and they're window of occurrence. 

		Get the list of everything to keep track of the onsets –– only search for windows of notes 
		and, at most, rests of length 0.25. 

		outLst is the list of all decitalas with their windows of occurrence. Will require some kind
		of summing over a range...
		'''
		objLst = self.getIndicesOfObjectOccurrence(filePath = filePath, partNum = partNum)
		outLst = []
		frames = []

		for thisWin in possibleWindows:
			for thisFrame in rollWindow(lst = objLst, window = thisWin):
				frames.append(thisFrame)

		for thisFrame in frames:
			'''
			With thisFrame, I have all of the data I need stored! 
			'''
			asQl = []
			for thisObj, thisRange in thisFrame:
				if thisObj.isRest:
					if thisObj.quarterLength == 0.25:
						asQl.append(thisObj)
					else:
						pass		
				asQl.append(thisObj.quarterLength)

			searched = self.getByQlList(qlList = asQl, tryAllMethods = True)
			if searched is not None:
				off1 = thisFrame[0][0]
				off2 = thisFrame[-1][0]

				outLst.append((searched, (off1.offset, off2.offset + off2.quarterLength)))
				#outLst.append((searched, (thisFrame[0][0].offset, thisFrame[0][-1].offset))) #SUM OVER FOR RANGE!#

			#if thisFrame has a rest that isn't 0.25: skip, else: keep going. 
		#return frames

		return outLst

#---------------------------------------------------------------------------------------------------
	def bestFit(self, data):
		'''
		Given a list of tuples holding tâlas and their indices of occurrence, returns a new tuple
		consiting of the "best fit" of the tâlas.
		'''
		pass

	def annotateScoreByNumNote(self, filePath, onsetNum, data = []):
		'''
		Given foundTala data (by rollingSearch), annotates a given score for all n-onset talas. 
		'''
		pass