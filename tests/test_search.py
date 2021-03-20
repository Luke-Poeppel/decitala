# import os

# from decitala import search, hash_table
# from decitala.fragment import GreekFoot

# here = os.path.abspath(os.path.dirname(__file__))

# def test_shuffled_I_path():
# 	# path = search.path_finder(
# 	# 	filepath = os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml",
# 	# 	part_num=0,
# 	# 	frag_type="greek_foot",
# 	# 	slur_constraint=False
# 	# )

# 	fragments = search.rolling_hash_search(
# 		filepath=os.path.dirname(here) + "/tests/static/Shuffled_Transcription_1.xml",
# 		part_num=0,
# 		table=hash_table.GreekFootHashTable()
# 	)
# 	for x in fragments:
# 		print(x)

# 	# fragments = [x["fragment"] for x in path]
# 	# return fragments
# 	# analysis = [
# 	# 	GreekFoot("Peon_IV"),
# 	# 	GreekFoot("Iamb"),
# 	# 	GreekFoot("Peon_IV"),
# 	# 	GreekFoot("Peon_IV")
# 	# ]

# print(test_shuffled_I_path())