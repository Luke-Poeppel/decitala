####################################################################################################
# File:     hash_table.py
# Purpose:  Hash table lookup algorithm for rhythmic search. 
# 
# Author:   Luke Poeppel
#
# Location: NYC, 2021. 
####################################################################################################
from .utils import augment

MODIFICATION_HIERARCHY = [
	"r",
	"rr",
	"d",
	"rd",
	"sr",
	"rsr"
]

def generate_all_augmentations(fragment):
	"""
	Generates all possible additive and multiplicative augmentations of a fragment. 

	:param fragment numpy.array: array defining the rhythmic fragment.

	>>> all_dvitiya_augmentations = generate_all_augmentations(fragment=[0.25, 0.25, 0.5])
	>>> for possible_augmentation in all_dvitiya_augmentations[:15]:
	...     print(possible_augmentation)
	[0.125 0.125 0.25 ]
	[0.375 0.375 0.5  ]
	[0.625 0.625 0.75 ]
	[0.875 0.875 1.   ]
	[0.1875 0.1875 0.375 ]
	[0.4375 0.4375 0.625 ]
	[0.6875 0.6875 0.875 ]
	[0.9375 0.9375 1.125 ]
	[0.25 0.25 0.5 ]
	[0.5  0.5  0.75]
	[0.75 0.75 1.  ]
	[1.   1.   1.25]
	[0.0625 0.0625 0.375 ]
	[0.3125 0.3125 0.625 ]
	[0.5625 0.5625 0.875 ]
	"""
	factors = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
	differences = [-0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75]
	all_augmentations = []
	for this_factor in factors:
		for this_difference in differences:
			augmentation = augment(fragment=fragment, factor=this_factor, difference=this_difference)
			if all(x > 0 for x in augmentation):
				all_augmentations.append(augmentation)

	return np.vstack(all_augmentations)

@dataclass
class DecitalaHashTable:
	def __init__(self, allowed_modifications):
		pass

@dataclass
class GreekFootHashTable:
	def __init__(self, allowed_modifications):
		pass