Basic Usage
------------------------------

The ``decitala`` package includes a number of rhythmic fragments in the ``corpora`` directory. We can
access the data for these fragments using the ``decitala.fragment`` module. Classes like ``fragment.Decitala``, 
``fragment.GreekFoot``, and  ``fragment.ProsodicFragment`` are supported. More fragment types will become 
available in the future. (Note: rhythmic corpora would be gladly accepted as contributions.) 
These objects are normally instantiated with a name (as provided in the corpora directory). We can 
also create custom fragments with the ``fragment.GeneralFragment`` class. 

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

See the ``fragment`` module for more information on methods. Also included is a function for fast queries 
on rhythmic datasets. The ``hash_table`` module allows the user to create and query a generic ``hash_table.FragmentHashTable``
object as below. The modification types are based on Olivier Messiaen's well-documentation rhythmic manipulation
techniques. 

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

The ``hash_table`` module also subclasses ``hash_table.FragmentHashTable`` with the included datasets. 
These objects are pre-loaded and can be created by calling, for instance, ``GreekFootHashTable()`` 
or ``DecitalaHashTable()`` (see the module for more options and information). If we're interested in 
querying a score for all detected fragments stored in a ``FragmentHashTable`` or its subclasses, 
we may use the ``search.rolling_hash_search`` function as follows:

   >>> from decitala.hash_table import GreekFootHashTable
   >>> from decitala.search import rolling_hash_search
   >>> composition = "/Users/lukepoeppel/decitala/tests/static/Shuffled_Transcription_1.xml"
   >>> all_search_results = rolling_hash_search(
   ...      filepath=composition,
   ...      part_num=0,
   ...      table=GreekFootHashTable(),
   ...      windows=[2, 3, 5, 7], # restrict search windows to our desired parameters.
   ... )
   >>> for result in all_search_results[:5]:
   ...      print(result["fragment"], result["onset_range"])
   ...
   <fragment.GreekFoot Anapest> (0.125, 0.625)
   <fragment.GreekFoot Iamb> (0.25, 0.625)
   <fragment.GreekFoot Iamb> (0.875, 1.25)
   <fragment.GreekFoot Amphibrach> (0.875, 1.375)
   <fragment.GreekFoot Trochee> (1.0, 1.375)

Normally, this package is used to find 'paths' of rhythms through a given composition. If we're interested 
in finding the "best" path of Greek metrics through a given part (as calculated by dynamic programming 
algorithms), we could use the following: 

   >>> from decitala.search import path_finder
   >>> from decitala.hash_table import GreekFootHashTable
   >>> composition = "/Users/lukepoeppel/decitala/tests/static/Shuffled_Transcription_1.xml"
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

Each element of ``path`` stores a number of pieces of information in a dictionary. It includes the fragment, 
its onset range, the associated pitch content of the region, whether it is slurred, the modification type of 
the fragment, etc... If a faster algorithm than Floyd-Warshall is desired, replace it with ``"Dijkstra"`` 
(though this currently disables the possibility of ``slur_constraint``). By version 0.13.0, the ``path`` elements
will be replaced by python dataclasses. 

**Rhythmic Manipulation**

Messiaen often altered rhythmic fragments from the various datasets he used before including 
them in his compositions. He still establishes an equivalence relation where
a fragment :math:`F` and a transformed fragment :math:`T(F)` are examples of the same fragment so long as there
exists a highly specified (but simple) transformation between them. These possible 
transformations include multiplicative augmentation, additive augmentation, mixed augmentation, 
flips into retrograde, subdivision, and "contiguous summation."