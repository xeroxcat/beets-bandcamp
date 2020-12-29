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
from operator import truth
from typing import Any, Dict, List, Optional, Sequence

import beets
import beets.ui
import requests
import six
from beets import plugins
from beets.autotag.hooks import AlbumInfo, Distance, TrackInfo
from beets.library import Item
from cached_property import cached_property

from beetsplug import fetchart  # type: ignore[attr-defined]

JSONDict = Dict[str, Any]

DEFAULT_CONFIG: JSONDict = {
    "source_weight": 0.5,
    "min_candidates": 5,
    "lyrics": False,
    "art": False,
}

SEARCH_URL = "https://bandcamp.com/search?q={0}&page={1}"
SEARCH_ITEM_PAT = 'href="(https://[^/]*/{0}/[^?]*)'
USER_AGENT = "beets/{0} +http://beets.radbox.org/".format(beets.__version__)
ALBUM = "album"
ARTIST = "band"
TRACK = "track"

COUNTRY = "XW"
MEDIA = "Digital Media"
ALBUM_STATUS = "Official"
DATA_SOURCE = "bandcamp"
COMMON = {"data_source": DATA_SOURCE, "media": MEDIA}

TRACK_SPLIT = "-"
DATE_FORMAT = "%d %B %Y"
BLOCK_PAT = re.compile(r".*datePublished.*", flags=re.MULTILINE)
CATALOGNUM_PAT = re.compile(r"^[^\d\W]+[_\W]?\d+(?:\W\d|CD)?")
LABEL_PAT = re.compile(r'og:site_name".*content="([^"]*)"')
LYRICS_PAT = re.compile(r'"lyrics":({[^}]*})')
RELEASE_DATE_PAT = re.compile(r" released (.*)")

# track_alt and artist are optional in the track name
TRACK_NAME_PAT = re.compile(
    r"""
((?P<track_alt>[ABCDEFGH]{1,3}\d\d?)[^\w\d]*)?
((?P<artist>[^-]*\w)\s?-\s?)?
(?P<title>.*)""",
    re.VERBOSE,
)


class NoTracklistException(Exception):
    def __str__(self) -> str:
        return "Could not find tracklist in the page"


