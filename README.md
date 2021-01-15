<!-- vim-markdown-toc GFM -->

* [Installation](#installation)
* [Configuration](#configuration)
* [Usage](#usage)

<!-- vim-markdown-toc -->

[![image](http://img.shields.io/pypi/v/beetcamp.svg)](https://pypi.python.org/pypi/beetcamp)

Plug-in for [beets](https://github.com/beetbox/beets) to use Bandcamp as
an autotagger source.

This is an up-to-date fork of [unrblt/beets-bandcamp](https://github.com/unrblt/beets-bandcamp)

# Installation

Install this plug-in with

```bash
   pip install .
```

from within this folder (it's not available on PyPI just yet)


and add `bandcamp` to the `plugins` list in your beets config file.

# Configuration

-   **search_max** (Default: `10`). Maximum number of results to be fetched from
    the search query. Depending on the specificity of the query and whether a
    suitable match is found, it could fetch 50+ results which may take a minute,
    so it'd make sense to bound this to some sort of sensible number.
-   **lyrics** (Default: `false`). Add lyrics to the tracks if they are available.
-   **art** (Default: `false`). Add a source to the
    [FetchArt](http://beets.readthedocs.org/en/latest/plugins/fetchart.html)
    plug-in to download album art for Bandcamp albums (requires `FetchArt` plug-in
    enabled as well).

# Usage

This plug-in uses the Bandcamp URL as id (for both albums and songs). If
no matching release is found when importing you can select `enter Id`
and paste the Bandcamp URL.
