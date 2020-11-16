# -*- coding: utf-8 -*-
####################################################################################################
# File:     prepare_docs.py
# Purpose:  Simple script for running the command line arguments required for building sphinx documentation.
# 
# Author:   Luke Poeppel
#
# Location: Frankfurt, DE 2020 
####################################################################################################
"""
1. Run `python3 setup.py install` in the decitala directory.
2. cd into the docs directory.
3. `make html`
"""
import os
def prepare():
	os.chdir("/Users/lukepoeppel/decitala/")
	os.system("python3 setup.py install")
	os.chdir("/Users/lukepoeppel/decitala/docs")
	os.system("make html")
	
if __name__ == "__main__":
	prepare()