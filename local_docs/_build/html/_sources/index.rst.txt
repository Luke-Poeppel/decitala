.. decitala documentation master file, created by
   sphinx-quickstart on Sun Nov 15 16:04:11 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Decitala Documentation
====================================

Tools for automating ethnological rhythmic analysis of Olivier Messiaen's music. The basic
pipeline used in this package is Search →→ Path Finding →→ Analysis.

The version of the ``decitala`` package can be found with ``decitala --version``. 

Rhythmic Manipulation
====================================
Messiaen often altered rhythmic fragments from the decitala database before including 
them in his composition. But he still establishes a kind of equivalence relation such that
a fragment :math:`F` and a transformed fragment :math:`T(F)` are equivalent if there
exists a special kind (and highly specified) transformation between them. These possible 
transformations include multiplicative augmentation, additive augmentation, mixed augmentation, 
flips into retrograde, and subdivision. Using a n-ary tree-based algorithm, we can 
efficiently search for such modification.

We define the following representations of a rhythm (see X for the implementation):

+--------+-----------------------------------+
| Symbol | Corresponding Search              |
+========+===================================+
| ``r``  | ratio                             |
+--------+-----------------------------------+
| ``rr`` | retrograde-ratio                  |
+--------+-----------------------------------+
| ``d``  | difference                        |
+--------+-----------------------------------+
| ``rd`` | retrograde-difference             |
+--------+-----------------------------------+
| ``sr`` | subdivision-ratio                 |
+--------+-----------------------------------+
| ``rsr``| retrograde-subdivision-ratio      |
+--------+-----------------------------------+
| ``sd`` | subdivision-difference            |
+--------+-----------------------------------+
| ``rsd``| retrograde-subdivision-difference |
+--------+-----------------------------------+

Basic Usage
====================================
Coming soon! 

Installation
====================================
0. Navigate to home directory with ``cd``
1. ``git clone https://github.com/Luke-Poeppel/decitala``
2. ``cd decitala``
3. ``pip3 install -e .``
4. ``pre-commit install``

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. toctree::
   :maxdepth: 2
   :caption: Modules
   :glob:

   mods/database
   mods/path_finding
   mods/fragment
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
