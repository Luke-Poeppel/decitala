# Change Log
All important changes to the decitala package will be documented here.

The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.9.1] ???
### Fixed
- Issues #102: empty numpy iterator for cases with no extracted fragments; #109: missing verbose argument in `search.path_finder`; #111: UnboundLocalError for Bach chorale –– this also resolves #101; #106: reformatted analysis JSON files to match the output of `search.path_finder` (every extraction is a dictionary). 

## [v0.9.0] April 14, 2021
### Added
- Function for annotating a score with the extracted data: ``vis.annotate_score``. 
- Added private ``remake_analysis_files.py`` for remaking the analysis files in each release. 
- Added testing to improve coverage (46%-50%). 
- Added various utility functions: `utils.measure_by_measure_time_signatures` (for for extracting measure-by-measure time signatures); `utils.is_octatonic_collection` (for checking if pitch content belongs to one of the two octatonic collections); `utils.write_analysis` (for writing analysis JSON files); `utils.net_ql_array` (for returning all quarter length values in a given composition as a vector); `utils.transform_to_time_scale` (for getting the time-scale notation of quarter length array).
- Added `PRIMES` variable to `utils.py` for storing primes <100. 
- Added `vis.result_bar_plot` for plotting the counts of the extracted fragments in a `path_finder` list or analysis JSON (#105).
- Added the first class of the `Theorie_Karnatique` dataset (Tiśra) to the `fragments` directory. These are not yet integrated into the `fragments` module.  

### Changed
- Improved ``fragment.py``'s ``FragmentEncoder`` and ``FragmentDecoder`` classes with better logic; this fixes #99: incorrect ``frag_type`` in the JSON encoding. 

### Fixed
- Missing import bug in ``vis.annotate_score``. 
- README: incorrect installation notes in README, improved translation to the commentary. 
- Issues #53: duplicates in logs caused by saved handlers; #100: `path_finder` bug related to `curr_best_sink`; 

## [v0.8.4] March 22, 2021
### Fixed
- Added the missing Zenodo badge to the README.md file.

## [v0.8.3] March 22, 2021
### Fixed
- Issue #90: removed unused JS modules used in tree visualization. 

## [v0.8.2] March 22, 2021
### Added
- Added a ``.coveragerc`` file for excluding the tests and CLI tools from coverage reports. 

### Changed
- Refactored ``get_path`` to include a ``reconstruct_standard_path`` helper function. 

### Fixed
- Additional bugfixes for slur constraint in ``get_path`` (causing infinite runtime). 
- Issues #19: referenced a fault Nary tree size. It appears to be fixed, but I added a test; #95: the ``pathfinder`` command line tool now writes to JSON; #94: minor formatting error in ``floyd_warshall.py``.

## [v0.8.1] March 20, 2021
### Added
- Coverage and coverage shield for code improvement. 

### Changed
- The CLI ``pathfinder`` tool now wraps the search.py module's ``path_finder`` function. 
- The ``create_tree_diagram`` now uses ``webshot`` from R to save to PNG. Can also now effectively do ``FragmentTree.show()`` without opening in the browser using the wand library. 

### Fixed
- Github Actions is now caching dependencies for faster builds.
- Fixed bugs in ``vis.create_tree_diagram``. 
- Bugfixes in ``path_finder`` related to ``is_spanned_by_slur`` attribute. 
- The ``utils.roll_window`` now ensures that no ``NoneTypes`` are included if the window size is greater than the input data. Similarly, in ``rolling_hash_search`` we ensure no searches of size greater than the length of the data. 
- Fixed missing Iambs in the GreekFoot hash table (#91). 
- The ``Decitala`` and ``GreekFoot`` classes included a ``stream`` attribute in their ``__init__`` –– this is already created in the ``super``.
- Hotfix to extremely strange inheritance bug in the ``GeneralFragment`` child classes. (#92)
- Bugfix in ``floyd_warshall.get_path``. Function was inserting the given starting point in the path, even if it was overrided by the slur constraint. 

## [v0.8.0] March 15, 2021
### Added
- Added a ``loader`` function in utils.py for easy loading of Messiaen's analyses (encoded by me). Also added additional analysis json files (including parts 0 & 1 of Livre d'Orgue (1951-52) movement V). 
- Added testing and improved functionality for the hash table creation and ``rolling_hash_search``. This included adding a ``GreekHashTable`` and ``CombinedHashTable`` for a combined database. 
- Added an optional progress bar to the Floyd-Warshall algorithm. 
- Added function for getting the best source and sink after Floyd-Warshall (``floyd_warshall.best_source_and_sink(data)``). 
- Added ``+/- 0.125, +/- 0.375, -0.25, 0.875, 1.75, 2.625, 3.5, 4.375`` as possible difference valuess in ``hash_table.py``; also added ``0.125, 0.25`` as a possible ratio values. 
- Added a ``path_finder`` command line tool that wraps all the functions for analysis via Floyd-Warshall & the hash tables. Used simply as ``decitala path-finder --filepath ... --part_num ... --frag_type ...``. 
- Added a ``ignore_single_anga_class_fragments`` parameter to ``rolling_hash_search`` (default is False). 
- Added optional ``slur_constraint`` parameter to ``floyd_warshall.best_path`` which constrains the path to require the slurred fragments found (#87). 

### Removed
- Removed the ``self.conn`` attribute in the ``Decitala`` class; in doing so, we can now use multiprocessing (multiprocessing requires pickling which is impossible on sqlite3 ``Connection`` objects). 

### Fixed
- Missing modification data in ``rolling_hash_search``. 

## [v0.7.4] March 8, 2021 (Kent)
### Fixed
- Finished applying flake8 to modules. 
- Fixed #83 (missing modules in setup.py)

## [v0.7.3] March 8, 2021 (Kent)
### Fixed
- Re-gitignored ``local_docs``. 

## [v0.7.2] March 8, 2021 (Kent)
### Fixed
- Missing modifications types ``rr``, ``rd``, ``sr``, and ``rsr`` in ``DecitalaHashTable``. Refactored and clean up the instantiation code –– still requires work for Greek metrics and General fragments. 
- Applied flake8 to vis.py.
- JSON Serialization/Deserialization errors for ``GeneralFragment`` and its inherited classes. This makes saving "training data" easier. (This step is for the next minor patch.)
- The ``local_docs`` directory (this was previously gitignored for no good reason). Also an analyses directory of databases holding valid analysis of compositions. 

## [v0.7.1] March 3, 2021 (NYC)
### Fixed
- In enabling github actions, I hit several git/github snags. There were some commit message errors and bad merges. Hopefully everything is fixed now. 

## [v0.7.0] March 3, 2021 (NYC)
### Added
- Implemented the Floyd-Warshall Algorithm for path-finding. 
- Added a ``hash_table.py`` module for more efficient searching. This is  used in ``search.rolling_hash_search``.
- Added flake8 for maintaining PEP8 standards. Applied to setup.py, fragment.py, and utils.py. 
- Added a `fragment_roll` function to `vis.py` (#62). 
- Added a progress bar to `DBParser.model_full_path` to more easily track progress. 
- Added a `DBParser.onset_ranges` method that returns a list of tuples holding the onset ranges of all extracted fragments.
- Added a `return_data` parameter to `model_full_path` (just a wrapper for `path_data`). 
- Added an MIT License

### Changed
- The ``trees.py`` module has been refactored into ``trees.py`` and ``search.py`` with the relevant search functions in the latter module. (#27)

### Fixed
- Issue #54 (unreferenced variable); Issue #51 (updated databases); Issue #58 (unfiltered fragment table); 

## [v0.6.3] February 23, 2021 (NYC)
### Added
- Added support/testing for python3.8. 

### Changed
- Migrated to SQLAlchemy for `database.create_database`. 
- Further refactored `database.create_database`. 
- Default window sizes in `database.create_database` no longer includes 1. 
- Updated the gitignore file. 

### Fixed
- Issue #45 (requires .db extension in `database.create_database`); Issue #46 (missing logger reference in helper function); Issue #47 (missing logs in the trees.py module); Issue #40 (incorrect numbers in `database.create_database` logs); Issue #50 (change `start` in enumeration statements for readability); Issue #41 (first part of migration to SQLAlchemy); Issue #37 (example SQL insertion error). 

## [v0.6.2] - February 5, 2021 (NYC)
### Changed
- Refactored code in ``database.create_database`` to improve readability. 

## [v0.6.1] - February 3, 2021 (Kent, CT)
### Fixed
- Fixed issue #35. Error with saving logs to file. 

### Changed
- The trees module no longer logs results. This is a temporary change while I figure out a better solution for global/local logging. 

## [v0.6.0] - February 3, 2021 (Kent, CT)
### Added
- Added the missing ``database.model_full_path`` function. 
- Documentation fixes for ``DBParser`` and ``fragments.py``. 
- Optional ``save_logs_to_file`` parameter to ``database.create_database``. 
- Can now create FragmentTrees from a list of multiple data paths. 
- Section in the documentation giving a brief exposition to the encoded rhythmic fragments. 

### Changed
- Documentation now is in sphinx RTD theme. 
- Revamped README. 
- Rather than setting the same logger at the top of each file, added ``get_logger`` function to utils.py in which we can set optional filename to the basicConfig for saving to file when desired. 

### Fixed
- Missing name argument in fragment trees created from ``frag_type``.

## [v0.5.2] - January 17, 2020 (Kent, CT)
### Removed
- Codecov coverage status (because the service is terrible). 

## [v0.5.1] - January 17, 2020 (Kent, CT)
### Added
- Added a function in database.py that filters out cross-corpus duplicates from the data generated in ``create_database`` (``database.remove_cross_corpus_duplicates``).

### Changed
- Fragment Trees are now created with ``frag_types`` via the class method ``FragmentTree.from_frag_type``. (The logic in the ``__init__`` is now much cleaner.) 

### Fixed
- Coverage results published on codecov.io (private upload token) with badge. 

## [v0.5.0] - January 16, 2020 (Kent, CT)
### Added
- Added a ``create_fragment_database`` function in ``database.py`` that holds name/ql data & ratio/difference equivalents in the decitala and greek metric databases (including equivalents _across_ databases). This data is available in ``fragment_database.db`` in the databases directory. 
- Decitala and GreekFoot objects now have an ``equivalents`` method that return equivalents (based on the ``rep_type``) in the fragment corpus.
- Created a Travis-CI account for continuous integration. 
- Added a Codecov account for coverage.  
- Added build icons for travis-ci and codecov. 

### Changed
- Decitala and Greek Metric instantiation now relies on SQL database instead of ``os.listdir``.
- FragmentTree instantiation now relies on SQL database instead of os.listdir.
- No doctests rely on absolute paths anymore. 

## [v0.4.4] - January 10, 2020 (Kent, CT)
### Added
- The output of rolling search now has an id parameter. This will be useful in a number of contexts. **NOTE**: this may require some fiddling when dealing with combined databases. 

### Changed
- Rewrote all the ``pofp.py`` code, making it far more readable. The duplicate error caused by contiguous summation should now be fixed. 

## [v0.4.3] - January 8, 2020 (Kent, CT)
### Changed
- The DBParser now has ``metadata`` in the attributes, which stores the path table num, number of subpaths, and average onset data. That way, it needn't be reevalutaed every time we run the model. 

### Fixed
- Fixed minor documentation errors.

### Removed
- Removed all inheritence from ``object`` in classes (python3 classes are new-style). 

## [v0.4.2] - January 7, 2020 (Kent, CT)
### Added
- Added fragment table visualization (``DBParser.show_fragments_table``) using pandas (wrapper for pd.read_sql_query). Also added a few other sub-displays (like ``show_slurred_fragments``). 
- Added preliminary native FragmentTree visualization. Can be called with ``FragmentTree.show()``. 
- Implemented first path processing/modeling methods for the ``database.DBParser`` class. Most of the ``paths.py`` code has moved there. 

### Changed
- Fragments table from ``database.create_database`` has the name in the fragment column instead of full repr. 
- Output of ``get_pareto_optimal_longest_paths`` now includes all data, not just the fragment. 
- Cleaned up the path code in ``database.create_database``.
- The Paths tables in the database now store the row number in the ``onset_range`` columns. 
- The Path tables are no longer 0-indexed. 

### Fixed
- The rolling search code now has a line that filters out all grace notes. This was causing the duplicates in the database creation.
- Minor documentation fixes (typos and old parameters).

### Removed
- The ``paths.py`` file has been removed as all of its functionality has migrated to ``database.DBParser``.

## [v0.4.1] - January 4, 2020 (Kent, CT)
### Fixed
- Bugfix for prime pitch contour calculation (cseg doesn't work on extrema data).
- Bugfix in database creation (missing comma). 

## [v0.4.0] - January 4, 2020 (Kent, CT)
### Added
- Added ``utils.pitch_content_to_contour``. 
- Implementation of Morris' 1993 pitch contour reduction algorithm. ``utils.contour_to_prime_contour``. 
- Added ``Pitch_Contour`` column in the Fragment database. 

### Changed
- The ``utils.roll_window`` function now allows for a ``fn`` input (allows for rolling window over parts of list, as defined by a lambda expression). 

## [v0.3.2] - January 1, 2020 (Kent, CT)
### Added
- ``__all__`` for each module for ease-of-import. 
- Documentation for CLI (version getter and ``cli.create_db``).

### Fixed
- Bugfix in ``utils.frame_is_spanned_by_slur``. Previously didn't take into account the fact that a range may have multiple overlapping spanners. 
- Removed old tree diagram information from cli. 

## [v0.3.1] - December 31, 2020 (Kent, CT)
### Added
- Documentation page for ``vis.create_tree_diagram`` (Fragment Tree visualization using Treant.js.)
- Log message telling the user if a database has already been made (useful for working in Jupyter).

### Fixed
- Incorrect output of ``pofp.partition_data_by_break_points`` caused by unsorted data from ``trees.rolling_search``.
- Documentation typo for ``utils.filter_single_anga_class_fragments``.

## [v0.3.0] - December 30, 2020 (Kent, CT)
### Added
- Added preliminary ``database.DBParser`` class that allows for easier querying of data from the ``Fragment`` table of ``database.create_database``.

### Changed
- The pitch information from rolling search is now stored in the Fragments table (made in ``database.create_database``).

### Removed
- Helper functions ``database._check_tuple_in_tuple_range`` and ``database._pitch_info_from_onset_range`` are removed due to the above addition. 

## [v0.2.4] - December 30, 2020 (Kent, CT)
### Fixed
- Bugfix in ``database.create_database`` (related to new rolling search output). 
- Bugfix in ``pofp.get_pareto_optimal_longest_paths`` (related to new rolling search output).

## [v0.2.3] - December 30, 2020 (Kent, CT)
### Added 
- Added a ``utils.frame_to_midi`` option used in rolling search.
- Documentation updates reflecting the new rolling search output. 

### Changed
- Output of ``trees.rolling_search`` is now a list of ``dict`` objects. This is better for querying data, adding extra parameters, etc...
- The ``trees.rolling_search`` function now stores pitch data using the ``utils.frame_to_midi``.
- Changed the input data parameter of ``utils.frame_to_ql_array`` from ``data`` to ``frame`` (matching the other functions).
- Made the ``utils.find_clusters`` function public. 

### Removed
- Removed  ``trees.rolling_search_on_array`` (at least for now) as it doesn't currently match the other search formats.
- Removed ``utils.contiguous_multiplication``. 

## [v0.2.2] - December 29, 2020 (Kent, CT)
### Added
- Added a .yaml file for a pre-commit hook that prevents writing to master. (Uses ``pre-commit`` library).

### Changed
- Changed the name of ``utils.frame_is_spanned_by_slur`` (fixing a typo). 

### Removed
- Removed unnecessary doctest imports from modules. 
- Removed old cleaning function for ``setup.py``.

## [v0.2.1] - December 29, 2020 (Kent, CT)
### Changed
- The ``decitala.trees`` and ``decitala.database`` modules now use ``logging.disable`` (removing a number of if statements) for readability. (Also removed logging from ``decitala.pofp``.)

## [v0.2.0] - December 29, 2020 (Kent, CT)
### Added
- The ``decitala.utils`` module now includes a ``frame_is_spanned_by_slur`` function.
- The output of ``trees.rolling_search`` now includes ``is_spanned_by_slur`` for each fragment found. 
- The output of ``database.create_database`` now shows which fragments are spanned by music21.spanner.Slur objects.

### Fixed
- The ``database.create_database`` function now raises a ``DatabaseException`` when an invalid score path is provided. 

## [v0.1.1] - December 28, 2020 (Kent, CT)
- First tagged version.
- Documentation (made with sphinx, hosted on github pages) available at https://luke-poeppel.github.io/decitala/.