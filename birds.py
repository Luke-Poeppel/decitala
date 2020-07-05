# -*- coding: utf-8 -*-
####################################################################################################
# File:     birds.py
# Purpose:  Birdsong in the music of Olivier Messiaen.
# 
# Author:   Luke Poeppel
#
# Location: Kent, CT 2020
####################################################################################################
"""
TODO:
- bird.regions
- bird.num_transcriptions
- bird.transcriptions()[i].show()
- bird.country
- bird.show_photo() (if path has more than 1 photo, pick random photo.)
- bird.all_info
- bird.listen()
"""
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
import random 

from pathlib import Path

birds_data_path = '/Users/lukepoeppel/decitala_v.2.0/Birds'

class Bird(object):
    def __init__(self, name):
        for x in Path(birds_data_path).rglob('*'):
            if x.is_dir() and x.name == name:
                self.all_data_path = x
                for x in self.all_data_path.iterdir():
                    if x.name == 'photos':
                        self.photo_path = x
                
                    if x.name == 'XML':
                        self.streams_path = x
                    
                    if x.is_file():
                        self.info_path = x

    def __repr__(self):
        return '<Chocard des Alpes (Alpine Chough)>'
    
    @property
    def num_transcriptions(self):
        count = 0
        for f in os.listdir(self.streams_path):
            if not(f.startswith('.')):
                count += 1
        
        return count
    
    @property
    def num_photos(self):
        count = 0
        for f in os.listdir(self.photo_path):
            if not(f.startswith('.')):
                count += 1
    
        return count
    
    def show_photo(self):
        photo = random.choice([x for x in os.listdir(self.photo_path) if not(x.startswith('.'))])
        this_photo_path = str(self.photo_path) + '/' + photo
        img = mpimg.imread(this_photo_path)
        plt.imshow(img)
        plt.title('Chocard des Alpes (Alpine Chough) \n $Pyrrhocorax \: graculus$')
        plt.show()
  
class Country(object):
    pass

class Region(Country):
    pass