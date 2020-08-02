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

			searched = self.get_by_ql_list(ql_list = as_quarter_lengths, try_all_methods=True)
			if searched is not None:
				offset_1 = this_frame[0][0]
				offset_2 = this_frame[-1][0]

				fragments_found.append((searched, (offset_1.offset, offset_2.offset + offset_2.quarterLength)))
				#fragments_found.append((searched, (thisFrame[0][0].offset, thisFrame[0][-1].offset))) #SUM OVER FOR RANGE!#

		return fragments_found





















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
	













	def partition_by_windows(lst, partition_lengths = []):
	'''
	Takes in a list of data and a list of partition lengths and returns a list of lists that holds
	the original data in windows of length (partition_lengths)_i. Given that there may be a remainder 
	the final list in the output may be of a different size. 

	>>> pi1 = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
	>>> for this_partition in partition_by_windows(pi1, partition_lengths = [1, 2, 3]):
	...     print(this_partition)
	[3]
	[1, 4]
	[1, 5, 9]
	[2]
	[6, 5]
	[3, 5]

	>>> pi2 = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7]
	>>> partition_by_windows(pi2, partition_lengths = [7, 4])
	[[3, 1, 4, 1, 5, 9, 2], [6, 5, 3, 5], [8, 9, 7]]
	'''
	it = iter(lst)
	num_of_repeats = (len(lst) // sum(partition_lengths)) + 1
	new_partitions = num_of_repeats * partition_lengths
	all_slices = [s for s in (list(itertools.islice(it, 0, i)) for i in new_partitions)]

	remainder = list(it)
	if remainder:
		all_slices.append(remainder)

	for this_slice in all_slices:
		if len(this_slice) == 0:
			all_slices.remove(this_slice)

	return all_slices















	################################## REPRESENTATIONS ##################################
def _ratio(array, start_index):
	"""
	Given an array and a starting index, returns the ratio of the element at the provided index 
	to the element at the following one. A ZeroDivision error will only occur if it encounters a 
	difference list.

	>>> _ratio(np.array([1.0, 0.5]), 0)
	0.5
	>>> _ratio(np.array([0.25, 0.25, 0.75]), 1)
	3.0
	>>> _ratio(np.array([1.5, 1.0]), 0)
	0.66667
	"""
	if not (0 <= start_index and start_index <= len(array) - 1):
		raise IndexError('Input ``start_index`` not in appropriate range!')
	try: 
		ratio = array[start_index + 1] / array[start_index]
		return round(ratio, 5)
	except ZeroDivisionError:
		raise Exception('Something is off...')

def _difference(array, start_index):
	"""
	Returns the difference between two elements. 
	"""
	try:
		difference = array[start_index + 1] - array[start_index]
		return difference
	except IndexError:
		pass

def successive_ratio_list(lst):
	"""
	Returns an array of the successive duration ratios. By convention, we set the first value to 1.0. 
	"""
	ratio_array = [1.0] #np.array([1.0])
	i = 0
	while i < len(lst) - 1:
		ratio_array.append(_ratio(lst, i))
		i += 1

	return np.array(ratio_array)
	
def successive_difference_array(lst):
	"""
	Returns a list containing differences between successive durations. By convention, we set the 
	first value to 0.0. 
	"""
	difference_lst = [0.0]
	i = 0
	while i < len(lst) - 1:
		difference_lst.append(_difference(lst, i))
		i += 1

	return difference_lst