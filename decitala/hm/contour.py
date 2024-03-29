####################################################################################################
# File:     contour.py
# Purpose:  Pitch contour tools for the birdsong transcriptions.
#
# Author:   Luke Poeppel
#
# Location: Kent, 2021
####################################################################################################
from .schultz import spc
from .contour_utils import (
	_track_extrema,
	_recheck_extrema,
	_pitch_contour,
	_adjacency_and_intervening_checks
)

NEUMES = {
	(1, 0): "Clivis",
	(0, 1): "Podatus",
	(0, 1, 2): "Scandicus",
	(2, 1, 0): "Climacus",
	(0, 1, 0): "Torculus",
	(1, 0, 1): "Porrectus"
}

# Morris's Prime Contour Classes (1993, 220-221)
# "Linear Prime Classes" (Schultz 92)
# NOTE: Schultz uses the same linear prime classes to refer to symmetries
# of these classes: e.g. <0 2 1> and <1 0 2> = L.
PRIME_CONTOUR_CLASSES = {
	(0,): "A",
	(0, 0): "B",
	(0, 1): "D",
	(0, 1, 0): "G",
	(0, 2, 1): "L",
	(1, 0, 2, 1): "P",
	(1, 0, 3, 2): "X",
	(1, 3, 0, 2): "Y",
	(1, 0, 2, 0, 1): "12a",
	(1, 0, 3, 0, 2): "12b"
}

class ContourException(Exception):
	pass

def strip_monotonic_pitch_content(pitch_content):
	"""
	The pitch content extracted in the :obj:`decitala.search` module consists of lists of tuples.
	This functions strips monotonic pitch content to a single list. If non-monotonic pitch content
	is provided, the function chooses the lowest pitch.

	:param list pitch_content: pitch content of the format returned in
							:obj:`decitala.search.rolling_hash_search`.
	:return: a list of MIDI tones.
	:rtype: list

	>>> pitch_content = [(60,), (61,), (65,)]
	>>> strip_monotonic_pitch_content(pitch_content)
	[60, 61, 65]
	"""
	return [x[0] for x in pitch_content]

def normalize_pitch_content(data, midi_start=60):
	"""
	Normalizes a list of MIDI tones to a a starting value.

	:param list data: a list of MIDI tones.
	:param int midi_start: the MIDI starting point to which the data are normalized.
	:return: a numpy array of the pitch content, normalized to the starting value.
	:rtype: numpy.array

	>>> normalize_pitch_content(data=[58, 60, 62], midi_start=60)
	[60, 62, 64]
	"""
	diff = data[0] - midi_start
	return [x - diff for x in data]

def uds_contour(data):
	"""
	Returns the for "up-down-stay" contour (UDS) of a given list of MIDI tones. Normalized
	to start at 0.

	:param list data: a list of MIDI tones.
	:return: a numpy array of the UDS contour of the given data.
	:rtype: numpy.array

	>>> midis = [47, 42, 45, 51, 51, 61, 58]
	>>> uds_contour(midis)
	[0, -1, 1, 1, 0, 1, -1]
	"""
	out = [0]
	i = 1
	while i < len(data):
		prev = data[i - 1]
		curr = data[i]

		if curr > prev:
			out.append(1)
		elif curr < prev:
			out.append(-1)
		elif curr == prev:
			out.append(0)

		i += 1

	return out

def pitch_contour(pitch_content, as_str=False):
	"""
	This function returns the contour of given pitch content. It accepts either a list of MIDI
	tones, or the data returned in the :obj:`decitala.search` module. Like
	:obj:`decitala.hm.contour.strip_monotonic_pitch_content`, if non-monotonic pitch content is
	provided, it chooses the lowest pitch.

	:param list pitch_content: pitch content from the output of rolling_search."
	:param bool as_str: whether to return the pitch content as a string (standard format),
						like ``"<0 1 1>"``.
	:return: the contour of the given ``pitch_content``.
	:rtype: numpy.array or str

	>>> pitch_content_1 = [(80,), (91,), (78,), (85,)]
	>>> pitch_contour(pitch_content_1)
	[1, 3, 0, 2]
	>>> pitch_content_2 = [80, 84, 84]
	>>> pitch_contour(pitch_content_2, as_str=True)
	'<0 1 1>'
	"""
	return _pitch_contour(pitch_content=pitch_content, as_str=as_str)

