# Change Log
All important changes to the decitala package will be documented here.

The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.14.0](https://github.com/Luke-Poeppel/decitala/tree/v0.14.0) ???
#### Added
- Moved all `moiseaux` (private repo) tools to `decitala`. The `decitala.db` now holds `Transcription` and `Species` SQLAlchemy query wrappers; also added the corresponding helpers: `db.get_all_transcriptions()` and `db.get_all_species()`. 
- Added `database.db_utils` module. 
- Added a `make_core_dbs` file to `decitala.extra` that creates the fragment database and ODNC database. 
- Added `decitala.hm` directory for holding all harmony and melody (i.e. pitch) related analysis tools. This directory holds an `hm.molt` module (tools for dealing with the modes of limited transposition), an `hm.contour` module for contour calculations (moved some general utils there, like Morris prime contour calculation), and an `hm.hm_utils` for utility functions; this final module also stores the associated color and key-finding coefficient data.
- WIP: Improved implementation of Morris contour reduction algorithm (1993) and added implementation of Schultz's modified version (see Schultz 2008, p. 108, ex. 14). 
- Added `decitala.sp` directory for holding signal processing tools. It currently only holds an `sp_utils` module for spectrogram/audio plotting, but this directory will be populated in future versions. 
- Added Dipartite and Tripartite Hexasyllabic Metrics: Dianapest, Dicretic, Didactyl, and Triiamb. 
- Scripts for calculating hyperparameters and plotting analysis are in the `decitala.extra` directory. Latest accuracy is 74.41%. 
- Added `enforce_earliest_start` argument to `path_finding_utils.sources_and_sinks`. 
- Added `split()` method to both `GeneralFragment` and `Extraction`. Used for splitting Di- and Tri- partite greek prosodic feet. 
- Added `slur_count` and `slur_start_end_count` arguments to the `Extraction` dataclass.

#### Removed
- Dactylo-Epitrite. Removed as, along with Dochmius, there are a large number of variations of the fragment (see Traité Vol. 1).

#### Fixed
- Graph calculation for Dijkstra was being done _within_ the function. Given the agnostic source/target picking, this was very inefficient; now, the graph is generated a single time in `dijkstra_best_source_and_sink`. 
- Various bugfixes for Dijkstra and Floyd-Warshall for source and target picking. 

## [v0.13.2](https://github.com/Luke-Poeppel/decitala/tree/v0.13.2) June 19, 2021
#### Fixed
- Added the missing progress bar for `path_finding_utils.build_graph` (`verbose=True` did nothing). 
- Fixed bug (#144) in `measure_divide_mode` of `utils.get_object_indices`. 
- Fixed several documentation errors. 

## [v0.13.1](https://github.com/Luke-Poeppel/decitala/tree/v0.13.1) June 19, 2021
#### Fixed
- Issue #157: broken `source` button. 

## [v0.13.0](https://github.com/Luke-Poeppel/decitala/tree/v0.13.0) June 19, 2021
#### Added
- All results from `search.rolling_hash_search` are now stored as `Extraction` dataclasses. This new approach greatly simplifies the inconsistent dictionary-style search results. Also removes the need to store `frag_type`s in the hash tables. 
- Added a `CostFunction` class to `decitala.path_finding_utils`. This cost function class is to be used as an input to `path_finder` and `dijkstra` (and `floyd_warshall`, as well), replacing the previously used `weights` dictionaries. This addition allows the user to input any cost function they like (see PR#152). 
- Added three functions to `fragment` for querying the fragment database for each fragment type: `get_all_greek_feet`, `get_all_decitalas`, and `get_all_prosodic_fragments`. 
- Added `rolling_SRR` function to utils. 
- Added `decitala.extra` module where miscellaneous scripts will be stored. This will eventually hold the script for computing hyperparameters (`decitala.extra.hyperparameters`) and the formerly hidden script for remaking analysis files. 
- Added `decitala dtest --module` CLI tool for quickly running doctests (hindered by relative imports). Consequently removed the `tests/doctest_runner.py` file. 
- Restructured the DB approach. Added a `database` directory that will store all the database-related material. 

#### Changed
- All tree creation has migrated to the [treeplotter](https://github.com/Luke-Poeppel/treeplotter) package. Removed the Treant templates accordingly. 
- Greatly simplified the logic in `successive_ratio_array` and `successive_difference_array` using numpy. 

#### Fixed
- Issues #147: allow weight hyperparameters as input to Dijkstra; #143: `0` as possible quarter length in `FragmentHashTable`; #157: broken source button in docs (as well as missing section). 

## [v0.12.1](https://github.com/Luke-Poeppel/decitala/tree/v0.12.1) May 23, 2021
#### Fixed
- The `path_finding_utils.build_graph` function was calculating the cost between two vertices without checking if it needed to be calculated. 
- Bug in `GreekFoot` returned incorrect `self.data` due to extra slash in path. 
- Fixed incorrect presets for `generate_all_modifications` in the hash table module. Also now force clearing the dictionary before running load with new parameters. 
- Documentation fixes; added screenshots of the visualization functions. 

## [v0.12.0](https://github.com/Luke-Poeppel/decitala/tree/v0.12.0) May 21, 2021
#### Added
- Began adding prosodic patterns from Traité T1 analyses. Also added classes (and corresponding `frag_types`) for the package. You can now create `fragment.ProsodicFragment` objects as well as create, for instance, a `ProsodicFragmentHashTable`. These fragments will accumulate over future versions (directory structure subject to change).  
- Added `plot_2D_search_results` to `vis` module for plotting search results in XY space, along with a given path. (This implements #4, finally!)
- Re-added `search.rolling_search_on_array`. It conforms to the hash table approach. (See #48)
- Added `allow_contiguous_summation` parameter to `search.rolling_hash_search` and `path_finder`. (See #127)
- Added `Breve` and `Macron` classes to the fragments module. This will eventually be used in accessing the `parts` of a `ProsodicFragment`. 
- Added missing parameter for `windows` and `allow_subdivision` in `search.path_finder`.

#### Changed
- Big documentation improvements, code/logic cleanup. Trying a new solution for documentation maintenence. Using a github build in the sphinx makefile. 
- Removed `utils.is_octatonic_collection`. All Modes of Limited Transposition stuff will eventually be living in `moiseaux.molt`. 
- Moved some `search`-specific functions from `utils` (they were really helpers, not utility functions). See #138. 

## [v0.11.1](https://github.com/Luke-Poeppel/decitala/tree/v0.11.1) May 13, 2021
#### Changed
- Moved `dseg` calculation to `utils.py` that `GeneralFragment.dseg` now wraps. Also made `reduced` a parameter in the same function for simplicity (removing the need for a second method). 
- Table name in `database.py` for extractions is now `Extractions`, not `Fragments` (this made no sense). 
- Structure of documentation. Major improvements to Basic Usage. 

#### Fixed
- Missing `lru_cache` in `GeneralFragment.ql_tuple()`. 
- Missing `get_engine/get_session` in `database.py`. 
- Issues #133: formatting issue in docs; #131: missing assertions in database tests. 

## [v0.11.0](https://github.com/Luke-Poeppel/decitala/tree/v0.11.0) May 12, 2021
#### Added
- Added a `utils.phrase_divider` function for over-simplistically dividing a filepath/part-num combination into phrases (in the same output as `utils.get_object_indices`). The division is only on the basis of the appearance of rests and fermatas. (See #104)
- Added a `contour_to_neume` function in utils.py for some experiments with Wai Ling Cheong's work (2008). 
- Hash tables and search now support stretch augmentation. Added `utils.stretch_augment` for simplicity. 

#### Changed
- All functions accepting a `ql_array` in `utils.py` now take in a variable called `ql_array` –– a few were set to `fragment` instead which was confusing (fixes #122). 
- The `measure_divider_mode` of `utils.get_object_indices` now accepts `"str"` and `"list"` to be consistent with standard python type naming. 
- Renamed `utils.ts_to_reduced_ts` to `utils.reframe_ts` and now allow any input `new_denominator` (reducing maximally by default).  
- Removed complicated Cauchy-Schwartz pre-filtering in the Tree instantiation. Faster to just overwrite than check. 

#### Fixed
- Issues #130: Allow both lowercase and uppercase algorithm names in `search.path_finder`; #129: contiguous summation fails with rests; #132: `ignore_grace` was not doing anything (also fixed docs typo) in `get_object_indices`; 

## [v0.10.1](https://github.com/Luke-Poeppel/decitala/tree/v0.10.1) May 1, 2021
#### Changed
- The caching in the `fragment` module now uses `functools.lru_cache(maxsize=None)` (replacing the newer `functools.cache`) to allow support for python 3.7/3.8. 

#### Fixed
- The `utils.find_possible_superdivisions` function was including itself as a possible superdivision. This was a bit confusing, so I added an `include_self` parameter. This option was accidentally set to `False` by default which has been fixed. 
- Issues #125: duplicate `sr` and `rsr` results from `rolling_hash_search`; #123/#126: source-sink error in Dijkstra (fixed with a much more general solution (see `path_finding.dijkstra.dijkstra_best_source_and_sink`) and integrated into `search.path_finder`. 

## [v0.10.0](https://github.com/Luke-Poeppel/decitala/tree/v0.10.0) April 29, 2021
#### Added
- Revamped the database module (see #120). Everything is now ported over to SQLAlchemy and is more easily extendable to broader rhythmic corpora. Also added a `database.batch_create_database` function for creating a database from a large set of compositions. 
- Implemented Dijkstra's Algorithm for path finding. This is now the default algorithm used in `search.path_finder`, but the user can override this. 
- New utils functions and additions: a `non_retrogradable_measures` function for finding all palindromic measures in a given filepath and part number; an optional `measure_divider_mode` parameter to `utils.get_object_indices` which returns the same objects, divided into lists of measures or objects divided by a string; a `utils.ts_to_reduced_ts` function for fully reducing time signatures; a `UtilsException` class. 
- The `search.path_finder` function now has optional `save_filepath` argument for dumping the results to a JSON file. (#97)
- All classes inheriting from `GeneralFragment` (currently just `Decitala` and `GreekFoot`) as well as `GeneralFragment` itself now have a `frag_type` class attribute. 

#### Changed
- Renamed the `fragments` directory to `corpora`. Also removed the `.sib` encoding files for the greek metrics to make the package lighter weight. 
- The `fragments` module was relying on SQLite in a piecemeal way. Objects from encoded corpora are now proper SQLAchemy models for consistency with the rest of the package. 
- The `fragment.morris_symmetry_class` function now returns integers representing the classes (instead of string describing them). The meaning of each class is given in the documentation. 
- Refactored `path_finding.floyd_warshall` and added helper functions for all path-finding algorithms to `path_finding_utils.py`. 
- The CLI `path-finder` tool now logs the saved file. 
- Improved doctest integration by running them within the (pytest) tests directory. 
- Removed all `# -*- coding: utf-8 -*-` lines. 
- Renamed `trees.rolling_search` to `trees.rolling_tree_search` to be consistent with the other rolling search type(s) (#114).  
- The `Decitala.get_by_id` class method now requires a string as input. Additionally the `id_num` property returns a string as a number of the Decitalas have subtalas. 
- All `GeneralFragment` objects now have the `carnatic_string` and `greek_string` properties. 

#### Fixed
- Issues #116: missing result logging from `decitala.cli.pathfinder`; #115: incorrect results from Morris symmetry classes; #73: default value for `try_contiguous_summation`. 
- Incorrect serialization condition for `GeneralFragment` –– forced incorrect parsing to and from analysis files. 

## [v0.9.1](https://github.com/Luke-Poeppel/decitala/tree/v0.9.1) April 16, 2021
#### Added
- Added testing to improve coverage (50%-52%)

#### Fixed
- Issues #102: empty numpy iterator for cases with no extracted fragments; #109: missing verbose argument in `search.path_finder`; #111: UnboundLocalError for Bach chorale –– this also resolves #101; #106: reformatted analysis JSON files to match the output of `search.path_finder` (every extraction is a dictionary). 
- Typo in Documentation installation instructions. 
- Missing documentation for `vis.result_bar_plot`. 
- Fixed incorrect order of Morris Symmetry Classes (1999). 

#### Removed
- Removed `py_modules` from `setup.py`. 

## [v0.9.0](https://github.com/Luke-Poeppel/decitala/tree/v0.9.0) April 14, 2021
#### Added
- Function for annotating a score with the extracted data: ``vis.annotate_score``. 
- Added private ``remake_analysis_files.py`` for remaking the analysis files in each release. 
- Added testing to improve coverage (46%-50%). 
- Added various utility functions: `utils.measure_by_measure_time_signatures` (for for extracting measure-by-measure time signatures); `utils.is_octatonic_collection` (for checking if pitch content belongs to one of the two octatonic collections); `utils.write_analysis` (for writing analysis JSON files); `utils.net_ql_array` (for returning all quarter length values in a given composition as a vector); `utils.transform_to_time_scale` (for getting the time-scale notation of quarter length array).
- Added `PRIMES` variable to `utils.py` for storing primes <100. 
- Added `vis.result_bar_plot` for plotting the counts of the extracted fragments in a `path_finder` list or analysis JSON (#105).
- Added the first class of the `Theorie_Karnatique` dataset (Tiśra) to the `fragments` directory. These are not yet integrated into the `fragments` module.  

#### Changed
- Improved ``fragment.py``'s ``FragmentEncoder`` and ``FragmentDecoder`` classes with better logic; this fixes #99: incorrect ``frag_type`` in the JSON encoding. 

#### Fixed
- Missing import bug in ``vis.annotate_score``. 
- README: incorrect installation notes in README, improved translation to the commentary. 
- Issues #53: duplicates in logs caused by saved handlers; #100: `path_finder` bug related to `curr_best_sink`; 

## [v0.8.4](https://github.com/Luke-Poeppel/decitala/tree/v0.8.4) March 22, 2021
#### Fixed
- Added the missing Zenodo badge to the README.md file.

## [v0.8.3](https://github.com/Luke-Poeppel/decitala/tree/v0.8.3) March 22, 2021
#### Fixed
- Issue #90: removed unused JS modules used in tree visualization. 

## [v0.8.2](https://github.com/Luke-Poeppel/decitala/tree/v0.8.2) March 22, 2021
#### Added
- Added a ``.coveragerc`` file for excluding the tests and CLI tools from coverage reports. 

#### Changed
- Refactored ``get_path`` to include a ``reconstruct_standard_path`` helper function. 

#### Fixed
- Additional bugfixes for slur constraint in ``get_path`` (causing infinite runtime). 
- Issues #19: referenced a fault Nary tree size. It appears to be fixed, but I added a test; #95: the ``pathfinder`` command line tool now writes to JSON; #94: minor formatting error in ``floyd_warshall.py``.

## [v0.8.1](https://github.com/Luke-Poeppel/decitala/tree/v0.8.1) March 20, 2021
#### Added
- Coverage and coverage shield for code improvement. 

#### Changed
- The CLI ``pathfinder`` tool now wraps the search.py module's ``path_finder`` function. 
- The ``create_tree_diagram`` now uses ``webshot`` from R to save to PNG. Can also now effectively do ``FragmentTree.show()`` without opening in the browser using the wand library. 

#### Fixed
- Github Actions is now caching dependencies for faster builds.
- Fixed bugs in ``vis.create_tree_diagram``. 
- Bugfixes in ``path_finder`` related to ``is_spanned_by_slur`` attribute. 
- The ``utils.roll_window`` now ensures that no ``NoneTypes`` are included if the window size is greater than the input data. Similarly, in ``rolling_hash_search`` we ensure no searches of size greater than the length of the data. 
- Fixed missing Iambs in the GreekFoot hash table (#91). 
- The ``Decitala`` and ``GreekFoot`` classes included a ``stream`` attribute in their ``__init__`` –– this is already created in the ``super``.
- Hotfix to extremely strange inheritance bug in the ``GeneralFragment`` child classes. (#92)
- Bugfix in ``floyd_warshall.get_path``. Function was inserting the given starting point in the path, even if it was overrided by the slur constraint. 

## [v0.8.0](https://github.com/Luke-Poeppel/decitala/tree/v0.8.0) March 15, 2021
#### Added
- Added a ``loader`` function in utils.py for easy loading of Messiaen's analyses (encoded by me). Also added additional analysis json files (including parts 0 & 1 of Livre d'Orgue (1951-52) movement V). 
- Added testing and improved functionality for the hash table creation and ``rolling_hash_search``. This included adding a ``GreekHashTable`` and ``CombinedHashTable`` for a combined database. 
- Added an optional progress bar to the Floyd-Warshall algorithm. 
- Added function for getting the best source and sink after Floyd-Warshall (``floyd_warshall.best_source_and_sink(data)``). 
- Added ``+/- 0.125, +/- 0.375, -0.25, 0.875, 1.75, 2.625, 3.5, 4.375`` as possible difference valuess in ``hash_table.py``; also added ``0.125, 0.25`` as a possible ratio values. 
- Added a ``path_finder`` command line tool that wraps all the functions for analysis via Floyd-Warshall & the hash tables. Used simply as ``decitala path-finder --filepath ... --part_num ... --frag_type ...``. 
- Added a ``ignore_single_anga_class_fragments`` parameter to ``rolling_hash_search`` (default is False). 
- Added optional ``slur_constraint`` parameter to ``floyd_warshall.best_path`` which constrains the path to require the slurred fragments found (#87). 

#### Removed
- Removed the ``self.conn`` attribute in the ``Decitala`` class; in doing so, we can now use multiprocessing (multiprocessing requires pickling which is impossible on sqlite3 ``Connection`` objects). 

#### Fixed
- Missing modification data in ``rolling_hash_search``. 

## [v0.7.4](https://github.com/Luke-Poeppel/decitala/tree/v0.7.4) March 8, 2021 (Kent)
#### Fixed
- Finished applying flake8 to modules. 
- Fixed #83 (missing modules in setup.py)

## [v0.7.3](https://github.com/Luke-Poeppel/decitala/tree/v0.7.3) March 8, 2021 (Kent)
#### Fixed
- Re-gitignored ``local_docs``. 

## [v0.7.2](https://github.com/Luke-Poeppel/decitala/tree/v0.7.2) March 8, 2021 (Kent)
#### Fixed
- Missing modifications types ``rr``, ``rd``, ``sr``, and ``rsr`` in ``DecitalaHashTable``. Refactored and clean up the instantiation code –– still requires work for Greek metrics and General fragments. 
- Applied flake8 to vis.py.
- JSON Serialization/Deserialization errors for ``GeneralFragment`` and its inherited classes. This makes saving "training data" easier. (This step is for the next minor patch.)
- The ``local_docs`` directory (this was previously gitignored for no good reason). Also an analyses directory of databases holding valid analysis of compositions. 

## [v0.7.1](https://github.com/Luke-Poeppel/decitala/tree/v0.7.1) March 3, 2021 (NYC)
### Fixed
- In enabling github actions, I hit several git/github snags. There were some commit message errors and bad merges. Hopefully everything is fixed now. 

## [v0.7.0](https://github.com/Luke-Poeppel/decitala/tree/v0.7.0) March 3, 2021 (NYC)
#### Added
- Implemented the Floyd-Warshall Algorithm for path-finding. 
- Added a ``hash_table.py`` module for more efficient searching. This is  used in ``search.rolling_hash_search``.
- Added flake8 for maintaining PEP8 standards. Applied to setup.py, fragment.py, and utils.py. 
- Added a `fragment_roll` function to `vis.py` (#62). 
- Added a progress bar to `DBParser.model_full_path` to more easily track progress. 
- Added a `DBParser.onset_ranges` method that returns a list of tuples holding the onset ranges of all extracted fragments.
- Added a `return_data` parameter to `model_full_path` (just a wrapper for `path_data`). 
- Added an MIT License

#### Changed
- The ``trees.py`` module has been refactored into ``trees.py`` and ``search.py`` with the relevant search functions in the latter module. (#27)

#### Fixed
- Issue #54 (unreferenced variable); Issue #51 (updated databases); Issue #58 (unfiltered fragment table); 

## [v0.6.3](https://github.com/Luke-Poeppel/decitala/tree/v0.6.3) February 23, 2021 (NYC)
#### Added
- Added support/testing for python3.8. 

#### Changed
- Migrated to SQLAlchemy for `database.create_database`. 
- Further refactored `database.create_database`. 
- Default window sizes in `database.create_database` no longer includes 1. 
- Updated the gitignore file. 

#### Fixed
- Issue #45 (requires .db extension in `database.create_database`); Issue #46 (missing logger reference in helper function); Issue #47 (missing logs in the trees.py module); Issue #40 (incorrect numbers in `database.create_database` logs); Issue #50 (change `start` in enumeration statements for readability); Issue #41 (first part of migration to SQLAlchemy); Issue #37 (example SQL insertion error). 

## [v0.6.2](https://github.com/Luke-Poeppel/decitala/tree/v0.6.2) - February 5, 2021 (NYC)
#### Changed
- Refactored code in ``database.create_database`` to improve readability. 

## [v0.6.1](https://github.com/Luke-Poeppel/decitala/tree/v0.6.1) - February 3, 2021 (Kent, CT)
#### Fixed
- Fixed issue #35. Error with saving logs to file. 

#### Changed
- The trees module no longer logs results. This is a temporary change while I figure out a better solution for global/local logging. 

## [v0.6.0](https://github.com/Luke-Poeppel/decitala/tree/v0.6.0) - February 3, 2021 (Kent, CT)
#### Added
- Added the missing ``database.model_full_path`` function. 
- Documentation fixes for ``DBParser`` and ``fragments.py``. 
- Optional ``save_logs_to_file`` parameter to ``database.create_database``. 
- Can now create FragmentTrees from a list of multiple data paths. 
- Section in the documentation giving a brief exposition to the encoded rhythmic fragments. 

#### Changed
- Documentation now is in sphinx RTD theme. 
- Revamped README. 
- Rather than setting the same logger at the top of each file, added ``get_logger`` function to utils.py in which we can set optional filename to the basicConfig for saving to file when desired. 

#### Fixed
- Missing name argument in fragment trees created from ``frag_type``.

## [v0.5.2](https://github.com/Luke-Poeppel/decitala/tree/v0.5.2) - January 17, 2020 (Kent, CT)
#### Removed
- Codecov coverage status (because the service is terrible). 

## [v0.5.1](https://github.com/Luke-Poeppel/decitala/tree/v0.5.1) - January 17, 2020 (Kent, CT)
#### Added
- Added a function in database.py that filters out cross-corpus duplicates from the data generated in ``create_database`` (``database.remove_cross_corpus_duplicates``).

#### Changed
- Fragment Trees are now created with ``frag_types`` via the class method ``FragmentTree.from_frag_type``. (The logic in the ``__init__`` is now much cleaner.) 

#### Fixed
- Coverage results published on codecov.io (private upload token) with badge. 

## [v0.5.0](https://github.com/Luke-Poeppel/decitala/tree/v0.5.0) - January 16, 2020 (Kent, CT)
#### Added
- Added a ``create_fragment_database`` function in ``database.py`` that holds name/ql data & ratio/difference equivalents in the decitala and greek metric databases (including equivalents _across_ databases). This data is available in ``fragment_database.db`` in the databases directory. 
- Decitala and GreekFoot objects now have an ``equivalents`` method that return equivalents (based on the ``rep_type``) in the fragment corpus.
- Created a Travis-CI account for continuous integration. 
- Added a Codecov account for coverage.  
- Added build icons for travis-ci and codecov. 

#### Changed
- Decitala and Greek Metric instantiation now relies on SQL database instead of ``os.listdir``.
- FragmentTree instantiation now relies on SQL database instead of os.listdir.
- No doctests rely on absolute paths anymore. 

## [v0.4.4](https://github.com/Luke-Poeppel/decitala/tree/v0.4.0) - January 10, 2020 (Kent, CT)
#### Added
- The output of rolling search now has an id parameter. This will be useful in a number of contexts. **NOTE**: this may require some fiddling when dealing with combined databases. 

#### Changed
- Rewrote all the ``pofp.py`` code, making it far more readable. The duplicate error caused by contiguous summation should now be fixed. 

## [v0.4.3](https://github.com/Luke-Poeppel/decitala/tree/v0.4.3) - January 8, 2020 (Kent, CT)
#### Changed
- The DBParser now has ``metadata`` in the attributes, which stores the path table num, number of subpaths, and average onset data. That way, it needn't be reevalutaed every time we run the model. 

#### Fixed
- Fixed minor documentation errors.

#### Removed
- Removed all inheritence from ``object`` in classes (python3 classes are new-style). 

## [v0.4.2](https://github.com/Luke-Poeppel/decitala/tree/v0.4.2) - January 7, 2020 (Kent, CT)
#### Added
- Added fragment table visualization (``DBParser.show_fragments_table``) using pandas (wrapper for pd.read_sql_query). Also added a few other sub-displays (like ``show_slurred_fragments``). 
- Added preliminary native FragmentTree visualization. Can be called with ``FragmentTree.show()``. 
- Implemented first path processing/modeling methods for the ``database.DBParser`` class. Most of the ``paths.py`` code has moved there. 

#### Changed
- Fragments table from ``database.create_database`` has the name in the fragment column instead of full repr. 
- Output of ``get_pareto_optimal_longest_paths`` now includes all data, not just the fragment. 
- Cleaned up the path code in ``database.create_database``.
- The Paths tables in the database now store the row number in the ``onset_range`` columns. 
- The Path tables are no longer 0-indexed. 

#### Fixed
- The rolling search code now has a line that filters out all grace notes. This was causing the duplicates in the database creation.
- Minor documentation fixes (typos and old parameters).

#### Removed
- The ``paths.py`` file has been removed as all of its functionality has migrated to ``database.DBParser``.

## [v0.4.1](https://github.com/Luke-Poeppel/decitala/tree/v0.4.1) - January 4, 2020 (Kent, CT)
#### Fixed
- Bugfix for prime pitch contour calculation (cseg doesn't work on extrema data).
- Bugfix in database creation (missing comma). 

## [v0.4.0](https://github.com/Luke-Poeppel/decitala/tree/v0.4.0) - January 4, 2020 (Kent, CT)
#### Added
- Added ``utils.pitch_content_to_contour``. 
- Implementation of Morris' 1993 pitch contour reduction algorithm. ``utils.contour_to_prime_contour``. 
- Added ``Pitch_Contour`` column in the Fragment database. 

#### Changed
- The ``utils.roll_window`` function now allows for a ``fn`` input (allows for rolling window over parts of list, as defined by a lambda expression). 

## [v0.3.2](https://github.com/Luke-Poeppel/decitala/tree/v0.3.2) - January 1, 2020 (Kent, CT)
#### Added
- ``__all__`` for each module for ease-of-import. 
- Documentation for CLI (version getter and ``cli.create_db``).

#### Fixed
- Bugfix in ``utils.frame_is_spanned_by_slur``. Previously didn't take into account the fact that a range may have multiple overlapping spanners. 
- Removed old tree diagram information from cli. 

## [v0.3.1](https://github.com/Luke-Poeppel/decitala/tree/v0.3.1) - December 31, 2020 (Kent, CT)
#### Added
- Documentation page for ``vis.create_tree_diagram`` (Fragment Tree visualization using Treant.js.)
- Log message telling the user if a database has already been made (useful for working in Jupyter).

#### Fixed
- Incorrect output of ``pofp.partition_data_by_break_points`` caused by unsorted data from ``trees.rolling_search``.
- Documentation typo for ``utils.filter_single_anga_class_fragments``.

## [v0.3.0](https://github.com/Luke-Poeppel/decitala/tree/v0.3.0) - December 30, 2020 (Kent, CT)
#### Added
- Added preliminary ``database.DBParser`` class that allows for easier querying of data from the ``Fragment`` table of ``database.create_database``.

#### Changed
- The pitch information from rolling search is now stored in the Fragments table (made in ``database.create_database``).

#### Removed
- Helper functions ``database._check_tuple_in_tuple_range`` and ``database._pitch_info_from_onset_range`` are removed due to the above addition. 

## [v0.2.4](https://github.com/Luke-Poeppel/decitala/tree/v0.2.4) - December 30, 2020 (Kent, CT)
#### Fixed
- Bugfix in ``database.create_database`` (related to new rolling search output). 
- Bugfix in ``pofp.get_pareto_optimal_longest_paths`` (related to new rolling search output).

## [v0.2.3](https://github.com/Luke-Poeppel/decitala/tree/v0.2.3) - December 30, 2020 (Kent, CT)
#### Added 
- Added a ``utils.frame_to_midi`` option used in rolling search.
- Documentation updates reflecting the new rolling search output. 

#### Changed
- Output of ``trees.rolling_search`` is now a list of ``dict`` objects. This is better for querying data, adding extra parameters, etc...
- The ``trees.rolling_search`` function now stores pitch data using the ``utils.frame_to_midi``.
- Changed the input data parameter of ``utils.frame_to_ql_array`` from ``data`` to ``frame`` (matching the other functions).
- Made the ``utils.find_clusters`` function public. 

#### Removed
- Removed  ``trees.rolling_search_on_array`` (at least for now) as it doesn't currently match the other search formats.
- Removed ``utils.contiguous_multiplication``. 

## [v0.2.2](https://github.com/Luke-Poeppel/decitala/tree/v0.2.2) - December 29, 2020 (Kent, CT)
#### Added
- Added a .yaml file for a pre-commit hook that prevents writing to master. (Uses ``pre-commit`` library).

#### Changed
- Changed the name of ``utils.frame_is_spanned_by_slur`` (fixing a typo). 

#### Removed
- Removed unnecessary doctest imports from modules. 
- Removed old cleaning function for ``setup.py``.

## [v0.2.1](https://github.com/Luke-Poeppel/decitala/tree/v0.2.1) - December 29, 2020 (Kent, CT)
#### Changed
- The ``decitala.trees`` and ``decitala.database`` modules now use ``logging.disable`` (removing a number of if statements) for readability. (Also removed logging from ``decitala.pofp``.)

## [v0.2.0](https://github.com/Luke-Poeppel/decitala/tree/v0.2.0) - December 29, 2020 (Kent, CT)
#### Added
- The ``decitala.utils`` module now includes a ``frame_is_spanned_by_slur`` function.
- The output of ``trees.rolling_search`` now includes ``is_spanned_by_slur`` for each fragment found. 
- The output of ``database.create_database`` now shows which fragments are spanned by music21.spanner.Slur objects.

#### Fixed
- The ``database.create_database`` function now raises a ``DatabaseException`` when an invalid score path is provided. 

## [v0.1.1](https://github.com/Luke-Poeppel/decitala/tree/v0.1.1) - December 28, 2020 (Kent, CT)
- First tagged version.
- Documentation (made with sphinx, hosted on github pages) available at https://luke-poeppel.github.io/decitala/.