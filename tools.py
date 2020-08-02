# -*- coding: utf-8 -*-
####################################################################################################
# File:     tools.py
# Purpose:  Random useful functions for Messiaen. 
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################

from music21 import converter

def get_stripped_object_list(filepath, part_num):
    '''
    Returns the quarter length list of an input stream (with ties removed), but also includes 
    spaces for rests.

    NOTE: this used to be .iter.notesAndRest, but I took it away, for now, to avoid complications.
    '''
    score = converter.parse(filepath)
    part = score.parts[part_num]
    object_list = []

    stripped = part.stripTies(retainContainers = True)
    for this_obj in stripped.recurse().iter.notes: 
        object_list.append(this_obj)

    return object_list
	
def get_indices_of_object_occurrence(filepath, part_num):
    '''
    Given a file path and part number, returns a list containing tuples of the form [(OBJ, (start, end))].

    >>> bach_path = '/Users/lukepoeppel/Documents/GitHub/music21/music21/corpus/bach/bwv66.6.mxl'
    >>> for data in get_indices_of_object_occurrence(bach_path, 0)[0:12]:
    ...     print(data)
    (<music21.note.Note C#>, (0.0, 0.5))
    (<music21.note.Note B>, (0.5, 1.0))
    (<music21.note.Note A>, (1.0, 2.0))
    (<music21.note.Note B>, (2.0, 3.0))
    (<music21.note.Note C#>, (3.0, 4.0))
    (<music21.note.Note E>, (4.0, 5.0))
    (<music21.note.Note C#>, (5.0, 6.0))
    (<music21.note.Note B>, (6.0, 7.0))
    (<music21.note.Note A>, (7.0, 8.0))
    (<music21.note.Note C#>, (8.0, 9.0))
    (<music21.note.Note A>, (9.0, 9.5))
    (<music21.note.Note B>, (9.5, 10.0))
    '''
    data_out = []
    stripped_object_list = get_stripped_object_list(filepath, part_num)
    for this_obj in stripped_object_list:
        data_out.append((this_obj, (this_obj.offset, this_obj.offset + this_obj.quarterLength)))

    return data_out

if __name__ == '__main__':
    import doctest
    doctest.testmod()


