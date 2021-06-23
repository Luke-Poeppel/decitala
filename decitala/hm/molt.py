####################################################################################################
# File:     MOLT.py
# Purpose:  Module for storing and dealing with the Modes of Limited Transposition [MOLT] (1944).
#
# Author:   Luke Poeppel
#
# Location: NYC, 2021
####################################################################################################
"""
Messiaen's Modes of Limited Transpositions.

Color translations come from
https://www.musicandpractice.org/volume-2/visualizing-visions-the-significance-of-messiaens-colours/.
by Håkon Austbø.

"I am ... affected by a kind of synopsia, found more in my mind than in
my body, which allows me, when I hear music, and equally when I read
it, to see inwardly, in the mind's eye, colors which move with the music,
and I sense these colors in an extremely vivid manner. . . ." (Samuel, 1976)
"""
import numpy as np

from music21 import converter
from music21 import scale
from music21.pitch import Pitch
from music21.note import Note

from scipy import stats, linalg

KS_MAJOR_WEIGHTS = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]) # noqa
KS_MINOR_WEIGHTS = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]) # noqa

# Good listing in Sherlaw Johnson p. 16
MOLT_DATA = {
	"MODE-1_TRANSPOSITION-1": (["C4", "D4", "E4", "F#4", "G#4", "A#4"],),
	"MODE-1_TRANSPOSITION-2": (["C#4", "D#4", "F4", "G4", "A4", "B4"],),
	#
	"MODE-2_TRANSPOSITION-1": (["C4", "C#4", "D#4", "E4", "F#4", "G4", "A4", "B-4"], ["Blue Violet"]), # noqa
	"MODE-2_TRANSPOSITION-2": (["C#4", "D4", "E4", "F4", "G4", "G#4", "A#4", "B4"], ["Gold", "Brown"]), # noqa
	"MODE-2_TRANSPOSITION-3": (["D4", "E-4", "F4", "F#4", "G#4", "A4", "B4", "C5"], ["Green"]),
	#
	"MODE-3_TRANSPOSITION-1": (["C4", "D4", "E-4", "E4", "F#4", "G4", "A-4", "B-4", "B4"], ["Orange", "Gold", "Milky white"]), # noqa
	"MODE-3_TRANSPOSITION-2": (["D-4", "E-4", "E4", "F4", "G4", "A-4", "A4", "B4", "C5"], ["Grey", "Mauve"]), # noqa
	"MODE-3_TRANSPOSITION-3": (["D4", "E4", "F4", "F#4", "G#4", "A4", "B-4", "C5", "C#5"], ["Blue", "Green"]), # noqa
	"MODE-3_TRANSPOSITION-4": (["E-4", "F4", "F#4", "G4", "A4", "B-4", "B", "C#", "D"], ["Orange", "Red", "A little blue"]), # noqa
	#
	"MODE-4_TRANSPOSITION-1": (["C4", "D-4", "D4", "F4", "F#4", "G4", "A-4", "B4"], ["Blue", "Grey", "Gold"]), # noqa
	"MODE-4_TRANSPOSITION-2": (["C#4", "D4", "E-4", "F#4", "G4", "A-4", "A4", "C5"], ["Grey", "Pink and copper yellow reflections", "Black and blue", "Green", "Purple"]), # noqa
	"MODE-4_TRANSPOSITION-3": (["D4", "E-4", "E4", "G4", "A-4", "A4", "B-4", "C#5"], ["Yellow", "Violet"]), # noqa
	"MODE-4_TRANSPOSITION-4": (["E-4", "E4", "F4", "A-4", "A4", "B-4", "B4", "D5"], ["Dark violet", "White with purple patterns"]), # noqa
	"MODE-4_TRANSPOSITION-5": (["E4", "F4", "F#4", "A4", "A#4", "B4", "C5", "D#5"], ["Intense violet with grey mauve zones"]), # noqa
	"MODE-4_TRANSPOSITION-6": (["F4", "G-4", "G4", "B-4", "B4", "C5", "D-5", "E5"], ["Carmine", "Violet purple", "Orange", "Grey mauve", "Grey pink"]), # noqa
	#
	"MODE-5_TRANSPOSITION-1": (["C4", "C#4", "F4", "F#4", "G4", "B4"],),
	"MODE-5_TRANSPOSITION-2": (["C#4", "D4", "F#4", "G4", "G#4", "C5"],),
	"MODE-5_TRANSPOSITION-3": (["D4", "D#4", "G4", "G#4", "A4", "C#5"],),
	"MODE-5_TRANSPOSITION-4": (["D#4", "E4", "G#4", "A4", "A#4", "D5"],),
	"MODE-5_TRANSPOSITION-5": (["E4", "F4", "A4", "A#4", "B4", "D#5"],),
	"MODE-5_TRANSPOSITION-6": (["F4", "F#4", "A#4", "B4", "C5", "E5"],),
	#
	"MODE-6_TRANSPOSITION-1": (["C4", "D4", "E4", "F4", "F#4", "G#4", "A#4", "B4"], ["Gold on grey background", "orange lozenges", "dark green", "golden"]), # noqa
	"MODE-6_TRANSPOSITION-2": (["D-4", "E-4", "F4", "G-4", "G4", "A4", "B4", "C5"], ["Leather chocolate", "Reddish orange", "violet", "Pale grey", "mauve"]), # noqa
	"MODE-6_TRANSPOSITION-3": (["D4", "E4", "F#4", "G4", "A-4", "B-4", "C5", "C#5"], ["Transparent sulphuric yellow", "Mauve", "Prussian blue", "Brown"]), # noqa
	"MODE-6_TRANSPOSITION-4": (["E-4", "F4", "G4", "A-4", "A4", "B4", "C#5", "D5"], ["Yellow", "Violet", "Black"]), # noqa
	"MODE-6_TRANSPOSITION-5": (["E4", "F#4", "G#4", "A4", "B-4", "C5", "D5", "D#5"], ["Gold", "Pale blue", "Violet", "Brown"]), # noqa
	"MODE-6_TRANSPOSITION-6": (["F4", "G4", "A4", "B-4", "B4", "C#5", "D#5", "E5"], ["White", "Black", "Pale blue"]), # noqa
	#
	"MODE-7_TRANSPOSITION-1": (["C4", "C#4", "D4", "D#4", "F4", "F#4", "G4", "G#4", "A4", "B4"],),
	"MODE-7_TRANSPOSITION-2": (["C#4", "D4", "D#4", "E4", "F#4", "G4", "G#4", "A4", "A#4", "C5"],),
	"MODE-7_TRANSPOSITION-3": (["D4", "D#4", "E4", "F4", "G4", "G#4", "A4", "A#4", "B4", "C#5"],),
	"MODE-7_TRANSPOSITION-4": (["D#4", "E4", "F4", "F#4", "G#4", "A4", "A#4", "B4", "C5", "D5"],),
	"MODE-7_TRANSPOSITION-5": (["E4", "F4", "F#4", "G4", "A4", "A#4", "B4", "C5", "C#5", "D#5"],),
	"MODE-7_TRANSPOSITION-6": (["F4", "F#4", "G4", "G#4", "A#4", "B4", "C5", "C#5", "D5", "E5"],)
}