def contour_to_neume(contour):
	"""
	Oversimplified function for checking the associated neume of a given pitch contour. Only two and
	three onset contours are supported.

	:param contour: A pitch contour (iterable).
	:return: The associated neume or ``None``.
	:rtype: str or None

	>>> contour = [1, 0, 1]
	>>> contour_to_neume(contour)
	'Porrectus'
	"""
	assert len(contour) <= 3, ContourException("Contour input must be of length three.")
	try:
		return NEUMES[tuple(contour)]
	except KeyError:
		raise ContourException(f"The contour {contour} was not found in the given current set.")

def contour_class(
		contour,
		allow_symmetries=False
	):
	"""
	Returns the associated pitch contour class (a letter) from Morris (1993, 220-221)
	of a contour.

	:param contour: a pitch contour (iterable).
	:param bool allow_symmetries: whether to allow permutations of the given contour to be found.
									Default is ``False``. Note that ``X`` and ``Y`` are weird cases
									for this symmetry. May currently fail (don't understand it).
	:rtype: str

	>>> contour_class((1, 0, 3, 2))
	'X'
	>>> contour_class((0, 1, 0), allow_symmetries=False)
	'G'
	>>> contour_class((0, 0, 1), allow_symmetries=True)
	'G'
	"""
	try:
		if not(allow_symmetries):
			return PRIME_CONTOUR_CLASSES[contour]
		elif contour in {(1, 0, 3, 2), (1, 3, 0, 2)}:  # IDK about this case.
			return PRIME_CONTOUR_CLASSES[contour]
		else:
			match = None
			for key in PRIME_CONTOUR_CLASSES.keys():
				if len(key) == len(contour) and len(set(key)) == len(set(contour)):
					match = PRIME_CONTOUR_CLASSES[key]
					break
			return match
	except KeyError:
		ContourException(f"The contour {contour} is not prime.")

####################################################################################################
# Contour reduction tools.
# Implementation of Morris contour reduction algorithm (1993).
def _morris_reduce(contour, depth):
	"""
	Steps 4-7 of the contour reduction algorithm.
	"""
	contour = [x for x in contour if x[1]]  # Step 4
	depth += 1  # Step 5

	# Step 6. Flag maxima and *delete* repetitions.
	_recheck_extrema(contour=contour, mode="max")
	_adjacency_and_intervening_checks(contour, mode="max", algorithm="morris")

	# Step 7. Flag minima and *delete* repetitions.
	_recheck_extrema(contour=contour, mode="min")
	_adjacency_and_intervening_checks(contour, mode="min", algorithm="morris")

	return contour, depth

def prime_contour(contour):
	"""
	Implementation of Robert Morris' Contour-Reduction algorithm (Morris, 1993). "The algorithm prunes
	pitches from a contour until it is reduced to a prime." (Schultz)

	:param contour: A pitch contour (iterable).
	:return: the prime contour of the given pitch contour, along with the depth of the reduction.
	:rtype: tuple

	>>> contour_a = [0, 1]
	>>> prime_contour(contour_a)
	([0, 1], 0)
	>>> contour_b = [0, 4, 3, 2, 5, 5, 1]
	>>> prime_contour(contour_b)[0]
	[0, 2, 1]
	"""
	depth = 0

	# If the segment is of length <= 2, it is prime by definition.
	if len(contour) <= 2:
		return (pitch_contour(contour), depth)

	# If all the values are extremas, it is already prime.
	prime_contour = _track_extrema(contour)
	initial_flags = [x[1] for x in prime_contour]
	if all(x for x in initial_flags):
		return (pitch_contour(contour), depth)

	still_unflagged_values = True
	while still_unflagged_values:
		prime_contour, depth = _morris_reduce(prime_contour, depth)
		if all(x[1] for x in prime_contour):  # Step 3
			still_unflagged_values = False

	# Remove flags.
	prime_contour = [x[0] for x in prime_contour]
	return (pitch_contour(prime_contour), depth)

def schultz_prime_contour(contour):
	"""
	Implementation of Schultz's (2008) modification of Morris' contour-reduction algorithm.
	See the Schultz module for the implementation. (It was complicated enough to warrent its
	own module...)

	:param contour: A pitch contour (iterable).
	:return: the Schultz Prime Contour (SPC) of the given contour, along with the depth of the
			reduction.
	:rtype: tuple

	>>> nightingale_5 = [2, 5, 3, 1, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	>>> spc(nightingale_5)
	([1, 2, 0], 3)
	"""
	return spc(contour)