class Metaguru:
    html: str
    meta: JSONDict

    def __init__(self, html: str) -> None:
        self.html = html

        # TODO: move it out
        match = re.search(BLOCK_PAT, html)
        if match:
            self.meta = json.loads(match.group())

    @cached_property
    def album(self) -> str:
        return self.meta["name"]  # type: ignore

    @cached_property
    def albumartist(self) -> str:
        return self.meta["byArtist"]["name"]  # type: ignore

    @cached_property
    def album_url_from_track(self) -> str:
        return self.meta["inAlbum"]["@id"]  # type: ignore

    @cached_property
    def album_id(self) -> str:
        return self.meta["@id"]  # type: ignore

    @cached_property
    def artist_id(self) -> str:
        return self.meta["byArtist"]["@id"]  # type: ignore

    @cached_property
    def image(self) -> str:
        image = self.meta.get("image", "")
        return str(image[0] if isinstance(image, list) else image)

    @cached_property
    def label(self) -> Optional[str]:
        match = re.search(LABEL_PAT, self.html)
        return match.groups()[0] if match else None

    @cached_property
    def lyrics(self) -> Optional[str]:
        matches = re.findall(LYRICS_PAT, self.html)
        if not matches:
            return None
        return "\n".join(json.loads(m).get("text") for m in matches)

    @cached_property
    def release_date(self) -> Optional[date]:
        match = re.search(RELEASE_DATE_PAT, self.html)
        if not match:
            return None
        return datetime.strptime(match.groups()[0], DATE_FORMAT).date()

    def _parse_track_name(self, name: str) -> Dict[str, str]:
        match = re.search(TRACK_NAME_PAT, name)
        if not match:  # backup option
            artist, _, title = name.rpartition(TRACK_SPLIT)
            data = {"artist": artist.strip(), "title": title.strip()}
        else:
            data = match.groupdict()

        if not data.get("artist"):
            data["artist"] = self.albumartist
        return data

    @property
    def tracks(self) -> List[JSONDict]:
        try:
            raw_tracks = self.meta["track"]["itemListElement"]
        except KeyError as exc:
            raise NoTracklistException() from exc

        tracks = []
        for raw_track in raw_tracks:
            track = raw_track["item"]
            track.update(self._parse_track_name(track["name"]))
            track["position"] = raw_track["position"]
            tracks.append(track)

        return tracks

    @cached_property
    def is_compilation(self) -> bool:
        artists = {track["artist"] for track in self.tracks}
        if len(artists) == 1 and artists.pop() == self.albumartist:
            return False
        return True

    @cached_property
    def catalognum(self) -> str:
        match = re.search(CATALOGNUM_PAT, self.album)
        return match.group() if match else ""  # type: ignore

    @cached_property
    def albumtype(self) -> str:
        if self.is_compilation:
            return "compilation"
        if self.catalognum:
            return "ep"
        return "album"

    @property
    def singleton(self) -> TrackInfo:
        track_data = self._parse_track_name(self.album)
        return TrackInfo(
            track_data["title"],
            self.album_id,
            length=floor(self.meta.get("duration_secs", 0)) or None,
            artist=track_data["artist"],
            artist_id=self.artist_id,
            data_url=self.album_id,
            **COMMON,
        )

    @property
    def trackinfos(self) -> List[TrackInfo]:
        return [
            TrackInfo(
                track.get("title"),
                track.get("url"),
                index=track.get("position"),
                length=floor(track.get("duration_secs", 0)) or None,
                data_url=track.get("url"),
                artist=track.get("artist"),
                artist_id=self.artist_id,
                track_alt=track.get("track_alt"),
                **COMMON,
            )
            for track in self.tracks
        ]

    @property
    def albuminfo(self) -> AlbumInfo:
        return AlbumInfo(
            self.album,
            self.album_id,
            self.albumartist,
            self.artist_id,
            self.trackinfos,
            va=self.is_compilation,
            year=self.release_date.year,
            month=self.release_date.month,
            day=self.release_date.day,
            original_year=self.release_date.year,
            original_month=self.release_date.month,
            original_day=self.release_date.day,
            label=self.label,
            catalognum=self.catalognum,
            albumtype=self.albumtype,
            data_url=self.album_id,
            albumstatus=ALBUM_STATUS,
            country=COUNTRY,
            **COMMON,
        )


class BandcampRequestsHandler:
    """A class that provides an ability to make requests and handles failures."""

    _log: logging.Logger

    def _exc(self, msg_template: str, *args: Sequence[str]) -> None:
        self._log.log(logging.WARNING, msg_template, *args, exc_info=True)

    def _info(self, msg_template: str, *args: Sequence[str]) -> None:
        self._log.log(logging.INFO, msg_template, *args, exc_info=False)

    def _get(self, url: str) -> Optional[str]:
        """Return text contents of the url response."""
        headers = {"User-Agent": USER_AGENT}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            self._exc("Communication error while fetching URL: {}", url)
            return None
        return response.text


class BandcampAlbumArt(BandcampRequestsHandler, fetchart.RemoteArtSource):
    NAME = "Bandcamp"

    def get(self, album: AlbumInfo, *_: Sequence[Any]) -> fetchart.Candidate:
        """Return the url for the cover from the bandcamp album page.
        This only returns cover art urls for bandcamp albums (by id).
        """
        if hasattr(album, "art_source") and album.art_source == DATA_SOURCE:
            self._info("Art cover is already present")
            return None

        url = album.mb_albumid
        if not isinstance(url, six.string_types) or DATA_SOURCE not in url:
            self._info("Not fetching art for a non-bandcamp album")
            return None

        html = self._get(url)
        if not html:
            return None

        try:
            image_url = Metaguru(html).image
            yield self._candidate(url=image_url, match=fetchart.Candidate.MATCH_EXACT)
        except Exception:
            self._exc("Unexpected parsing error fetching bandcamp album art")
        return None