def get_all_coefficients(exclude_major_minor=False, molt_tonic_val=1):
	MOLT_COEFFS = {
		"M1T1": MOLT(mode=1, transposition=1).pc_vector(tonic_value=molt_tonic_val),
		"M1T2": MOLT(mode=1, transposition=2).pc_vector(tonic_value=molt_tonic_val),
		#
		"M2T1": MOLT(mode=2, transposition=1).pc_vector(tonic_value=molt_tonic_val),
		"M2T2": MOLT(mode=2, transposition=2).pc_vector(tonic_value=molt_tonic_val),
		"M2T3": MOLT(mode=2, transposition=3).pc_vector(tonic_value=molt_tonic_val),
		#
		"M3T1": MOLT(mode=3, transposition=1).pc_vector(tonic_value=molt_tonic_val),
		"M3T2": MOLT(mode=3, transposition=2).pc_vector(tonic_value=molt_tonic_val),
		"M3T3": MOLT(mode=3, transposition=3).pc_vector(tonic_value=molt_tonic_val),
		#
		"M4T1": MOLT(mode=4, transposition=1).pc_vector(tonic_value=molt_tonic_val),
		"M4T2": MOLT(mode=4, transposition=2).pc_vector(tonic_value=molt_tonic_val),
		"M4T3": MOLT(mode=4, transposition=3).pc_vector(tonic_value=molt_tonic_val),
		"M4T4": MOLT(mode=4, transposition=4).pc_vector(tonic_value=molt_tonic_val),
		"M4T5": MOLT(mode=4, transposition=5).pc_vector(tonic_value=molt_tonic_val),
		"M4T6": MOLT(mode=4, transposition=6).pc_vector(tonic_value=molt_tonic_val),
		#
		"M5T1": MOLT(mode=5, transposition=1).pc_vector(tonic_value=molt_tonic_val),
		"M5T2": MOLT(mode=5, transposition=2).pc_vector(tonic_value=molt_tonic_val),
		"M5T3": MOLT(mode=5, transposition=3).pc_vector(tonic_value=molt_tonic_val),
		"M5T4": MOLT(mode=5, transposition=4).pc_vector(tonic_value=molt_tonic_val),
		"M5T5": MOLT(mode=5, transposition=5).pc_vector(tonic_value=molt_tonic_val),
		"M5T6": MOLT(mode=5, transposition=6).pc_vector(tonic_value=molt_tonic_val),
		#
		"M6T1": MOLT(mode=6, transposition=1).pc_vector(tonic_value=molt_tonic_val),
		"M6T2": MOLT(mode=6, transposition=2).pc_vector(tonic_value=molt_tonic_val),
		"M6T3": MOLT(mode=6, transposition=3).pc_vector(tonic_value=molt_tonic_val),
		"M6T4": MOLT(mode=6, transposition=4).pc_vector(tonic_value=molt_tonic_val),
		"M6T5": MOLT(mode=6, transposition=5).pc_vector(tonic_value=molt_tonic_val),
		"M6T6": MOLT(mode=6, transposition=6).pc_vector(tonic_value=molt_tonic_val),
		#
		"M7T1": MOLT(mode=7, transposition=1).pc_vector(tonic_value=molt_tonic_val),
		"M7T2": MOLT(mode=7, transposition=2).pc_vector(tonic_value=molt_tonic_val),
		"M7T3": MOLT(mode=7, transposition=3).pc_vector(tonic_value=molt_tonic_val),
		"M7T4": MOLT(mode=7, transposition=4).pc_vector(tonic_value=molt_tonic_val),
		"M7T5": MOLT(mode=7, transposition=5).pc_vector(tonic_value=molt_tonic_val),
		"M7T6": MOLT(mode=7, transposition=6).pc_vector(tonic_value=molt_tonic_val),
	}
	if not(exclude_major_minor):
		return MOLT_COEFFS | {
			"Major": [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88],
			"Minor": [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17],
		}
	else:
		return MOLT_COEFFS

