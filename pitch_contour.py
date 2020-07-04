# -*- coding: utf-8 -*-
####################################################################################################
# File:     pitch_contour.py
# Purpose:  Tools for analyzing pitch contour in collections of found-talas. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
NOTE:
- table as follows:
"""
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas

from music21 import chord
from music21 import converter
from music21 import note
from music21 import stream

liturgiePath = '/Users/lukepoeppel/Dropbox/Luke_Myke/Messiaen_Qt/Messiaen_I_Liturgie/Messiaen_I_Liturgie_de_cristal_CORRECTED.mxl'
introPath = '/Users/lukepoeppel/Desktop/Sept_Haikai/1_Introduction.xml'

V_Opening_Ql = [1.0, 0.5, 1.5, 1.5, 1.5, 1.0, 1.5, 0.25, 0.25, 0.25, 0.125, 0.125, 0.125, 0.125, 0.25, 0.25, 0.375, 0.75, 1.25, 1.25, 1.75, 1.25, 1.25, 1.25, 0.75]
possibleWindows = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19]
oneIteration = [1.0, 1.0, 1.0, 0.5, 0.75, 0.5, 0.5, 0.5, 0.5, 0.75, 0.75, 0.75, 0.25, 0.5, 0.75, 1.0, 2.0]
twoIterations = [1.0, 1.0, 1.0, 0.5, 0.75, 0.5, 0.5, 0.5, 0.5, 0.75, 0.75, 0.75, 0.25, 0.5, 0.75, 1.0, 2.0, 1.0, 1.0, 1.0, 0.5, 0.75, 0.5, 0.5, 0.5, 0.5, 0.75, 0.75, 0.75, 0.25, 0.5, 0.75, 1.0, 2.0]

#---------------------------------------------------------------------------------------------------
def getStrippedQlListOfStream(filePath, part):
	'''
	Returns the quarter length list of an input stream with all ties removed. That way we are able
	to extract all tâlas without the hassle of dealing with barlines.
	'''
	fullScore = converter.parse(filePath)
	part = fullScore.parts[part]
	objectList = []
	qlList = []

	for thisObj in part.recurse().iter.notes:
		objectList.append(thisObj)

	for i, thisObj in enumerate(objectList):
		if thisObj.tie is not None:
			nextObj = objectList[i + 1]
			qlList.append(thisObj.duration.quarterLength + nextObj.duration.quarterLength)
			del objectList[i + 1]
		else:
			qlList.append(thisObj.duration.quarterLength)

	return qlList

def lowestNoteOrChordOffset(streamIn):
	'''
	Returns the offset of the first note or chord in the stream, ignoring rests.
	Question for Cuthbert: Can I speed this up?
	'''
	for this in streamIn.recurse().iter.notes:
		try:
			if this.isNote:
				return this.offset
				break
			elif this.isChord:
				return this.offset
				break
		except AttributeError:
			break

#-------------------------------------------------------------------------------
#PITCH CONTOUR
def removePitchesBelow(chordIn):
	'''
	Removes all pitches below the highest note of an input chord.

	>>> c = chord.Chord(['D4', 'F#4', 'A4'])
	>>> removePitchesBelow(c)
	<music21.chord.Chord A4>
	'''
	newChord = chord.Chord()
	asPs = []
	for thisPitch in chordIn.pitches:
		asPs.append(thisPitch.ps)

	newChord.add(note.Note(max(asPs)))
	return newChord

def removePitchesAbove(chordIn):
	'''
	NOT USED
	Removes all pitches above the lowest note of an input chord.
	'''
	newChord = chord.Chord()
	asPs = []
	for thisPitch in chordIn.pitches:
		asPs.append(thisPitch.ps)

	newChord.add(note.Note(min(asPs)))
	return newChord

def returnHighestMelody(streamIn):
	'''
	Given a stream of chords (and notes), returnHighestMelody returns a stream with identical 
	rhythm, but with only the highest notes of each chord present. Thus a stream of chords gets
	reduced to a stream of notes. 
	'''
	for thisObj in streamIn.recurse().notesAndRests:
		try:
			if thisObj.isChord:
				highestPitch = thisObj.pitches[0]
				for thisPitch in thisObj.pitches:
					if thisPitch.ps > highestPitch.ps:
						highestPitch = thisPitch

				for thisPitch in thisObj.pitches:
					if thisPitch == highestPitch:
						pass
					else:
						thisObj.remove(thisPitch)
		except AttributeError:
			pass

	return streamIn

def returnLowestMelody(streamIn):
	'''
	Same as returnHighestMelody, but with opposite operation.
	'''
	for thisObj in streamIn.recurse().notesAndRests:
		try:
			if thisObj.isChord:
				highestPitch = thisObj.pitches[0]
				for thisPitch in thisObj.pitches:
					if thisPitch.ps < highestPitch.ps:
						highestPitch = thisPitch

				for thisPitch in thisObj.pitches:
					if thisPitch == highestPitch:
						pass
					else:
						thisObj.remove(thisPitch)
		except AttributeError:
			pass

	return streamIn

def flattenOneNoteChordToNoteObj(chordIn):
	'''
	Given a chord with a single note, flattens it to a note object.
	'''
	if type(chordIn) == note.Note:
		return chordIn
	if len(chordIn.pitches) > 1:
		return
	else:
		newNote = note.Note(chordIn.pitches[0].ps)
		return newNote

def normalizeStreamsToStartingPitchClass(streamIn, pitchClass):
	'''
	Given an input stream, this function normalizes it to a starting frequency. 
	For now, only functions on streams without chords. 
	'''
	reduced = returnHighestMelody(streamIn)
	minOffset = lowestNoteOrChordOffset(reduced)
	difference = 0.0

	for thisObj in reduced.recurse().iter.getElementsByOffset(minOffset).notes:
		x = flattenOneNoteChordToNoteObj(thisObj)
		if x.pitch.ps == pitchClass:
				print("EQ")
		else:
			xPitch = x.pitch.ps
			difference = pitchClass - xPitch

	d = reduced.flat.transpose(difference)
	return d

#---------------------------------------------------------------------------------------------------
intro = converter.parse(introPath)
bois = intro.parts[0]
s = converter.parse(liturgiePath)
p1 = s.parts[3]
p2 = s.parts[1]

raga_1 = stream.Stream()
raga_2 = stream.Stream()
raga_3 = stream.Stream()
raga_4 = stream.Stream()
raga_5 = stream.Stream()
raga_6 = stream.Stream()
raga_7 = stream.Stream()
raga_8 = stream.Stream()
raga_9 = stream.Stream()
raga_10 = stream.Stream()

sopranofied = returnHighestMelody(p1)

for thisThing in sopranofied.recurse().iter.getElementsByOffset(2.0, 6.25).notes:
	raga_1.append(thisThing)
for thisThing in sopranofied.recurse().iter.getElementsByOffset(15.0, 19.25).notes:
	raga_2.append(thisThing)
for thisThing in sopranofied.recurse().iter.getElementsByOffset(28.0, 32.25).notes:
	raga_3.append(thisThing)
for thisThing in sopranofied.recurse().iter.getElementsByOffset(41.0, 45.25).notes:
	raga_4.append(thisThing)
for thisThing in sopranofied.recurse().iter.getElementsByOffset(54.0, 58.25).notes:
	raga_5.append(thisThing)
for thisThing in sopranofied.recurse().iter.getElementsByOffset(67.0, 71.25).notes:
	raga_6.append(thisThing)
for thisThing in sopranofied.recurse().iter.getElementsByOffset(80.0, 84.25).notes:
	raga_7.append(thisThing)
for thisThing in sopranofied.recurse().iter.getElementsByOffset(93.0, 97.25).notes:
	raga_8.append(thisThing)
for thisThing in sopranofied.recurse().iter.getElementsByOffset(106.0, 110.25).notes:
	raga_9.append(thisThing)
for thisThing in sopranofied.recurse().iter.getElementsByOffset(119.0, 123.25).notes:
	raga_10.append(thisThing)

ragas = [raga_1]

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

	x, y = data.T
	#plt.plot(x, y, 'o-')
	#plt.show()

graphPitchContour()