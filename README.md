[![image](http://img.shields.io/pypi/v/beetcamp.svg)](https://pypi.python.org/pypi/beetcamp)

Plug-in for [beets](https://github.com/beetbox/beets) to use Bandcamp as
an autotagger source.

This is an up-to-date fork of [unrblt/beets-bandcamp](https://github.com/unrblt/beets-bandcamp)

# Installation

Navigate to your `beets` virtual environment, install the plug-in with

```bash
   pip install --user beetcamp
```

and add `bandcamp` to the `plugins` list to your beets configuration file.


# Configuration

#### `preferred_media`

- Default: `Digital`
- available: `Vinyl`, `CD`, `Cassette`, `Digital`.

A comma-separated list of media to prioritise when
fetching albums. For example: `preferred_media: Vinyl,Cassette`
will ignore `CD`, check for a `Vinyl`, and then for a `Cassette`, in the end
defaulting to `Digital` (always available) if none of the two are found.

#### `include_digital_only_tracks`

- Default: `True`

For media that isn't `Digital Media`, include all tracks, even if their titles
contain **digital only** (or alike).

If you have `False` here, then, for example, a `Vinyl` media of an album will
only include the tracks that are supposed to be found in that media.

#### `search_max`

- Default: `10`.

Maximum number of items to fetch through search queries. Depending on the
specificity of queries and whether a suitable match is found, it could
fetch 50+ results which may take a minute, so it'd make sense to bound
this to some sort of sensible number. Usually, a match is found among the first 5 items.

#### `lyrics`

- Default: `false`.

Add lyrics to the tracks if they are available.

#### `art`

- Default: `false`.

Add a source to the [FetchArt](http://beets.readthedocs.org/en/latest/plugins/fetchart.html)
plug-in to download album art for Bandcamp albums (requires `FetchArt` plug-in enabled).

# Usage

This plug-in uses the Bandcamp URL as id (for both albums and songs). If no matching
release is found when importing you can select `enter Id` and paste the Bandcamp URL.

## Currently supported / returned data

| field            | singleton track | album track | album |
|-----------------:|:---------------:|:-----------:|:-----:|
| `album`          |                 |             | ✔     |
| `album_id`       |                 |             | ✔     |
| `albumartist`    | ✔               | ✔           | ✔     |
| `albumstatus`    |                 |             | ✔     |
| `albumtype`      |                 |             | ✔     |
| `artist`         | ✔               | ✔           | ✔     |
| `artist_id`      | ✔               | ✔           |       |
| `catalognum`     |                 |             | ✔     |
| `country`        |                 |             | ✔     |
| `day`            |                 |             | ✔     |
| `disctitle`      |                 | ✔           |       |
| `image`          |                 | ✔           | ✔     |
| `index`          |                 | ✔           |       |
| `label`          |                 | ✔           | ✔     |
| `length`         | ✔               | ✔           |       |
| `lyrics`         |                 | ✔           |       |
| `media`          |                 | ✔           | ✔     |
| `medium`         |                 | ✔           |       |
| `mediums`        |                 |             | ✔     |
| * `medium_index` |                 | ✔           |       |
| * `medium_total` |                 | ✔           |       |
| `month`          |                 |             | ✔     |
| `title`          | ✔               | ✔           |       |
| `track_alt`      | ✔               | ✔           |       |
| `va`             |                 |             | ✔     |
| `year`           |                 |             | ✔     |

* \* are likely to be inaccurate, since Bandcamp does not provide this data,
  therefore they depend on artists providing some clues in the descriptions of
  their releases. This is only relevant if you have `per_disc_numbering` set to
  `True` in the global beets configuration.
