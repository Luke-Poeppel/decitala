# -*- coding: utf-8 -*-
####################################################################################################
# File:     pitch_contour.py
# Purpose:  Tools for analyzing & graphing pitch contour in collections of found-talas. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
Want: given a collection of talas found (in appropriate onset locations!), calculates the pitch contour
and 

TODO:
- elegant pitch normalization functions
- elegant pitch contour function *as* a normalizer
	- find the name of the term used by Marvin
- average pitch contour
- plot by onset_num or by offset indexed at 0?  
"""
import matplotlib.pyplot as plt
import numpy as np

#-------------------------------------------------------------------------------
def graphPitchContour(streamsIn = []):
	'''
	Given a list of n streams, graphs a scatter plot with the x axis corresponding to the 
	quarter length list, and the y axis corresponding to the midi value. How to normalize? 
	Percent shift! Merci, dad!
	'''
	import matplotlib.pyplot as plt

	data = np.array([
		[0, 76],
		[1, 74],
		[2, 74],
		[3, 72],
		[3.5, 72],
		[4.25, 72],

		[0, 76],
		[1, 73],
		[2, 69],
		[3, 73],
		[3.5, 72],
		[4.25, 71],

		[0, 76],
		[1, 82],
		[2, 80],
		[3, 80],
		[3.5, 83],
		[4.25, 83],

		[0, 76],
		[1, 71],
		[2, 73],
		[3, 74],
		[3.5, 67],
		[4.25, 64],

		[0, 76],
		[1, 80],
		[2, 80],
		[3, 79],
		[3.5, 84],
		[4.25, 83],

		[0, 76],
		[1, 74],
		[2, 85],
		[3, 83],
		[3.5, 81],
		[4.25, 81],

		####
		[0, 76],
		[1, 75],
		[2, 72],
		[3, 68],
		[3.5, 72],
		[4.25, 71],

		[0, 76],
		[1, 76],
		[2, 82],
		[3, 80],
		[3.5, 80],
		[4.25, 83],

		[0, 76],
		[1, 75],
		[2, 70],
		[3, 72],
		[3.5, 73],
		[4.25, 66],

		[0, 76],
		[1, 76],
		[2, 80],
		[3, 80],
		[3.5, 79],
		[4.25, 84],
	])

	x_coords = [x[0] for x in data]
	y_coords = [x[1] for x in data]

	#x, y = data.T
	plt.plot(x_coords, y_coords, 'o-')
	plt.xlabel('Offset')
	plt.xticks(np.arange(0, 5.0, 0.5))
	#plt.xticks(range(min(x_coords), max(x_coords) +1))
	plt.show()

graphPitchContour()