class MOLT:
	"""
	Simple class representing the modes of limited transposition (Messiaen, 1944),
	therefore called a MOLT.

	TODO: could also make the repr à la Bernard (1986) –– 3(2) = Mode 3/Transposition 2.

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
	Traceback (most recent call last):
	Exception: Colors only provided for modes 2, 3, 4, and 6.
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
		Return a MOLT object from string input of the form MXTB
		"""
		return MOLT(mode=str_in[1], transposition=str_in[3])

	@property
	def scale(self):
		pitches = MOLT_DATA[f"MODE-{self.mode}_TRANSPOSITION-{self.transposition}"][0]
		return scale.ConcreteScale(pitches=pitches)

	# Override scale.pitches attribute to remove octave duplication.
	@property
	def pitches(self):
		return self.scale.pitches[:-1]

	@property
	def color(self):
		if self.mode in {1, 5, 7}:
			raise Exception("Colors only provided for modes 2, 3, 4, and 6.")
		return MOLT_DATA[f"MODE-{self.mode}_TRANSPOSITION-{self.transposition}"][1]

	@property
	def is_color_mode(self):
		return self.mode in {2, 3, 4, 6}

	def pitch_names(self):
		return [x.name for x in self.pitches]

	def pc_dict(self, tonic_value=None):
		pc_dict = {x: 0 for x in range(0, 12)}
		for p in self.pitches:
			if p == self.scale.tonic and tonic_value is not None:
				pc_dict[p.pitchClass] = tonic_value
			else:
				pc_dict[p.pitchClass] = 1
		return pc_dict

	def pc_vector(self, tonic_value=None):
		return pc_dict_to_vector(self.pc_dict(tonic_value=tonic_value))

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
	for key, val in MOLT_DATA.items():
		pcs = set()
		for this_pitch in val[0]:
			pcs.add(Pitch(this_pitch).pitchClass)

		if query_collection.issubset(pcs):
			split = key.split("_")
			mode = split[0][-1]
			transposition = split[1][-1]
			res.append(MOLT(mode=mode, transposition=transposition))

	return res

