# Change Log
All important changes to the decitala package will be documented here.

The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.2.3] - December 30, 2020 (Kent, CT)
### Added 
- Added a ``utils.frame_to_midi`` option used in rolling search.

### Changed
- Output of ``trees.rolling_search`` is now a list of ``dict`` objects. This is better for querying data, adding extra parameters, etc...
- The ``trees.rolling_search`` function now stores pitch data using the ``utils.frame_to_midi``.
- Changed the input data parameter of ``utils.frame_to_ql_array`` from ``data`` to ``frame`` (matching the other functions).

### Removed
- Helper functions ``database._check_tuple_in_tuple_range`` and ``database._pitch_info_from_onset_range`` are removed due to the above addition. 

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