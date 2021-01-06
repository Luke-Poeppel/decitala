# -*- coding: utf-8 -*-
####################################################################################################
# File:     model.py
# Purpose:  Extraction of the "best" path from using basic heuristics.
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
from .fragment import (
	Decitala,
	GreekFoot
)

def model_in(subpath, weights=[]):
	"""
	>>> subpath_a = [
	...		[{'fragment': Decitala("21_Tribhinna"), 'mod': ('sr', 0.25), 'onset_range': (19.5, 20.25), 'is_spanned_by_slur': False, 'pitch_content': [(76,), (78,), (70,), (68,), (74,)]}, (19.5, 20.25)], 
	... 	[{'fragment': Decitala("17_Yatilagna"), 'mod': ('rr', 0.5), 'onset_range': (20.25, 20.625), 'is_spanned_by_slur': False, 'pitch_content': [(81,), (75,)]}, (20.25, 20.625)], 
	... 	[{'fragment': Decitala("118_Rajamartanda"), 'mod': ['rr-cs', 0.5], 'onset_range': (20.625, 21.5), 'is_spanned_by_slur': False, 'pitch_content': [(69,), (64,), (73,), (73,)]}, (20.625, 21.5)]
	...	]
	>>> subpath_b = [
	...		[{'fragment': Decitala("17_Yatilagna"), 'mod': ('r', 0.5), 'onset_range': (15.25, 15.625), 'is_spanned_by_slur': False, 'pitch_content': [(76,), (78,)]}, (15.25, 15.625)], 
	... 	[{'fragment': Decitala("86_Garugi"), 'mod': ('d', 0.125), 'onset_range': (15.625, 16.25), 'is_spanned_by_slur': True, 'pitch_content': [(76,), (71,), (78,), (69,)]}, (15.625, 16.25)]
	... ]
	>>> subpath_c = [
	...		[{'fragment': Decitala("17_Yatilagna"), 'mod': ('r', 0.5), 'onset_range': (15.25, 15.625), 'is_spanned_by_slur': False, 'pitch_content': [(76,), (78,)]}, (15.25, 15.625)], 
	...		[{'fragment': Decitala("2_Dvitiya"), 'mod': ('r', 0.5), 'onset_range': (15.75, 16.25), 'is_spanned_by_slur': False, 'pitch_content': [(71,), (78,), (69,)]}, (15.75, 16.25)]
	...	]
	"""
	gaps = []
	total_range = []
	i = 0
	while i < len(subpath) - 1:
		curr_data = subpath[i][0]
		next_data= subpath[i + 1][0]
		
		gap = next_data["onset_range"][0] - curr_data["onset_range"][1]
		gaps.append(gap)
		total_range.append(curr_data["onset_range"][1] - curr_data["onset_range"][0])
		if i == len(subpath) - 2:
			total_range.append(next_data["onset_range"][1] - next_data["onset_range"][0])
		i += 1
	
	gaps = sum(gaps)
	total_range = sum(total_range)

	print(gaps)
	print(total_range)

	# if len(subpath) == 1:
	# 	percentage_gap_pre = 0
	# else:
	# 	percentage_gap_pre = (gaps / total_range) * 100
	
	# assert percentage_gap_pre > 0
	# percentage_gap = 100 - percentage_gap_pre
	# print(percentage_gap_pre)
	# print(percentage_gap)

	# return percentage_gap






def model_out(subpath_a, subpath_b):
	pass


