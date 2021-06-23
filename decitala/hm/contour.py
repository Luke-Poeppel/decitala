# -*- coding: utf-8 -*-
####################################################################################################
# File:     contour.py
# Purpose:  Pitch contour tools for the birdsong transcriptions.
#
# Author:   Luke Poeppel
#
# Location: Kent, 2021
####################################################################################################
import numpy as np

def strip_monotonic_pitch_content(pitch_content):
	"""
	Given monotonic pitch content output from the decitala search modules (which stores singleton
	pitch content as tuples), strips to individual elements.
	"""
	return [x[0] for x in pitch_content]

def normalize_pitch_content(data, midi_start=60):
	"""
	Normalize pitch content to starting value `midi_start`.
	"""
	diff = data[0] - midi_start
	return np.array([x - diff for x in data])

def uds_contour(data):
	"""
	Stands for "up-down-stay" as a measure of pitch contour. Normalized to start at 0.

	>>> frag = np.array([47, 42, 45, 51, 51, 61, 58])
	>>> uds_contour(frag)
	array([ 0, -1,  1,  1,  0,  1, -1])
	"""
	out = [0]
	i = 1
	while i < len(data):
		prev = data[i - 1]
		curr = data[i]

		if curr > prev:
			out.append(1)
		if curr < prev:
			out.append(-1)
		if curr == prev:
			out.append(0)

		i += 1

	return np.array(out)