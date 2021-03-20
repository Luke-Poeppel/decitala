import os

from decitala import search, hash_table, utils
from decitala.fragment import GreekFoot

# here = os.path.abspath(os.path.dirname(__file__))
# filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml"

om_ex_34 = "/Users/lukepoeppel/Messiaen/Oiseaux_De_Nouvelle_Calédonie/2_LOiseau_Moine/XML/LOiseau_Moine_Ex34.xml"
# object_list = utils.get_object_indices(filepath=om_ex_34, part_num=0)
# for this_window in utils.roll_window(object_list, 2):
# 	print(this_window, utils.frame_is_spanned_by_slur(this_window))

# # so spanners *are* being found -> the issue is not in frame_is_spanned_by_slur. 
# #for this_window in utils.roll_window(object_list, 2):
# #	print(this_window, utils.frame_is_spanned_by_slur(this_window))

fragments = search.rolling_hash_search(
	filepath=om_ex_34,
	part_num=0,
	table=hash_table.GreekFootHashTable()
)
# print(fragments)
for x in fragments:
	print(x["is_spanned_by_slur"])


# path = search.path_finder(
# 	filepath=om_ex_34,
# 	part_num=0,
# 	frag_type="greek_foot",
# 	slur_constraint=False
# )
# for x in path:
# 	print(x)




# def test_shuffled_I_path():
# 	# path = search.path_finder(
# 	# 	filepath = filepath,
# 	# 	part_num=0,
# 	# 	frag_type="greek_foot",
# 	# 	slur_constraint=False
# 	# )

# 	object_list = utils.get_object_indices(filepath=filepath, part_num=0)
# 	for this_object in object_list:
# 		print(this_object[0].getSpannerSites())

# 	# fragments = search.rolling_hash_search(
# 	# 	filepath=os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml",
# 	# 	part_num=0,
# 	# 	table=hash_table.GreekFootHashTable()
# 	# )
# 	# for x in fragments:
# 	# 	print(x)

# 	# fragments = [x["fragment"] for x in path]
# 	# return fragments
# 	# analysis = [
# 	# 	GreekFoot("Peon_IV"),
# 	# 	GreekFoot("Iamb"),
# 	# 	GreekFoot("Peon_IV"),
# 	# 	GreekFoot("Peon_IV")
# 	# ]

# print(test_shuffled_I_path())