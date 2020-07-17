'''
print(t.get_by_ql_list([1.0, 1.0, 1.0, 0.5, 1.5, 1.0, 1.5])) #Simhavikrama
print(t.get_by_ql_list([1.5, 1.0, 1.5, 0.5, 1.0, 1.0, 1.0], try_all_methods = True)) #Simhavikrama retrograde
print(t.get_by_ql_list([0.5, 1.0, 1.0, 1.5, 1.0, 1.0, 1.0, 0.5])) #Niccanka 
print(t.get_by_ql_list([0.5, 1.0, 1.0, 1.0, 1.5, 1.0, 1.0, 0.5])) #Niccanka 
print(t.get_by_ql_list([1.5, 1.0, 1.5])) #Vijaya 
print(t.get_by_ql_list([1.0, 0.25, 0.25, 0.375])) #Gajajhampa
print(t.get_by_ql_list([0.375, 0.25, 0.25, 1.0], try_all_methods = True)) #Gajajhampa retrograde
print(t.get_by_ql_list([0.125, 0.125, 0.125, 0.125, 0.25, 0.25, 0.375])) #Bhagna
print(t.get_by_ql_list([0.375, 0.375, 0.5, 0.5], try_all_methods = True)) #Sama retrograde
print(t.get_by_ql_list([1.0, 1.0, 1.0, 0.5, 0.75, 0.5])) #varied ragavardhana
print(t.get_by_ql_list([0.5, 0.5, 1.0, 1.0])) #Kudukka
print(t.get_by_ql_list([0.5, 1.0, 0.25, 0.25])) #Rajavidyadhara
print(t.get_by_ql_list([0.25, 0.25, 1.0, 0.5])) #Rajavidyadhara retrograde
print(t.get_by_ql_list([0.5, 0.5, 1.0])) #Dvitiya
print(t.get_by_ql_list([0.125, 0.125, 0.125, 0.125, 0.25, 0.25, 0.375]))
print(t.get_by_ql_list([1.0, 0.5, 1.5, 1.5, 1.5, 1.0, 1.5, 0.25, 0.25, 0.25]))
print(t.get_by_ql_list([1.0, 0.5, 0.375, 0.25])) #laks

print(t.get_by_ql_list([0.75, 1.25, 1.25, 1.75, 1.25, 1.25, 1.25, 0.75]))
for x in t.search_with_added_values_removed([1.0, 0.25, 1.0, 0.25, 1.0, 0.5, 0.75, 0.5]):
	print(x)
'''

#t.partitionSearch(filePath = liturgiePath, pathToWrite = path_to_data, part = 3, partitions = [6, 7, 4], showScore = True)

#print(f.search_with_added_values_removed([1.0, 0.25, 1.0, 0.25, 1.0, 0.5, 0.75, 0.5]))
'''
print(f.getByQlList([1.0, 1.0, 1.0, 0.5, 1.5, 1.0, 1.5])) #Simhavikrama
print(f.getByQlList([1.5, 1.0, 1.5, 0.5, 1.0, 1.0, 1.0], tryAllMethods = True)) #Simhavikrama retrograde
print(f.getByQlList([0.5, 1.0, 1.0, 1.5, 1.0, 1.0, 1.0, 0.5])) #Niccanka 
print(f.getByQlList([0.5, 1.0, 1.0, 1.0, 1.5, 1.0, 1.0, 0.5])) #Niccanka 
print(f.getByQlList([1.5, 1.0, 1.5])) #Vijaya 
print(f.getByQlList([1.0, 0.25, 0.25, 0.375])) #Gajajhampa
print(f.getByQlList([0.375, 0.25, 0.25, 1.0], tryAllMethods = True)) #Gajajhampa retrograde
print(f.getByQlList([0.125, 0.125, 0.125, 0.125, 0.25, 0.25, 0.375])) #Bhagna
print(f.getByQlList([0.375, 0.375, 0.5, 0.5], tryAllMethods = True)) #Sama retrograde
print(f.getByQlList([1.0, 1.0, 1.0, 0.5, 0.75, 0.5])) #varied ragavardhana
print(f.getByQlList([0.5, 0.5, 1.0, 1.0])) #Kudukka
print(f.getByQlList([0.5, 1.0, 0.25, 0.25])) #Rajavidyadhara
print(f.getByQlList([0.25, 0.25, 1.0, 0.5])) #Rajavidyadhara retrograde
print(f.getByQlList([0.5, 0.5, 1.0])) #Dvitiya
print(f.getByQlList([0.125, 0.125, 0.125, 0.125, 0.25, 0.25, 0.375]))
print(f.getByQlList([1.0, 0.5, 1.5, 1.5, 1.5, 1.0, 1.5, 0.25, 0.25, 0.25]))
print(f.getByQlList([0.75, 1.25, 1.25, 1.75, 1.25, 1.25, 1.25, 0.75]))

#objects = f.get_indices_of_object_occurrence(file_path = liturgiePath, part_num = 3)
#print([x.quarterLength for x, y in objects])

good = []
i = 0
for thisTala in f.rolling_search(path = sept_haikai, part_num = 0):
	good.append(thisTala)

new = [y for x, y in good]
new.sort()

#for this in getAllEndOverlappingIndices(lst = new, i = 0, out = []):
	#print(this)

for thisTala in f.filteredData:
	print(thisTala.qlList())
	print(getAddedValues(qlList = thisTala.qlList()))
	print('')

Figure this out soon! If the fragment starts with 1.0... what do you do...? This may become a 
problem. Possible temporary solution: if first value is 1.0, try running the qlList itself without 
conversion, then try with conversion. 

print(successiveRatioList([1.0, 0.25, 1.5]))

#indices = [(0.0, 2.0), (0.0, 4.0), (2.5, 4.5), (2.0, 5.75), (2.0, 4.0), (6.0, 7.25), (4.0, 5.5)]
#indices = [(0.0, 2.0), (0.0, 4.0), (2.5, 4.5), (2.0, 5.75), (2.0, 4.0), (6.0, 7.25), (4.0, 5.5), \
#(8.0, 9.5), (9.5, 10.75), (9.75, 10.0)]

indices_pre = f.get_indices_of_object_occurrence(file_path = sept_haikai, part_num = 0)
indices = [y for x, y in indices_pre]
print(indices)
print(len(indices_pre))
indices = [y for x, y in indices_pre]
indices.sort()
print(len(indices))

#for this in f._getStrippedObjectList(f = liturgiePath, p = 3):
	#print(this)

print(f.get_indices_of_object_occurrence(file_path = liturgiePath, part_num = 3))

Things to consider: 
- number of talas
- complexity of the talas 
- distance between the occurrences

You can use the bisect method to insert options inPlace. 
#f.rolling_search(path = sept_haikai, part_num = 0)

print(f.rolling_search(path = subtilite, part_num = 0))

for i in range(2):
	print(i)
	f.rolling_search(path = sept_haikai, part_num = i)
	print('------------------------------------------------')

print(f._getStrippedQlListOfStream(filePath = sept_haikai, part = 0))

This is a great test case, because it has an added value inherant to the rhythm! 
print(f.search_with_added_values_removed([1.0, 1.0, 0.25, 1.0, 0.5, 0.75, 0.5]))
print(f.getByQlList(qlList = [4.0, 1.0, 6.0], tryAllMethods = False))
print(f.getByQlList(qlList = successiveRatioList([4.0, 1.0, 6.0])))

Talas from Sept Haikai
1.) [1.5, 1.0, 1.5] = 'Vijaya Retrograde'
2.) [0.375, 0.375 ,0.5, 0.5] = 'Sama Retrograde'
3.) [1.5, 1.0, 1.5, 0.5, 1.0, 1.0, 1.0] = 'Simhavikrama Retrograde'
4.) [0.375, 0.25, 0.25, 1.0] = 'Gajajampa Retrograde'
5.) [0.5, 1.5, 1.5, 1.5, 1.0, 1.0, 1.0] = Candrakala Retrograde 
6.) [1.0, 0.5, 0.375, 0.25] = Laksmica Retrograde
'''