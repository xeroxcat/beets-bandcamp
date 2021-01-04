.. image:: http://img.shields.io/pypi/v/beets-bandcamp.svg
    :target: https://pypi.python.org/pypi/beets-bandcamp

Plugin for `beets <https://github.com/beetbox/beets>`_ to use bandcamp as an
autotagger source.

Installation
------------

Install this plugin with

..

   $ pip install beets-bandcamp

and add ``bandcamp`` to the ``plugins`` list in your beets config file.

Configuration
-------------

*
  **min_candidates** (Default: ``6``). How many candidates to fetch through the search.

*
  **preferred_media** (Default: ``Digital Media``). When fetching albums or tracks *by their ids*,
  this will be preferred. Can be ``Cassette``, ``CD``, ``Vinyl`` and ``Digital Media``. It defaults
  to the latter if your preferred media isn't available.

*
  **lyrics** (Default: ``false``). Add lyrics to the tracks if they are available.

*
  **art** (Default: ``false``). Add a source to the `FetchArt <http://beets.readthedocs.org/en/latest/plugins/fetchart.html>`_
  plugin to download album art for bandcamp albums (requires ``FetchArt`` plugin enabled as well).

Usage
-----

This plugin uses the bandcamp URL as id (for both albums and songs). If no
matching release is found when importing you can select ``enter Id`` and paste
the bandcamp URL.
