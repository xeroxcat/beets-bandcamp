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

"""Adds bandcamp album search support to the autotagger. Requires the
BeautifulSoup library.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import logging
import re
from datetime import date, datetime
from functools import partial
from html import unescape
from math import floor
from typing import Any, Dict, Iterator, List, MutableMapping, Optional, Tuple

import beets
import beets.ui
import requests
import six
from beets import plugins
from beets.autotag.hooks import AlbumInfo, Distance, TrackInfo
from bs4 import BeautifulSoup

from beetsplug import fetchart  # type: ignore[attr-defined]

DEFAULT_CONFIG = {
    "source_weight": 0.5,
    "min_candidates": 5,
    "max_candidates": 5,
    "lyrics": False,
    "art": False,
    "split_artist_title": False,
}

USER_AGENT = "beets/{0} +http://beets.radbox.org/".format(beets.__version__)
BANDCAMP_SEARCH = "http://bandcamp.com/search?q={query}&page={page}"
ALBUM = "album"
ARTIST = "band"
TRACK = "track"

WORLDWIDE = "XW"
DIGITAL_MEDIA = "Digital Media"
BANDCAMP = "bandcamp"

META_DATE_PAT = r'"release_date":"([^"]*)"'
META_TRACK_ITEM_PAT = r'"item":({[^}]*})'
META_LYRICS_PAT = r'"lyrics":({[^}]*})'
META_STANDALONE_DUR_PAT = r'"duration_secs":(\d+.\d+)'

META_DATE_FORMAT = "%d %b %Y"

JSONDict = Dict[str, Any]


class Metaguru:
    ALBUM_SPLIT = ", by "
    TRACK_SPLIT = " - "

    COMMON = {"data_source": BANDCAMP, "media": DIGITAL_MEDIA}

    _album = None  # type: str
    _artist = None  # type: str
    _release_date = None  # type: date
    _lyrics = ""  # type: Optional[str]
    _metastring = None  # type: str
    _propermap: MutableMapping[str, str]
    _raw_tracks: List[JSONDict]

    soup: BeautifulSoup
    metasoup: "partial[BeautifulSoup]"
    url: str

    def __init__(self, soup: BeautifulSoup, url: str) -> None:
        self.soup = soup
        self.metasoup = partial(self.soup.find, name="meta")
        self.url = url
        self._propermap = dict()
        self._raw_tracks = []

    def _property(self, name: str) -> Optional[str]:
        """Expects to find
        <meta content="of interest" property="{name}"/>
        """
        if name in self._propermap:
            return self._propermap[name]

        item = self.metasoup(property=name)
        self._propermap[name] = item.get("content") if item else None
        return self._propermap[name]

    def _parse_album_with_artist(self) -> None:
        if self.title and self.ALBUM_SPLIT in self.title:
            self._album, self._artist = self.title.split(self.ALBUM_SPLIT)

    @property
    def title(self) -> Optional[str]:
        return self._property("og:title")

    @property
    def type(self) -> Optional[str]:
        """Song, album, etc."""
        return self._property("og:type")

    @property
    def description(self) -> Optional[str]:
        return self._property("og:description")

    @property
    def label(self) -> Optional[str]:
        return self._property("og:site_name")

    @property
    def image(self) -> Optional[str]:
        return self._property("og:image")

    @property
    def album(self) -> str:
        if not self._album:
            self._parse_album_with_artist()
        return self._album

    @property
    def artist(self) -> str:
        if not self._artist:
            self._parse_album_with_artist()
        return self._artist

    @property
    def metastring(self) -> str:
        if not self._metastring:
            self._metastring = unescape(str(self.soup.find_all("meta")))
        return self._metastring

    @property
    def release_date(self) -> Optional[date]:
        if self._release_date:
            return self._release_date
        try:
            datestr = re.search(META_DATE_PAT, self.metastring).groups()[0]
            self._release_date = datetime.strptime(datestr[:11], META_DATE_FORMAT).date()
        except AttributeError:
            return None

        return self._release_date

    @property
    def raw_tracks(self) -> List[JSONDict]:
        """Some 'meta' list members contain tags (see above), but the most useful
        lies in index 4 (as it stands). It's a huge, barely accessible json string
        which contains more or less all we need, including the track information.
          {'duration_secs': 128.0,
           'name': 'Engann veginn nettur',
           'url': 'https://bbbbbbrecors.bandcamp.com/track/engann-veginn-nettur',
           'duration': 'P00H02M08S',
           '@id': 'https://bbbbbbrecors.bandcamp.com/track/engann-veginn-nettur',
           '@type': ['MusicRecording']},
        """
        if self._raw_tracks or self._raw_tracks is None:
            return self._raw_tracks

        match = re.findall(r'{[^}{]*duration_secs({[^{]*}.*)*}', self.metastring)
        print(len(match))
        added = set()
        for a in match:
            print(a)
            track = json.loads(a)
            if track["@id"] not in added:
                self._raw_tracks.append(track)
                added.add(track["@id"])

        from pprint import pprint
        pprint(self._raw_tracks)
        return self._raw_tracks

    def track_artist(self, track_title: str) -> str:
        if self.TRACK_SPLIT in track_title:
            return track_title.split(self.TRACK_SPLIT, maxsplit=1)[0]
        return self.artist

    @property
    def lyrics(self) -> Optional[str]:
        if self._lyrics or self._lyrics is None:
            return self._lyrics

        lyrics_matches = re.findall(META_LYRICS_PAT, self.metastring)
        lyrics = []
        for match in lyrics_matches:
            lyrics.append(json.loads(match)["text"])
            self._lyrics = "\n\n".join(lyrics)
        else:
            self._lyrics = None

        return self._lyrics

    @property
    def standalone_trackinfo(self) -> TrackInfo:
        return TrackInfo(
            self.album,
            self.url,
            length=floor(self.raw_tracks[0]["duration_secs"])
            if self.raw_tracks
            else None,
            artist=self.artist,
            artist_id=self.url,
            data_url=self.url,
            **self.COMMON,
        )

    def _trackinfo(self, track: JSONDict, index: int) -> TrackInfo:
        TrackInfo(
            track["name"],
            track["url"],
            index=index,
            length=track["duration_secs"],
            data_url=track["url"],
            artist=self.track_artist(track["name"]),
        )

    @property
    def tracks(self) -> List[TrackInfo]:
        # track_alt=track["track_alt"],
        return [
            self._trackinfo(track, idx) for idx, track in enumerate(self.raw_tracks, 1)
        ]

    @property
    def albuminfo(self) -> Optional[AlbumInfo]:
        if self.type == "song":
            return None

        return AlbumInfo(
            self.album,
            self.url,
            self.artist,
            self.url,
            self.tracks,
            year=self.release_date.year if self.release_date else None,
            month=self.release_date.month if self.release_date else None,
            day=self.release_date.day if self.release_date else None,
            label=self.label,
            country=WORLDWIDE,
            data_url=self.url,
            **self.COMMON,
        )


class RequestsHandler:
    """A tiny class that provides the ability to make requests and handles failures."""

    _log = logging.Logger

    def _report(self, msg, e=None, url=None, level=logging.DEBUG):
        # type: (str, Optional[Exception], Optional[str], int) -> None
        self._log.log(level, f"{msg} {url!r}: {e}")  # type: ignore[call-arg, arg-type]

    def _get(self, url: str) -> BeautifulSoup:
        """Returns a BeautifulSoup object with the contents of url."""
        headers = {"User-Agent": USER_AGENT}
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            self._report("Communication error while fetching album", e, url)
            return None
        return BeautifulSoup(r.text, "html.parser")


class BandcampPlugin(RequestsHandler, plugins.BeetsPlugin):
    def __init__(self) -> None:
        super(BandcampPlugin, self).__init__()
        self.config.add(DEFAULT_CONFIG)
        self.import_stages = [self.imported]
        self.register_listener("pluginload", self.loaded)

    def _from_bandcamp(self, item: Any) -> bool:
        return hasattr(item, "data_source") and item.data_source == BANDCAMP

    def imported(self, _: Any, task: Any) -> None:
        """Import hook for fetching lyrics from bandcamp automatically."""
        if self.config["lyrics"]:
            for item in task.imported_items():
                # Only fetch lyrics for items from bandcamp
                if self._from_bandcamp(item):
                    self.add_lyrics(item, True)

    def loaded(self) -> None:
        # Add our own artsource to the fetchart plugin.
        # FIXME: This is ugly, but i didn't find another way to extend fetchart
        # without declaring a new plugin.
        if self.config["art"]:
            for plugin in plugins.find_plugins():
                if isinstance(plugin, fetchart.FetchArtPlugin):
                    plugin.sources = [
                        BandcampAlbumArt(plugin._log, self.config)
                    ] + plugin.sources
                    fetchart.ART_SOURCES[BANDCAMP] = BandcampAlbumArt
                    fetchart.SOURCE_NAMES[BandcampAlbumArt] = BANDCAMP
                    break

    def add_lyrics(self, item: Any, write: bool = False) -> None:
        """Fetch and store lyrics for a single item. If ``write``, then the
        lyrics will also be written to the file itself."""
        # Skip if the item already has lyrics.
        if item.lyrics:
            self._report("lyrics already present: {0}", item, level=logging.INFO)
            return None

        html = self._get(item.mb_trackid)
        if not html:
            return None

        lyrics = self.guru.lyrics
        if not lyrics:
            self._report("lyrics not found: {0}", item, level=logging.INFO)
            return None

        self._report("fetched lyrics: {0}", item, level=logging.INFO)
        item.lyrics = lyrics
        if write:
            item.try_write()
        item.store()

    def album_distance(self, items: List[Any], album_info: AlbumInfo, _: Any) -> Distance:
        """Returns the album distance."""
        dist = Distance()

        if self._from_bandcamp(album_info):
            dist.add("source", self.config["source_weight"].as_number())
        return dist

    def candidates(self, items, artist, album, va_likely):
        # type: (List[Any], str, str, bool) -> List[AlbumInfo]
        """Returns a list of AlbumInfo objects for bandcamp search results
        matching an album and artist (if not various).
        """
        return [
            album
            for album in (self.get_album_info(url) for url in self._search(album, ALBUM))
            if album
        ]

    def item_candidates(self, item: Any, artist: str, album: str) -> List[TrackInfo]:
        """Returns a list of TrackInfo objects from a bandcamp search matching a
        singleton.
        """
        query = item.title or item.album or item.artist
        return [
            track
            for track in (self.get_track_info(url) for url in self._search(query, TRACK))
            if track
        ]

    def album_for_id(self, album_id: str) -> AlbumInfo:
        """Fetches an album by its bandcamp ID and returns an AlbumInfo object
        or None if the album is not found.
        """
        # We use album url as id, so we just need to fetch and parse the album page.
        return self.get_album_info(album_id)

    def track_for_id(self, track_id: str) -> TrackInfo:
        """Fetches a track by its bandcamp ID and returns a TrackInfo object
        or None if the track is not found.
        """
        return self.get_track_info(track_id)

    def get_album_info(self, url: str) -> Optional[AlbumInfo]:
        """Return an AlbumInfo object for a bandcamp album page."""
        html = self._get(url)
        if not html:
            return None
        return Metaguru(html, url).albuminfo

    def get_track_info(self, url: str) -> Optional[TrackInfo]:
        """Returns a TrackInfo object for a bandcamp track page."""
        html = self._get(url)
        if not html:
            return None
        return Metaguru(html, url).standalone_trackinfo()

    def _search(self, query, search_type=ALBUM, page=1):
        # type: (str, str, int) -> List[str]
        """Returns a list of bandcamp urls for items of type search_type
        matching the query.
        """
        if search_type not in [ARTIST, ALBUM, TRACK]:
            self._report(f"Invalid type for search: {search_type}", level=logging.INFO)
            return []

        urls: List[str] = []
        # Usually the search yields the correct result in the first 1-3 options.
        # Therefore it doesn't make sense to go down the list until the end, and
        # the users can choose the 'max_candidates' number.
        while len(urls) < self.config["min_candidates"].as_number():
            self._report("Searching {}, page {}".format(search_type, page))
            results = self._get(BANDCAMP_SEARCH.format(query=query, page=page))
            if not results:
                continue

            clazz = "searchresult {0}".format(search_type)
            for result in results.find_all("li", attrs={"class": clazz}):
                a = result.find(attrs={"class": "heading"}).a
                if a:
                    urls.append(a["href"].split("?")[0])
                    if len(urls) == self.config["max_candidates"]:
                        break

            # Stop searching if we are on the last page.
            if not results.find("a", attrs={"class": "next"}):
                break
            page += 1

        return urls


class BandcampAlbumArt(RequestsHandler, fetchart.RemoteArtSource):
    NAME = "Bandcamp"

    def get(self, album: AlbumInfo, *args: Tuple[Any]) -> Optional[Iterator[str]]:
        """Return the url for the cover from the bandcamp album page.
        This only returns cover art urls for bandcamp albums (by id).
        """
        url = album.mb_albumid
        if not isinstance(url, six.string_types) or BANDCAMP not in url:
            return None

        html = self._get(url)
        if not html:
            return None
        try:
            image_url = Metaguru(html, url).image
            yield self._candidate(url=image_url, match=fetchart.Candidate.MATCH_EXACT)
        except ValueError as e:
            self._report("Unexpected html error fetching bandcamp album art: ", e)
            return None


class BandcampException(Exception):
    pass
