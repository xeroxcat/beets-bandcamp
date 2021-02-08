## [0.5.6] 2021-02-08

### Fixed

- Bandcamp updated their html format which broke track duration parsing. This is now fixed
  and test html files are updated.

- Fixed track name parser which would incorrectly parse a track name like `24 hours`,
  ignoring the numbers from the beginning of the string.

- Locations that have non-ascii characters in their names would not be identified
  (something like _Montreal, Québec_) - now the characters are converted and
  `pycountry` does understand them.

- Fixed an edge case where an EP would be incorrectly misidentified as an album.

### Updated

- Catalogue number parser now requires at least two digits to find a good match.


## [0.5.5] 2021-01-30

### Updated

- Country name overrides for _Russia_ and _The Netherlands_ which deviate from the
  official names.
- Track names:
  - If _digital_ and _exclusive_ are found in the name, it means it's digital-only.
  - Artist / track splitting logic now won't split them on the dash if it doesn't have
    spaces on both sides.
  * `track_alt` field may now contain numerical values if track names start with them.
    Previously, only vinyl format was supported with the `A1` / `B2` notation.

## [0.5.4] 2021-01-25

### Added

- Previously skipped, not-yet-released albums are now handled appropriately. In such
  cases, `albumstatus` gets set to **Promotional**, and the release date will be a future
  date instead of past.

### Fixed

- Handle a sold-out release where the track listing isn't available, which would otherwise
  cause a KeyError.

- Catalogue number parser should now forget that cassette types like **C30** or **C90**
  could be valid catalogue numbers.

### Updated

- Brought dev dependencies up-to-date.

## [0.5.3] 2021-01-19

### Fixed

- For data that is parsed directly from the html, ampersands are now correctly
  unescaped.

## [0.5.2] 2021-01-18

### Fixed

- On Bandcamp merch is listed in the same list together with media - this is now
  taken into account and merch is ignored. Previously, some albums would fail to
  be returned because of this.

## [0.5.1] 2021-01-18

### Fixed

- Fixed readme headings where configuration options were shown in capitals on `PyPI`.

## [0.5.0] 2021-01-18

### Added

- Added some functionality to exclude digital-only tracks for media that aren't
  _Digital Media_. A new configuration option `include_digital_only_tracks`, if
  set to `True` will include all tracks regardless of the media, and if set to
  `False`, will mind, for example, a _Vinyl_ media and exclude tracks that
  have some sort of _digital only_ flag in their names, like `DIGI`, `[Digital Bonus]`,
  `[Digital Only]` and alike. These flags are also cleared from the
  track names.

### Fixed

- For LP Vinyls, the disc count and album type are now corrected.

## [0.4.4] 2021-01-17

### Fixed

- `release_date` search pattern now looks for a specific date format, guarding
  it against similar matches that could be found in the description, thanks
  @noahsager.

## [0.4.3] 2021-01-17

### Fixed

- Handled a `KeyError` that would come up when looking for an album/track where
  the block describing available media isn't found. Thanks @noahsager.

### Changed

- Info logs are now `DEBUG` logs so that they're not printed without the verbose
  mode, thanks @arogl.

## [0.4.2] 2021-01-17

### Fixed

- `catalognum` parser used to parse `Vol.30` or `Christmas 2020` as catalogue
  number - these are now excluded. It's likely that additional patterns will
  come up later.

### Added

- Added the changelog.

## [0.4.1] 2021-01-16

### Fixed

- Fixed installation instructions in the readme.

## [0.4.0] 2021-01-16

### Added

- The pipeline now uses generators, therefore the plug-in searches until it
  finds a good fit and won't continue further (same as the musicbrainz autotagger)
- Extended the parsing functionality with data like catalogue number, label,
  country etc. The full list is given in the readme.
