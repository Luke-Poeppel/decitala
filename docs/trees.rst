========
trees.py
========

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

.. automodule:: decitala.trees
   :members:
   :member-order: bysource
   :show-inheritance: