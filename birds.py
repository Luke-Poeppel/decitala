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
Note: use my ``python3 jpg2png.py <PATH> remove/keep`` tool after scraping for some pics! (It's in the
home directory).
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
import re

from pathlib import Path

from music21 import converter

birds_data_path = '/Users/lukepoeppel/decitala_v.2.0/Birds'

class Bird(object):
    """
    Data structure for holding information about birdsongs encoded in Volume 5 of Messiaen's 
    Traite de Rhythme, de Couleur, d'Ornithologie.

    BIRDS:
    Le_Chocard_des_Alpes
    Le_Grand_Corbeau
    """
    def __init__(self, name):
        for x in Path(birds_data_path).rglob('*'):
            if x.is_dir() and x.name == name:
                self.all_data_path = x
                for x in self.all_data_path.iterdir():
                    if x.name == 'photos':
                        self.photo_path = x
                
                    if x.name == 'XML':
                        self.xml_path = x
                    
                    if x.is_file():
                        self.info_path = x
            
        txt = open(self.info_path, 'r').read().split('\n')
        for line in txt:
            s = line.split('=')
            if 'Name=' in line:
                self.name = s[1]
            if 'Name_Translation' in line:
                self.name_translation = s[1]
            if 'Binomial' in line:
                self.binomial_name = s[1]
            if 'Country' in line:
                self.country = s[1]
            if 'Region=' in line:
                self.region = s[1]
            if 'Region_Translation' in line:
                self.region_translation = s[1]
        
        streams = []
        for this_file in self.xml_path.iterdir():
            streams.append(converter.parse(this_file))
        #for this_file in os.listdir(self.xml_path):
            #if not(this_file.startswith('.')):
                #print(self.xml_path)
                #streams.append(converter.parse(str(self.xml_path) + '/' + this_file))

        self.streams = streams

    def __repr__(self):
        return '<{0} ({1})>'.format(self.name, self.name_translation)
    
    @property
    def num_transcriptions(self):
        count = 0
        for f in os.listdir(self.xml_path):
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
    
    def show_transcription(self, num=0):
        for this_stream in self.streams:
            stream_title = this_stream.metadata.title

        return self.streams[num].show()
    
    def show_photo(self):
        photo = random.choice([x for x in os.listdir(self.photo_path) if not(x.startswith('.'))])
        this_photo_path = str(self.photo_path) + '/' + photo
        img = mpimg.imread(this_photo_path)
        plt.imshow(img)
        binomial_split = self.binomial_name.split()
        plt.title('{0} ({1}) \n ${2} \: {3}$'.format(self.name, self.name_translation, binomial_split[0], binomial_split[1]))
        plt.show()

chocard = Bird('Le_Grand_Corbeau')
chocard.show_photo()

class Country(object):
    pass

class Region(Country):
    pass