####################################################################################################
# Tools
def pc_counter(filepath, part_num, normalize_over_duration=False):
	"""
	Returns a dictionary holding the pitch classes in the keys and the count (or count normalized
	over duration) in the given filepath-part_num combination.

	IDK if this is totally right –– counts all QLs, even over chords.
	"""
	pitch_classes = {x: [] for x in range(0, 12)}
	converted = converter.parse(filepath)
	net = 0
	for tone in converted.parts[part_num].stripTies().flat.iter.notes:
		try:
			if tone.isChord:
				for i, x in enumerate(tone.pitches):
					pitch_classes[x.pitchClass].append(tone.quarterLength)
					net += tone.quarterLength
			else:
				pitch_classes[tone.pitch.pitchClass].append(tone.quarterLength)
				net += tone.quarterLength
		except AttributeError:
			continue

	if normalize_over_duration:
		normalized_dict = {x: sum(y) / net for x, y in pitch_classes.items()}
		assert round(sum(normalized_dict.values())) == 1
		return normalized_dict
	else:
		return {x: len(y) for x, y in pitch_classes.items()}

def pc_dict_to_vector(dict_in):
	"""
	Function for converting a pitch class dictionary (i.e. a dictionary with keys in range 0-11 and
	values some integer) to a vector of the associated values; sorted by the key, naturally.

	>>> m3t3 = MOLT(mode=3, transposition=3)
	>>> dict_in = m3t3.pc_dict()
	>>> dict_in
	{0: 1, 1: 1, 2: 1, 3: 0, 4: 1, 5: 1, 6: 1, 7: 0, 8: 1, 9: 1, 10: 1, 11: 0}
	>>> pc_dict_to_vector(dict_in)
	array([1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0])
	"""
	return np.array([dict_in[key] for key, val in sorted(dict_in.items(), key=lambda x: x[0])])

def diatonic_scale_binary(tonic, mode, as_vector=False):
	"""
	Function for creating a binary dict (or ordered vector if ``as_vector=True``) of a major or
	minor scale (set ``mode``) of a given ``diatonic``.
	"""
	pitch_classes = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0}
	if mode.lower() == "Major":
		res_scale = scale.MajorScale(tonic)
	elif mode.lower() == "Minor":
		res_scale = scale.MinorScale(tonic)
	else:
		raise Exception("{} is not a valid mode.".format(mode))

	res_scale_pitches = [x.pitchClass for x in res_scale.pitches][:-1]
	for pc in res_scale_pitches:
		pitch_classes[pc] = 1

	if not(as_vector):
		return pitch_classes
	else:
		return pc_dict_to_vector(pitch_classes)

def note_counter(filepath, part_num):
	"""
	Simple tool for counting the number of notes (with ties stripped) in a given filepath/part
	combination.
	"""
	converted = converter.parse(filepath)
	count = 0
	for tone in converted.parts[part_num].stripTies().flat.iter.notes:
		count += 1
	return count

def KS(pc_vector, coefficients, return_p_value=False):
	input_zscores = stats.zscore(pc_vector)

	coefficients = coefficients / np.linalg.norm(coefficients)
	score = stats.spearmanr(input_zscores, coefficients)
	if return_p_value:
		return score
	else:
		return score[0]

def KS_diatonic(pc_vector, coefficients, return_tonic=False):
	"""
	Needs to circulate over all major/minor keys.
	"""
	input_zscores = stats.zscore(pc_vector)

	coefficients = coefficients / np.linalg.norm(coefficients)
	coefficients = linalg.circulant(coefficients)

	scores = [
		stats.pearsonr(x=input_zscores, y=coefficient_collection)[0]
		for coefficient_collection in coefficients
	]
	max_correlation = max(scores)
	max_correlation_index = scores.index(max_correlation)
	max_correlation_pitch = Pitch(max_correlation_index).name

	if return_tonic:
		return max_correlation_pitch, max_correlation
	else:
		return max_correlation

def test_all_coefficients(vector, exclude_major_minor=False, molt_tonic_val=1):
	res = dict()
	for key, coefficients in get_all_coefficients(
			exclude_major_minor=exclude_major_minor,
			molt_tonic_val=molt_tonic_val
		).items():
		if key in {"Major", "Minor"}:
			res[key] = KS_diatonic(vector, coefficients)
		else:
			res[key] = KS(vector, coefficients, return_p_value=True)

	return res