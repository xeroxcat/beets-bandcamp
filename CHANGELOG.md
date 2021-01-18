# [0.5.1] 2021-01-18

### Fixed
- Fixed readme headings where configuration options were shown in capitals on `PyPI`.


# [0.5.0] 2021-01-18

### Added
- Added some functionality to exclude digital-only tracks for media that aren't
  _Digital Media_. A new configuration option `include_digital_only_tracks`, if
  set to `True` will include all tracks regardless of the media, and if set to
  `False`, will mind, for example, a _Vinyl_ media and exclude tracks that
  have some sort of _digital only_ flag in their names, like `DIGI`, `[Digital
  Bonus]`, `[Digital Only]` and alike. These flags are also cleared from the
  track names.

### Fixed
- For LP Vinyls, the disc count and album type are now corrected.


# [0.4.4] 2021-01-17

### Fixed
- `release_date` search pattern now looks for a specific date format, guarding
  it against similar matches that could be found in the description, thanks
  @noahsager.


# [0.4.3] 2021-01-17

### Fixed
- Handled a `KeyError` that would come up when looking for an album/track where
  the block describing available media isn't found. Thanks @noahsager.

### Changed
- Info logs are now `DEBUG` logs so that they're not printed without the verbose
  mode, thanks @arogl.


# [0.4.2] 2021-01-17

### Fixed
- `catalognum` parser used to parse `Vol.30` or `Christmas 2020` as catalogue
  number - these are now excluded. It's likely that additional patterns will
  come up later.

### Added
- Added the changelog.


# [0.4.1] 2021-01-16

### Fixed
- Fixed installation instructions in the readme.


# [0.4.0] 2021-01-16

### Added
- The pipeline now uses generators, therefore the plug-in searches until it
  finds a good fit and won't continue further (same as the musicbrainz autotagger)
- Extended the parsing functionality with data like catalogue number, label,
  country etc. The full list is given in the readme.
