####################################################################################################
# File:     molt.py
# Purpose:  Module for storing and dealing with the Modes of Limited Transposition [MOLT] (1944).
#
# Author:   Luke Poeppel
#
# Location: NYC, 2021
####################################################################################################
"""
Tools for dealing with Messiaen's Modes of Limited Transpositions (MOLT).

"I am ... affected by a kind of synopsia, found more in my mind than in
my body, which allows me, when I hear music, and equally when I read
it, to see inwardly, in the mind's eye, colors which move with the music,
and I sense these colors in an extremely vivid manner. . . ." (Samuel, 1976)

Color translations come from
`Håkon Austbø <https://www.musicandpractice.org/volume-2/visualizing-visions-the-significance-of-messiaens-colours/>`_ # noqa
"""
from music21 import scale
from music21.pitch import Pitch
from music21.note import Note

from . import hm_utils

class MOLT:
	"""
	Class representing a Mode of Limited Transposition (Messiaen, 1944), therefore called a MOLT.

	>>> m1t2 = MOLT(mode=1, transposition=2)
	>>> m1t2
	<moiseaux.MOLT mode=1, transposition=2>
	>>> m1t2.mode
	1
	>>> m1t2.transposition
	2
	>>> m1t2.scale
	<music21.scale.ConcreteScale C# Concrete>
	>>> for p in m1t2.pitches:
	... 	print(p)
	C#4
	D#4
	F4
	G4
	A4
	B4
	>>> m1t2.color
	>>> m1t2.pc_dict()
	{0: 0, 1: 1, 2: 0, 3: 1, 4: 0, 5: 1, 6: 0, 7: 1, 8: 0, 9: 1, 10: 0, 11: 1}
	"""
	def __init__(self, mode, transposition):
		self.mode = mode
		self.transposition = transposition

	def __repr__(self):
		return f"<moiseaux.MOLT mode={self.mode}, transposition={self.transposition}>"

	@classmethod
	def from_str(cls, str_in):
		"""
		Return a MOLT object from string input of the form ``"MXTB"``
		"""
		return MOLT(mode=str_in[1], transposition=str_in[3])

	@property
	def scale(self):
		"""
		Returns a music21.scale object consisting of the pitches in the MOLT.
		"""
		pitches = hm_utils.MOLT_DATA[f"MODE-{self.mode}_TRANSPOSITION-{self.transposition}"][0]
		return scale.ConcreteScale(pitches=pitches)

	# Override scale.pitches attribute to remove octave duplication.
	@property
	def pitches(self):
		"""
		Returns the pitches of the MOLT. Comes from the music21.scale.pitches, but overrides
		to remove the octave duplication.
		"""
		return self.scale.pitches[:-1]

	@property
	def color(self):
		"""
		Returns the associated color of the mode, if it exists.
		"""
		if self.mode in {1, 5, 7}:
			return None
		return hm_utils.MOLT_DATA[f"MODE-{self.mode}_TRANSPOSITION-{self.transposition}"][1]

	@property
	def is_color_mode(self):
		"""
		Returns whether the mode is a color mode, i.e. MOLT 2, 3, 4, or 6.
		"""
		return self.mode in {2, 3, 4, 6}

	def pitch_names(self):
		return [x.name for x in self.pitches]

	def pc_dict(self, tonic_value=None):
		"""
		Returns a dictionary for which the keys are the standard pitch classes (0-11)
		and the values are 0/1, determined by whether that pitch belongs to the mode.

		:param float tonic_value: an optional value to store in the tonic of the scale,
									i.e., the first tone. Otherwise, all pitches of the
									scale will be set to 1 (and the others set to 0).
		:rtype: dict
		"""
		pc_dict = {x: 0 for x in range(0, 12)}
		for p in self.pitches:
			if p == self.scale.tonic and tonic_value is not None:
				pc_dict[p.pitchClass] = tonic_value
			else:
				pc_dict[p.pitchClass] = 1
		return pc_dict

	def pc_vector(self, tonic_value=None):
		"""
		Returns the :obj:`molt.MOLT.pc_dict` as a vector, ordered by the pitch class.

				:param float tonic_value: an optional value to store in the tonic of the scale,
									i.e., the first tone. Otherwise, all pitches of the
									scale will be set to 1 (and the others set to 0).
		"""
		return hm_utils.pc_dict_to_vector(self.pc_dict(tonic_value=tonic_value))

def MOLT_query(collection):
	"""
	Returns a list of the possible MOLT (objects) that contain the collection. Accepts
	either a list of midi tones, a list of strings, a list of pitch objecs,
	or a list of note objects.
	"""
	# Prepare input
	query_collection = set()
	if all(isinstance(x, int) or isinstance(x, str) for x in collection):
		for x in collection:
			query_collection.add(Pitch(x).pitchClass)
	elif all(isinstance(x, Pitch) or isinstance(x, Note) for x in collection):
		for x in collection:
			query_collection.add(x.pitchClass)

	res = []
	for key, val in hm_utils.MOLT_DATA.items():
		pcs = set()
		for this_pitch in val[0]:
			pcs.add(Pitch(this_pitch).pitchClass)

		if query_collection.issubset(pcs):
			split = key.split("_")
			mode = split[0][-1]
			transposition = split[1][-1]
			res.append(MOLT(mode=mode, transposition=transposition))

	return res