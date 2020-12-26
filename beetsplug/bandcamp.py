# Copyright (C) 2015 Ariel George
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; version 2.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""Adds bandcamp album search support to the autotagger."""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import logging
import re
from datetime import date, datetime
from math import floor
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

import beets
import beets.ui
import requests
import six
from beets import plugins
from beets.autotag.hooks import AlbumInfo, Distance, TrackInfo

from beetsplug import fetchart  # type: ignore[attr-defined]

DEFAULT_CONFIG = {
    "source_weight": 0.5,
    "min_candidates": 5,
    "max_candidates": 5,
    "lyrics": False,
    "art": False,
    "split_artist_title": False,
}

SEARCH_URL = "https://bandcamp.com/search?q={query}&page={page}"
SEARCH_ITEM_PAT = r'href="(https://[^/]*/{query}/[^?]*)'
USER_AGENT = "beets/{0} +http://beets.radbox.org/".format(beets.__version__)
ALBUM = "album"
ARTIST = "band"
TRACK = "track"

COUNTRY = "XW"
MEDIA = "Digital Media"
DATA_SOURCE = "bandcamp"

META_BLOCK_PAT = r".*datePublished.*"
META_LYRICS_PAT = r'"lyrics":({[^}]*})'
META_LABEL_PAT = r'og:site_name".*content="([^"]*)"'
META_RELEASE_DATE_PAT = r" released (.*)"
META_DATE_FORMAT = "%d %B %Y"

TRACK_SPLIT = "-"

JSONDict = Dict[str, Any]


class Metaguru:
    COMMON = {"data_source": DATA_SOURCE, "media": MEDIA}

    _image = None  # type: str
    _lyrics = ""  # type: Optional[str]
    _raw_tracks = None  # type: List[JSONDict]
    _type = None  # type: str

    html: str
    meta: JSONDict

    def __init__(self, html: str) -> None:
        self.html = html
        match = re.search(META_BLOCK_PAT, html, flags=re.MULTILINE)
        if match:
            self.meta = json.loads(match.group())

    @property
    def type(self) -> Optional[str]:
        """Could be `MusicRecording`, `Product`, `MusicAlbum`."""
        if self._type:
            return self._type

        _type = self.meta["@type"]
        self._type = ", ".join(_type) if isinstance(_type, list) else _type

        return self._type

    @property
    def label(self) -> Optional[str]:
        match = re.search(META_LABEL_PAT, self.html)
        if match:
            return match.groups()[0]
        else:
            return None

    @property
    def image(self) -> Optional[str]:
        _image = self.meta["image"]
        self._image = ", ".join(_image) if isinstance(_image, list) else _image

        return self._image

    @property
    def url(self) -> str:
        return self.meta["@id"]

    @property
    def album(self) -> str:
        return self.meta["name"]

    @property
    def album_artist(self) -> str:
        return self.meta["byArtist"]["name"]

    @property
    def release_date(self) -> Optional[date]:
        match = re.search(META_RELEASE_DATE_PAT, self.html)
        if match:
            return datetime.strptime(match.groups()[0], META_DATE_FORMAT).date()
        return None

    @property
    def raw_tracks(self) -> List[JSONDict]:
        if self._raw_tracks is None:
            self._raw_tracks = [i["item"] for i in self.meta["track"]["itemListElement"]]

        return self._raw_tracks

    @property
    def lyrics(self) -> Optional[str]:
        if self._lyrics or self._lyrics is None:
            return self._lyrics

        lyrics_matches = re.findall(META_LYRICS_PAT, self.html)
        lyrics = []
        for match in lyrics_matches:
            lyrics.append(json.loads(match)["text"])
            self._lyrics = "\n\n".join(lyrics)
        else:
            self._lyrics = None

        return self._lyrics

    @property
    def standalone_trackinfo(self) -> TrackInfo:
        if self.type and "MusicAlbum" in self.type:
            return None

        return TrackInfo(
            self.album,
            self.url,
            length=floor(self.meta["duration_secs"]),
            artist=self.album_artist,
            artist_id=self.url,
            data_url=self.url,
            **self.COMMON,
        )

    def _trackinfo(self, track: JSONDict, index: int) -> TrackInfo:
        # TODO: Check for VA too
        artist = self.album_artist
        title = track["name"]
        if TRACK_SPLIT in title:
            artist, title = [s.strip() for s in title.split(TRACK_SPLIT, maxsplit=1)]

        return TrackInfo(
            title,
            track["url"],
            index=index,
            length=floor(track["duration_secs"]),
            data_url=track["url"],
            artist=artist,
        )

    @property
    def tracks(self) -> List[TrackInfo]:
        return [
            self._trackinfo(track, idx) for idx, track in enumerate(self.raw_tracks, 1)
        ]

    @property
    def albuminfo(self) -> AlbumInfo:
        return AlbumInfo(
            self.album,
            self.url,
            self.album_artist,
            self.url,
            self.tracks,
            year=self.release_date.year if self.release_date else None,
            month=self.release_date.month if self.release_date else None,
            day=self.release_date.day if self.release_date else None,
            label=self.label,
            country=COUNTRY,
            data_url=self.url,
            **self.COMMON,
        )


class RequestsHandler:
    """A class that provides an ability to make requests and handles failures."""

    _log = logging.Logger

    def _report(self, msg, e=None, url=None, level=logging.DEBUG):
        # type: (str, Optional[Exception], Optional[str], int) -> None
        self._log.log(level, f"{msg} {url!r}: {e}")  # type: ignore[call-arg, arg-type]

    def _get(self, url: str) -> Optional[str]:
        """Returns a BeautifulSoup object with the contents of url."""
        headers = {"User-Agent": USER_AGENT}
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            self._report("Communication error while fetching album", e, url)
            return None
        return r.content.decode()


class BandcampAlbumArt(RequestsHandler, fetchart.RemoteArtSource):
    NAME = "Bandcamp"

    def get(self, album: AlbumInfo, *args: Tuple[Any]) -> Optional[Iterator[str]]:
        """Return the url for the cover from the bandcamp album page.
        This only returns cover art urls for bandcamp albums (by id).
        """
        url = album.mb_albumid
        if not isinstance(url, six.string_types) or DATA_SOURCE not in url:
            return None

        html = self._get(url)
        if not html:
            return None
        try:
            image_url = Metaguru(html).image
            yield self._candidate(url=image_url, match=fetchart.Candidate.MATCH_EXACT)
        except ValueError as e:
            self._report("Unexpected html error fetching bandcamp album art: ", e)
            return None


class BandcampPlugin(RequestsHandler, plugins.BeetsPlugin):
    def __init__(self) -> None:
        super(BandcampPlugin, self).__init__()
        self.config.add(DEFAULT_CONFIG)
        self.import_stages = [self.imported]
        self.register_listener("pluginload", self.loaded)

    def _from_bandcamp(self, item: Any) -> bool:
        return hasattr(item, "data_source") and item.data_source == DATA_SOURCE

    def add_lyrics(self, item: Any, write: bool = False) -> None:
        """Fetch and store lyrics for a single item. If ``write``, then the
        lyrics will also be written to the file itself."""
        if item.lyrics:
            self._report("lyrics already present: {0}", item, level=logging.INFO)
            return None

        html = self._get(item.mb_trackid)
        if not html:
            return None

        lyrics = Metaguru(html).lyrics
        if not lyrics:
            self._report("lyrics not found: {0}", item, level=logging.INFO)
            return None

        self._report("fetched lyrics: {0}", item, level=logging.INFO)
        item.lyrics = lyrics
        if write:
            item.try_write()
        item.store()

    def imported(self, _: Any, task: Any) -> None:
        """Import hook for fetching lyrics from bandcamp automatically."""
        if self.config["lyrics"]:
            for item in task.imported_items():
                # Only fetch lyrics for items from bandcamp
                if self._from_bandcamp(item):
                    self.add_lyrics(item, True)

    def loaded(self) -> None:
        """Add our own artsource to the fetchart plugin."""
        # FIXME: This is ugly, but i didn't find another way to extend fetchart
        # without declaring a new plugin.
        if self.config["art"]:
            for plugin in plugins.find_plugins():
                if isinstance(plugin, fetchart.FetchArtPlugin):
                    plugin.sources = [
                        BandcampAlbumArt(plugin._log, self.config)
                    ] + plugin.sources
                    fetchart.ART_SOURCES[DATA_SOURCE] = BandcampAlbumArt
                    fetchart.SOURCE_NAMES[BandcampAlbumArt] = DATA_SOURCE
                    break

    def album_distance(self, items: List[Any], album_info: AlbumInfo, _: Any) -> Distance:
        """Return the album distance."""
        dist = Distance()

        if self._from_bandcamp(album_info):
            dist.add("source", self.config["source_weight"].as_number())
        return dist

    def candidates(self, items, artist, album, va_likely):
        # type: (List[Any], str, str, bool) -> List[AlbumInfo]
        """Return a list of albums given a search query."""
        return [
            album
            for album in (self.get_album_info(url) for url in self._search(album, ALBUM))
            if album
        ]

    def item_candidates(self, item, artist, album):
        # type: (TrackInfo, str, str) -> List[TrackInfo]
        """Return a list of tracks from a bandcamp search matching a singleton."""
        query = item.title or item.album or item.artist
        return [
            track
            for track in (self.get_track_info(url) for url in self._search(query, TRACK))
            if track
        ]

    def album_for_id(self, album_id: str) -> Optional[AlbumInfo]:
        """Fetch an album by its bandcamp ID and return it if found."""
        return self.get_album_info(album_id)

    def track_for_id(self, track_id: str) -> Optional[TrackInfo]:
        """Fetch a track by its bandcamp ID and return it if found."""
        return self.get_track_info(track_id)

    def get_album_info(self, url: str) -> Optional[AlbumInfo]:
        """Return an AlbumInfo object for a bandcamp album page."""
        html = self._get(url)
        return Metaguru(html).albuminfo if html else None

    def get_track_info(self, url: str) -> Optional[TrackInfo]:
        """Returns a TrackInfo object for a bandcamp track page."""
        html = self._get(url)
        return Metaguru(html).standalone_trackinfo if html else None

    def _search(self, query, search_type=ALBUM, page=1):
        # type: (str, str, int) -> List[str]
        """Return a list of URLs for items of type search_type matching the query."""
        urls: Set[str] = set()

        while len(urls) < self.config["min_candidates"].as_number():
            self._report(f"Searching {search_type}, page {page}")
            html = self._get(SEARCH_URL.format(query=query, page=page))
            if not html:
                continue

            matches = re.findall(SEARCH_ITEM_PAT.format(query), html)
            for match in matches:
                urls.add(match)
                if len(urls) == self.config["max_candidates"]:
                    break

            # Stop searching if we are on the last page.
            if not re.search(rf"page={page}", html):
                break
            page += 1

        return list(urls)
