# Change Log
All important changes to the decitala package will be documented here.

The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.4.0] - January 2, 2020 (Kent, CT)
### Added
- Added ``utils.pitch_content_to_contour``. 
- Added Pitch_Contour column in the Fragment database. 
- Prime Contour (using Morris' 1993 algorithm) implemented; now are columns in the db tables.

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