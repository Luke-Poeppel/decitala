.. decitala documentation master file, created by
   sphinx-quickstart on Sun Nov 15 16:04:11 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Decitala Documentation
====================================

The ``decitala`` package aims to make rhythmic analysis of encoded musical corpora easier. This toolkit can 
be used to both detect rhythmic fragments in a work and suggest possible alignments. ``decitala`` is being developed 
to make the analysis of Olivier Messiaen's music easier, particularly with respect to his use of ethnological 
rhythmic fragments. If you find the tools/corpora to be useful or discover a bug, feel free to 
file an issue at https://github.com/Luke-Poeppel/decitala/issues or drop me a note (luke.poeppel@gmail.com).   
I'd love to hear about how you used them and/or take suggestions. 

Source Code: https://github.com/Luke-Poeppel/decitala. 

Installation
====================================
Run the following::

   $ cd # Navigate to home directory
   $ git clone https://github.com/Luke-Poeppel/decitala.git
   $ cd decitala
   $ pip3 install -e .
   $ pre-commit install # Only needed if you'd like to contribute code.
   $ decitala --version # Check for proper installation.

Basic Usage
====================================
The ``decitala`` package includes a number of rhythmic fragments in the ``corpora`` directory. Currently, 
two fragment types are supported: ``fragment.Decitala`` and ``fragment.GreekFoot``. More possibilities
will become available in the future. These objects are normally instantiated with a name (as provided). 
We can also create custom fragments with the ``fragment.GeneralFragment`` class. 

   >>> from decitala.fragment import Decitala, GreekFoot, GeneralFragment
   >>> ragavardhana = Decitala("Ragavardhana")
   >>> ragavardhana.ql_array()
   array([0.25 , 0.375, 0.25 , 1.5  ])
   >>> bacchius = GreekFoot("Bacchius")
   >>> bacchius.greek_string
   '⏑ –– ––'
   >>> my_fragment = GeneralFragment(data=[1.0, 0.25, 0.375, 4.0]) # can also be instantiated with a filepath. 
   >>> my_fragment.std()
   1.5242185497821

See the ``fragment`` module for more information. Also included in the package is a method for fast queries 
on rhythmic datasets. The ``hash_table`` module stores a number of possible modifications to a given fragment 
(based on Messiaen's well-documented modification techniques). To create and query a generic ``hash_table.FragmentHashTable``, 
we may use the following:

   >>> from decitala.hash_table import FragmentHashTable
   >>> my_ht = FragmentHashTable(
   ...      datasets = ["greek_foot"],
   ...      custom_fragments = [GeneralFragment(data=filepath), Decitala("Ragavardhana")]
   ... )
   >>> my_ht.datasets
   ["greek_foot"]
   >>> my_ht.load() # You must first load the modifications into the data.
   >>> query = my_ht.data[(1.0, 1.0, 2.0)]
   >>> query["fragment"]
   <fragment.GreekFoot Anapest>
   >>> query["factor"]
   1.0

The ``hash_table`` module subclasses ``hash_table.FragmentHashTable`` with the included datasets. These objects are pre-loaded
and can be created by calling the classes ``GreekFootHashTable()`` or ``DecitalaHashTable()``, as below. Normally, this package 
is used to find paths of rhythms through a given composition. If we're interested in finding the "best" path of Greek metrics 
through a given part (as calculated by dynamic programming algorithms), we simply use the following: 

   >>> composition = "/Users/lukepoeppel/decitala/tests/static/Shuffled_Transcription_1.xml"
   >>> from decitala.search import path_finder
   >>> from decitala.hash_table import GreekFootHashTable
   >>> path = path_finder(
   ...   filename=composition,
   ...   part_num=0,
   ...   table=GreekFootHashTable(),
   ...   algorithm="floyd-warshall",
   ...   slur_constraint=True # forces the algorithm to include slurred fragments if found. 
   ... )
   >>> for fragment in path:
   ...   print(fragment["fragment"], fragment["onset_range"])
   ...
   <fragment.GreekFoot Peon_IV> (0.0, 0.625)
   <fragment.GreekFoot Iamb> (0.875, 1.25)
   <fragment.GreekFoot Peon_IV> (1.25, 1.875)
   <fragment.GreekFoot Peon_IV> (2.375, 3.0)

Each element of ``path`` stores a number of pieces of information in a dictionary. It includes the fragment, its onset range, the
associated pitch content of the region, whether it is slurred, the modification type of the fragment, etc... If a faster algorithm 
than Floyd-Warshall is desired, replace it with ``"Dijkstra"`` (though this currently disables the possibility of ``slur_constraint``).

Rhythmic Manipulation
====================================
Messiaen often altered rhythmic fragments from the various datasets he used before including 
them in his compositions. He still establishes an equivalence relation where
a fragment :math:`F` and a transformed fragment :math:`T(F)` are examples of the same fragment so long as there
exists a highly specified (but simple) transformation between them. These possible 
transformations include multiplicative augmentation, additive augmentation, mixed augmentation, 
flips into retrograde, subdivision, and "contiguous summation."

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
   mods/path_finding
   mods/search
   mods/trees
   mods/utils
   mods/vis

.. toctree::
   :maxdepth: 2
   :caption: Rhythmic Fragments
   :glob:

   datasets/decitalas
   datasets/greek_metrics

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
