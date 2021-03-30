# decitala
[![Wiki][wiki-img]][wiki]
[![Actions Status](https://github.com/Luke-Poeppel/decitala/workflows/Build/badge.svg)](https://github.com/Luke-Poeppel/decitala/actions)
![Coverage](./coverage.svg)
![img](https://img.shields.io/badge/semver-0.9.0-green)
[![DOI](https://zenodo.org/badge/275475667.svg)](https://zenodo.org/badge/latestdoi/275475667)

The ``decitala`` package aims to make rhythmic analysis of Olivier Messiaen's music easier, particularly with respect to his use of ethnological rhythmic fragments.  

<img src="sangitaa_image.png" height="350" width="660" style="border: 2px solid">

**The Kalānidhiḥ commentary on the opening of Śārngadeva's desītāla definitions (appearing in the** _Tālādhyāya_ **of the Saṅgītaratnākara**. 

-_"From the Sūtra beginning with 'laghu': having promised the tālas definition, he explains them sequentially. One laghu (|) āditāla (1) two drutas, one laghu (o o |) the dvitiya tāla (2) one druta, two druta viramas (o oc oc) the tṛtīya tāla (3) two laghus, one druta (| | o) the caturtha tāla (4) both of them drutas (o o) pacchamaḥ (5) two plutas, two gurus, one laghu (Sc Sc S S |) niḥśaṅkalīlaḥ (6) |"_ (Translation by Luke Poeppel)

### Documentation
Available at: https://luke-poeppel.github.io/decitala/.

### Installation
This package requires music21 which is available [here](https://github.com/cuthbertLab/music21). It is recommended you download this library separately as its installation helper will set some useful preferences for you (like default notation software). 
```
$ cd # Navigate to home directory
$ git clone https://github.com/Luke-Poeppel/decitala
$ cd decitala
$ pip3 install -e .
$ pre-commit install
$ decitala --version # Check for proper installation.
```
If you would like to use the ``vis.create_tree_diagram`` function, it requires several additional installation steps. These steps are available in the documentation. It is also recommended that you download the following application for viewing SQLite databases: [sqlite-browser](https://sqlitebrowser.org/). 

### Why is it called decitala?
Śārngadeva (शार्ङ्गदेव) compiled a list of 130 rhythmic fragments called desītālas (देसी ताल) in his 13th-century musicological treatise, the Sangītaratnākara (सङ्गीतरत्नाकर). Messiaen used the gallicized "deçi-tâlas" in his writing which has been simplified here to "decitala."


  [wiki-img]: https://img.shields.io/badge/docs-Wiki-blue.svg
  [wiki]: https://luke-poeppel.github.io/decitala/