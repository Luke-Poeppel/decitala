# def get_all_augmentations(
# 		fragment,
# 		frag_type,
# 		dict_in,
# 		factors=FACTORS,
# 		differences=DIFFERENCES,
# 		retrograde=True,
# 		allow_mixed=False,
# 		superdivision_str=None
# 	):
# 	if allow_mixed is False:
# 		for this_factor in factors:
# 			ql_array = json.loads(fragment[1])
# 			searches = [ql_array]
# 			if retrograde is True:
# 				searches.append(ql_array[::-1])
# 			for i, this_search in enumerate(searches):
# 				augmentation = tuple(augment(fragment=this_search, factor=this_factor, difference=0.0))
# 				if any(x <= 0 for x in augmentation):
# 					continue

# 				if i == 0:
# 					retrograde = False
# 				else:
# 					retrograde = True

# 				search_dict = {
# 					"fragment": fragment[0],
# 					"frag_type": frag_type,
# 					"retrograde": retrograde,
# 					"factor": this_factor,
# 					"difference": 0,
# 					"mod_hierarchy_val": 1 if retrograde is False else 2
# 				}
# 				if str(augmentation) in dict_in:
# 					existing = dict_in[str(augmentation)]
# 					if existing["mod_hierarchy_val"] < search_dict["mod_hierarchy_val"]:
# 						continue
# 					else:
# 						dict_in[str(augmentation)] = search_dict
# 				else:
# 					dict_in[str(augmentation)] = search_dict

# 		for this_difference in differences:
# 			ql_array = json.loads(fragment[1])
# 			searches = [ql_array]
# 			if retrograde is True:
# 				searches.append(ql_array[::-1])
# 			for i, this_search in enumerate(searches):
# 				augmentation = tuple(augment(fragment=this_search, factor=1.0, difference=this_difference))
# 				if any(x <= 0 for x in augmentation):
# 					continue

# 				if i == 0:
# 					retrograde = False
# 				else:
# 					retrograde = True

# 				search_dict = {
# 					"fragment": fragment[0],
# 					"frag_type": frag_type,
# 					"retrograde": retrograde,
# 					"factor": this_factor,
# 					"difference": 0,
# 					"mod_hierarchy_val": 3 if retrograde is False else 4
# 				}
# 				if str(augmentation) in dict_in:
# 					existing = dict_in[str(augmentation)]
# 					if existing["mod_hierarchy_val"] < search_dict["mod_hierarchy_val"]:
# 						continue
# 				else:
# 					dict_in[str(augmentation)] = search_dict
# 	else:
# 		raise Exception("Mixed augmentation is not yet supported.")

# # These should inherit from the general table. 
# def DecitalaHashTable():
# 	conn = sqlite3.connect(fragment_db)
# 	cur = conn.cursor()
# 	decitala_table_string = "SELECT * FROM Decitalas"
# 	cur.execute(decitala_table_string)
# 	decitala_rows = cur.fetchall()

# 	dht = dict()
# 	for fragment in decitala_rows:
# 		get_all_augmentations(dict_in=dht, fragment=fragment, frag_type="decitala")

# 	return dht

# def GreekFootHashTable():
# 	conn = sqlite3.connect(fragment_db)
# 	cur = conn.cursor()
# 	greek_table_string = "SELECT * FROM Greek_Metrics"
# 	cur.execute(greek_table_string)
# 	greek_rows = cur.fetchall()

# 	ght = dict()
# 	for fragment in greek_rows:
# 		get_all_augmentations(dict_in=ght, fragment=fragment, frag_type="greek_foot")

# 	return ght

# def CombinedHashTable():
# 	conn = sqlite3.connect(fragment_db)
# 	cur = conn.cursor()
# 	decitala_table_string = "SELECT * FROM Decitalas"
# 	greek_table_string = "SELECT * FROM Greek_Metrics"
# 	table_strings = [decitala_table_string, greek_table_string]

# 	cht = dict()
# 	for i, this_table_string in enumerate(table_strings):
# 		cur.execute(this_table_string)
# 		rows = cur.fetchall()

# 		for fragment in rows:
# 			if i == 0:
# 				frag_type = "decitala"
# 			else:
# 				frag_type = "greek_foot"

# 			get_all_augmentations(dict_in=cht, fragment=fragment, frag_type=frag_type)

# 	return cht























# d = FragmentHashTable(
# 	datasets=["greek_foot"],
# 	custom_fragments=[GeneralFragment([3.0, 4.0, 2.0, 1.0], name="my awesome fragment")]
# )
# print(d.data())