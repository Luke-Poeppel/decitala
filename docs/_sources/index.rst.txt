.. decitala documentation master file, created by
   sphinx-quickstart on Sun Nov 15 16:04:11 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Decitala Documentation
====================================

The ``decitala`` package aims to make rhythmic search and analysis of encoded musical corpora easier. This toolkit can 
be used to both detect rhythmic fragments in a work and suggest possible alignments. ``decitala`` is being developed 
to make the analysis of Olivier Messiaen's music easier, particularly with respect to his use of ethnological 
rhythmic fragments. If you find the tools/corpora to be useful or discover a bug, feel free to 
file an issue `here <https://github.com/Luke-Poeppel/decitala/issues>`_ or drop me a note (luke.poeppel@gmail.com).   
I'd love to hear about how you used them and/or take suggestions. 

Source Code: https://github.com/Luke-Poeppel/decitala. 

Written by: Luke Poeppel (lukepoeppel.com)

Installation
====================================
Run the following::

   $ cd # Navigate to home directory
   $ git clone https://github.com/Luke-Poeppel/decitala.git
   $ cd decitala
   $ pip3 install -e .
   $ pre-commit install # Only needed if you'd like to contribute code.
   $ decitala --version # Check for proper installation.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. toctree::
   :maxdepth: 2
   :caption: Modules
   :glob:

   mods/database
   mods/fragment
   mods/hash_table
   mods/hm
   mods/path_finding
   mods/search
   mods/sp
   mods/trees
   mods/utils
   mods/vis

.. toctree::
   :maxdepth: 2
   :caption: Rhythmic Corpora
   :glob:

   datasets/decitalas
   datasets/greek_metrics

.. toctree::
   :maxdepth: 2
   :caption: Basic Usage
   :glob:

   basic_usage

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
