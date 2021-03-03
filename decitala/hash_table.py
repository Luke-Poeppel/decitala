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



"""
want:
dht
{
    (1.0, 2.0, 3.0): "fragment_name_mod",
    (2, 1.0, 4): "fragment_name_mod"
}
"""

@dataclass
class FragmentHashTable:
	def __init__(
			self, 
			data, 
			allowed_modifications=[
				"r", 
				"rr", 
				"d", 
				"rd", 
				"sr",
				"rsr"
			],
		):
		pass
	
	@classmethod
	def from_frag_type(cls, frag_type):
		pass


