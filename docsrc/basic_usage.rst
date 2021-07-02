Basic Usage
------------------------------

Rhythm Tools
============

The ``decitala`` package includes a number of rhythmic fragments in the ``corpora`` directory. We can
access the data for these fragments using the ``decitala.fragment`` module. Classes like ``fragment.Decitala``, 
``fragment.GreekFoot``, and  ``fragment.ProsodicFragment`` are currently supported. More fragment types will become 
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
These objects are pre-loaded and can be created by calling, for instance, ``GreekFootHashTable()`` (or similarly
``DecitalaHashTable`` or ``ProsodicFragmentHashTable``):
   
   >>> from decitala.hash_table import GreekFootHashTable
   >>> ght = GreekFootHashTable()
   >>> ght
   <decitala.hash_table.FragmentHashTable 2855 fragments>

If we're interested in querying a score for all detected fragments stored in one of these 
``FragmentHashTable`` or its subclasses, we can use the ``search.rolling_hash_search``. This function
applies a rolling window to a composition and, at each stage, queries the hash table for the given 
fragment. 

   >>> from decitala.hash_table import GreekFootHashTable
   >>> from decitala.search import rolling_hash_search
   >>> composition = "/Users/lukepoeppel/decitala/tests/static/Shuffled_Transcription_1.xml"
   >>> all_search_results = rolling_hash_search(
   ...      filepath=composition,
   ...      part_num=0,
   ...      table=GreekFootHashTable(),
   ...      windows=[2, 3, 5, 7], # restrict search windows to our desired parameters.
   ... )

The ``rolling_hash_search`` function returns a list holding ``Extraction`` dataclasses. Each 
``Extraction`` object stores the fragment, onset range, pitch content, articulation information,
modification technique, etc... of these extracted fragments. 

   >>> for result in all_search_results[:5]:
   ...      print(result.fragment, result.onset_range)
   ...
   <fragment.GreekFoot Anapest> (0.125, 0.625)
   <fragment.GreekFoot Iamb> (0.25, 0.625)
   <fragment.GreekFoot Iamb> (0.875, 1.25)
   <fragment.GreekFoot Amphibrach> (0.875, 1.375)
   <fragment.GreekFoot Trochee> (1.0, 1.375)

This package can also be used to find 'paths' of rhythms through a given composition. If we're interested 
in finding a path of Greek metrics through a given part we use the dynamic programming path-finding
algorithms (implemented in ``decitala.path_finding``). The default algorithm used is an implementation of 
Dijkstra with a cost function determined by the gap between detected fragments and the number of onsets. 
Using only default parameters, this is as simple as:

   >>> from decitala.search import path_finder
   >>> from decitala.hash_table import GreekFootHashTable
   >>> composition = "/Users/lukepoeppel/decitala/tests/static/Shuffled_Transcription_1.xml"
   >>> path = path_finder(
   ...   filename=composition,
   ...   part_num=0,
   ...   table=GreekFootHashTable(),
   ... )
   >>> for fragment in path:
   ...   print(fragment.fragment, fragment.onset_range)
   ...
   <fragment.GreekFoot Peon_IV> (0.0, 0.625)
   <fragment.GreekFoot Iamb> (0.875, 1.25)
   <fragment.GreekFoot Peon_IV> (1.25, 1.875)
   <fragment.GreekFoot Peon_IV> (2.375, 3.0)

We can change a number of the default parameters used here. Most notably, the user can interpolate their
own cost function into the path-finding algorithm as follows:

   >>> from decitala.path_finding import path_finding_utils
   >>> from decitala.search import path_finder
   >>> from decitala.hash_table import GreekFootHashTable
   >>> my_cost_function = path_finding_utils.CostFunction(
   ...   def __init__(self, std_weight):
   ...      self.std_weight = std_weight
   ...   def cost(self, vertex_a, vertex_b):
   ...      return vertex_a.fragment.std() + vertex_b.fragment.std()
   ... ) 
   >>> composition = "/Users/lukepoeppel/decitala/tests/static/Shuffled_Transcription_1.xml"
   >>> path = path_finder(
   ...   filename=composition,
   ...   part_num=0,
   ...   table=GreekFootHashTable(),
   ...   cost_function_class=my_cost_function()
   ... )

**Rhythmic Manipulation**

Messiaen often altered rhythmic fragments from the various datasets he used before including 
them in his compositions. He still establishes an equivalence relation where
a fragment :math:`F` and a transformed fragment :math:`T(F)` are examples of the same fragment so long as there
exists a highly specified (but simple) transformation between them. These possible 
transformations include multiplicative augmentation, additive augmentation, mixed augmentation, 
flips into retrograde, subdivision, and "contiguous summation."