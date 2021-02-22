# Change Log
All important changes to the decitala package will be documented here.

The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v?]
### Changed
- Default window sizes in `database.create_database` no longer includes 1. 

### Removed
- Updated the gitignore file. 

### Fixed
- Issue #45: requires .db extension in `database.create_database`. 
- Issue #46: missing logger reference in helper function. 
- Issue #47: missing logs in the trees.py module. 

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