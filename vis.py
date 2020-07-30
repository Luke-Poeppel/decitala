# -*- coding: utf-8 -*-
####################################################################################################
# File:     vis.py
# Purpose:  Histogram and roll visualization for talas found in a particular piece. Either 
#           path-dependant or net find. 
#
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
TODO:
- sideways sorted histogram with the full_id and ql_array().

NOTE:
- Want: some basic demographic information for the Fragment info for both Sept Haikai and Liturgie.
	- paths.py gives us access to the path information, but we also need access to the fragment information...
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from collections import Counter

from decitala import Decitala
from paths import (
	SubPath, 
	Path,
	get_full_model3_path
)

FONTNAME = 'Times'
FONTSIZE_TITLE = 15
FONTSIZE_LABEL = 14

#databases
haikai0_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_0.db'
haikai1_database_path = '/Users/lukepoeppel/decitala_v2/sept_haikai_1.db'

liturgie3_database_path = '/Users/lukepoeppel/decitala_v2/liturgie_3.db'
liturgie4_database_path = '/Users/lukepoeppel/decitala_v2/liturgie_4.db'

livre_dorgue_0_path = '/Users/lukepoeppel/decitala_v2/livre_dorgue_0.db'
livre_dorgue_1_path = '/Users/lukepoeppel/decitala_v2/livre_dorgue_1.db'

####################################################################################################
# Visualization

def tala_counter(data, title, filename):
	"""
	Returns a histogram of the talas found in a path 
	"""
	mpl.style.use('seaborn')

	if isinstance(data, SubPath) or isinstance(data, Path):
		pass
	else:
		raise Exception('Invalid input; must be SubPath or Path.')

	talas = data.decitalas
	c = Counter(talas)
	sorted_c = sorted(c.items(), key = lambda x: x[1], reverse=False)

	#reduce to 12 characters
	names = [x[0].name if (len(x[0].name) <= 12) else ((x[0].name)[0:12] + '.') for x in sorted_c]
	counts = [x[1] for x in sorted_c]

	max_count = counts[-1]
	
	plt.figure(figsize=(11, 3))

	plt.xticks(list(range(0, max_count + 1, 1)))

	plt.subplots_adjust(bottom=0.17, top=0.81)
	plt.title(title, fontname=FONTNAME, fontsize=FONTSIZE_TITLE)
	plt.xlabel('Count (n)', fontname=FONTNAME, fontsize=12)
	plt.ylabel('Deçitâla Name', fontname=FONTNAME, fontsize=12)

	plt.barh(names, counts, height=0.8)
	plt.show()
	#plt.savefig(filename, dpi=800)#, format='eps')
	#plt.close()
	
def tala_roll(subpath):
	mpl.style.use('seaborn')
	plt.plot([1, 2, 3], [4, 5, 6])

	plt.show()

####################################################################################################
# Testing

sb = SubPath(livre_dorgue_0_path, 10, 5)
tala_counter(sb, title="Livre d'Orgue Example Subpath")

#print(type('a'))
#print(type(sb))

#subpaths = get_full_model3_path(livre_dorgue_1_path)
#full_path = Path(subpaths)

#tala_counter(haikai1_full_path, "$Sept \: Haïkaï \: Reduction$ \n (Part 0)")
#tala_counter(full_path, "$Livre \: d'Orgue \: V$ \n (Part 1)", "livre_dorgue1_hist")