class BandcampPlugin(BandcampRequestsHandler, plugins.BeetsPlugin):
    def __init__(self) -> None:
        super().__init__()
        self.config.add(DEFAULT_CONFIG.copy())
        self.import_stages = [self.imported]
        self.register_listener("pluginload", self.loaded)

    @staticmethod
    def _from_bandcamp(item: Item) -> bool:
        return hasattr(item, "data_source") and item.data_source == DATA_SOURCE

    def add_lyrics(self, item: Item, write: bool = False) -> None:
        """Fetch and store lyrics for a single item. If ``write``, then the
        lyrics will also be written to the file itself.
        """
        if item.lyrics:
            self._info("Lyrics are already present: {}", item)
            return None

        html = self._get(item.mb_trackid)
        if not html:
            return None

        lyrics = Metaguru(html).lyrics
        if not lyrics:
            self._info("Lyrics not found: {}", item)
            return None

        self._info("Fetched lyrics: {}", item)
        item.lyrics = lyrics
        if write:
            item.try_write()
        item.store()
        return None

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

    def album_distance(self, items, album_info, _):
        # type: (List[Any], AlbumInfo, Any) -> Distance
        """Return the album distance."""
        dist = Distance()
        if self._from_bandcamp(album_info):
            dist.add("source", self.config["source_weight"].as_number())
        return dist

    def candidates(self, items, artist, album, va_likely):
        # type: (List[Item], str, str, bool) -> List[AlbumInfo]
        """Return a list of albums given a search query."""
        return list(filter(truth, map(self.get_album_info, self._search(album, ALBUM))))

    def item_candidates(self, item, artist, title):
        # type: (Item, str, str) -> List[TrackInfo]
        """Return a list of tracks from a bandcamp search matching a singleton."""
        query = title or item.album or artist
        return list(filter(truth, map(self.get_track_info, self._search(query, TRACK))))

    def album_for_id(self, album_id: str) -> Optional[AlbumInfo]:
        """Fetch an album by its bandcamp ID and return it if found."""
        return self.get_album_info(album_id)

    def track_for_id(self, track_id: str) -> Optional[TrackInfo]:
        """Fetch a track by its bandcamp ID and return it if found."""
        return self.get_track_info(track_id)

    def get_album_info(self, url: str) -> Optional[AlbumInfo]:
        """Return an AlbumInfo object for a bandcamp album page."""
        html = self._get(url)
        if not html:
            return None

        guru = Metaguru(html)
        try:
            return guru.albuminfo
        except NoTracklistException:
            self._info("Track URL {} provided, getting the album instead", url)
            return self.get_album_info(guru.album_url_from_track)

    def get_track_info(self, url: str) -> Optional[TrackInfo]:
        """Returns a TrackInfo object for a bandcamp track page."""
        html = self._get(url)
        return Metaguru(html).singleton if html else None

    def _search(self, query: str, search_type: str = ALBUM) -> List[str]:
        """Return a list of URLs for items of type search_type matching the query."""
        urls: List[str] = []
        page = 1

        pattern = SEARCH_ITEM_PAT.format(search_type)
        max_urls = self.config["min_candidates"].as_number()
        while len(urls) < max_urls:
            self._info("Searching {}, page {}", search_type, str(page))

            html = self._get(SEARCH_URL.format(query, page))
            if not html:
                break

            matches = set(re.findall(rf"{pattern}", html))
            self._info("Found {} {} urls", str(len(matches)), search_type)
            for url in matches:
                urls.append(url)
                if len(urls) == max_urls:
                    return urls

            # Stop searching if we are on the last page.
            next_page = page + 1
            if not re.search(rf"page={next_page}", html):
                return urls
            page = next_page

        return urls
