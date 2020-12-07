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

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Iterator, List, Optional, Tuple

import beets
import beets.ui
import requests
import six
from beets import plugins
from beets.autotag.hooks import AlbumInfo, Distance, TrackInfo
from bs4 import BeautifulSoup, element

from beetsplug import fetchart  # type: ignore[attr-defined]

USER_AGENT = 'beets/{0} +http://beets.radbox.org/'.format(beets.__version__)
BANDCAMP_SEARCH = 'http://bandcamp.com/search?q={query}&page={page}'
BANDCAMP_ALBUM = 'album'
BANDCAMP_ARTIST = 'band'
BANDCAMP_TRACK = 'track'
ARTIST_TITLE_DELIMITER = ' - '
HTML_ID_TRACKS = 'track_table'
HTML_CLASS_TRACK = 'track_row_view'
HTML_META_DATE_FORMAT = '%d %B %Y'

WORLDWIDE = 'XW'
DIGITAL_MEDIA = 'Digital Media'
BANDCAMP = 'bandcamp'

INDEX_TITLE_PAT = r'(\d\d?. ?)([ABCDEFGH]{1,3}\d\d?. )?(.*)'
SINGLE_TRACK_DURATION_PAT = r'duration":"P([^"]+)"'

JSONDict = Dict[str, Any]


def _split_artist_title(title: str) -> Tuple[Optional[str], str]:
    """Returns artist and title by splitting title on ARTIST_TITLE_DELIMITER."""
    parts = title.split(ARTIST_TITLE_DELIMITER, maxsplit=1)
    if len(parts) == 1:
        return None, title
    return parts[0], parts[1]


def _albumartist_from_title(html: BeautifulSoup) -> Tuple[str, str, Optional[str]]:
    """Parse the following data '<album> | <artist> [ | <album-artist ]'."""
    split_info = html.find(name="title").text.split(" | ", maxsplit=2)
    album, artist = split_info[0:2]
    album_artist = None
    if len(split_info) > 2:
        album_artist = split_info[2]
    return album, artist, album_artist


def _parse_metadata(html: BeautifulSoup, url: str) -> JSONDict:
    """Obtain release metadata from a page. Common to tracks and albums."""
    # <release-name> by <artist>, released <day-of-the-month> <month-name> <year>
    meta = html.find("meta")["content"]  # contains all we need really
    meta_lines = [line for line in meta.splitlines() if line]
    # a bit tricky considering that 'by' can be found in the album or artist names
    data = next(filter(lambda x: " by " in x and ", released " in x, meta_lines))
    try:
        album, artist_and_date = data.split(" by ")
        artist, human_date = artist_and_date.split(", released ")
        album_artist = None
    except ValueError:
        human_date = data.split(", released ")[-1]
        album, artist, album_artist = _albumartist_from_title(html)

    return {
        "album": album,
        "album_id": url,
        "artist_url": url.split("/album/")[0],
        "artist": artist,
        "album_artist": album_artist,
        "date": datetime.strptime(human_date, HTML_META_DATE_FORMAT),
    }


def _duration_in_seconds(time_str: str) -> float:
    t = datetime.strptime(time_str, "%HH%MM%SS")
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second).total_seconds()


def _duration_from_track_html(parsed_duration: str) -> Optional[float]:
    """Get duration that's found in a page with multiple songs."""
    split_duration = parsed_duration.split(":")
    hours = "00"
    if len(split_duration) == 3:
        hours = split_duration[0]
        split_duration.remove(hours)
    minutes, seconds = split_duration
    return _duration_in_seconds(f"{hours}H{minutes}M{seconds}S")


def _duration_from_soup(soup: BeautifulSoup) -> Optional[float]:
    """Get duration that's found in a page with a single song/release."""
    match = re.search(SINGLE_TRACK_DURATION_PAT, str(soup))
    if not match:
        return None
    return _duration_in_seconds(list(match.groups()).pop())


def _trackinfo_from_meta(meta: JSONDict, html: BeautifulSoup) -> TrackInfo:
    """Make TrackInfo object using common metadata. Additionally parse the
    duration given the html soup.
    """
    return TrackInfo(
        meta["album"],
        meta["artist_url"],
        length=_duration_from_soup(html),
        artist=meta["artist"],
        artist_id=meta["artist_url"],
        data_source=BANDCAMP,
        media=DIGITAL_MEDIA,
        data_url=meta["url"],
    )


def _albuminfo_from_meta(meta: JSONDict, tracks: List[TrackInfo]) -> AlbumInfo:
    return AlbumInfo(
        meta["album"],
        meta["album_id"],
        meta["album_artist"] or meta["artist"],
        meta["artist_url"],
        tracks,
        year=meta["date"].year,
        month=meta["date"].month,
        day=meta["date"].day,
        country=WORLDWIDE,
        media=DIGITAL_MEDIA,
        data_source=BANDCAMP,
        data_url=meta["album_id"],
    )


def _parse_index_with_title(string):
    # type: (str) -> Tuple[Optional[str], Optional[int], Optional[str]]
    """Examples:
    6. A2. Cool Artist - Cool Track
    3. Okay Artist - Not Bad Track
    10.Uncool_Artist - Bad Track
    """

    def clean(idx: str) -> str:
        """Remove . from the index and strip it."""
        return idx.replace(".", "").strip()

    match = re.match(INDEX_TITLE_PAT, string)
    if not match:
        return None, None, None

    split_match = list(match.groups())
    title = split_match.pop()
    index = int(clean(split_match[0]))
    track_alt = clean(split_match[1]) if split_match[1] else None
    return title, index, track_alt


def _quick_track_data(info_strings: List[str]) -> JSONDict:
    """Parse track data from the initially parsed soup text."""
    index_title, duration = info_strings
    title, index, track_alt = _parse_index_with_title(index_title)
    return {
        "title": title,
        "index": index,
        "track_alt": track_alt,
        "duration": duration,
    }


def _volatile_track_data(track_html: element.Tag) -> JSONDict:
    """Given the above isn't available, try querying the html attributes."""
    return {
        "title": track_html.find(class_="track-title").text,
        "index": int(track_html.find(class_="track_number").text.replace(".", "")),
        "track_alt": None,
        "duration": track_html.find(class_="time")
        .text.replace("\n", "")
        .replace(" ", ""),
    }


class RequestsHandler:
    """A tiny class that provides the ability to make requests and handles failures."""
    _log = logging.Logger

    def _report(self, msg, e=None, url=None, level="DEBUG"):
        # type: (str, Optional[Exception], Optional[str], str) -> None
        self._log.log(level, f"{msg} {url!r}: {e}")  # type: ignore[call-arg, arg-type]

    def _get(self, url: str) -> BeautifulSoup:
        """Returns a BeautifulSoup object with the contents of url."""
        # TODO: Handle the error properly
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
        self.config.add(
            {
                "source_weight": 0.5,
                "min_candidates": 5,
                "lyrics": False,
                "art": False,
                "split_artist_title": False,
            }
        )
        self.import_stages = [self.imported]
        self.register_listener("pluginload", self.loaded)

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
                    fetchart.ART_SOURCES["bandcamp"] = BandcampAlbumArt
                    fetchart.SOURCE_NAMES[BandcampAlbumArt] = "bandcamp"
                    break

    def album_distance(self, items, album_info, _):
        # type: (List[TrackInfo], AlbumInfo, Any) -> Distance
        """Returns the album distance."""
        dist = Distance()
        if hasattr(album_info, "data_source") and album_info.data_source == "bandcamp":
            dist.add("source", self.config["source_weight"].as_number())
        return dist

    def candidates(self, items, artist, album, va_likely, extra_tags=None):
        # type: (List[TrackInfo], str, str, bool, Optional[List[str]]) -> List[AlbumInfo]
        """Returns a list of AlbumInfo objects for bandcamp search results
        matching an album and artist (if not various).
        """
        return self.get_albums(album)

    def album_for_id(self, album_id: str) -> AlbumInfo:
        """Fetches an album by its bandcamp ID and returns an AlbumInfo object
        or None if the album is not found.
        """
        # We use album url as id, so we just need to fetch and parse the album page.
        return self.get_album_info(album_id)

    def item_candidates(self, item: Any, artist: str, album: str) -> List[TrackInfo]:
        """Returns a list of TrackInfo objects from a bandcamp search matching
        a singleton.
        """
        param = item.title or item.album or item.artist
        if param:
            return self.get_tracks(param)
        return []

    def track_for_id(self, track_id: str) -> TrackInfo:
        """Fetches a track by its bandcamp ID and returns a TrackInfo object
        or None if the track is not found.
        """
        return self.get_track_info(track_id)

    def imported(self, _: Any, task: Any) -> None:
        """Import hook for fetching lyrics from bandcamp automatically."""
        if self.config["lyrics"]:
            for item in task.imported_items():
                # Only fetch lyrics for items from bandcamp
                if hasattr(item, "data_source") and item.data_source == "bandcamp":
                    self.add_lyrics(item, True)

    def get_albums(self, query: str) -> List[AlbumInfo]:
        """Returns a list of AlbumInfo objects for a bandcamp search query."""
        albums = []
        for url in self._search(query, BANDCAMP_ALBUM):
            album = self.get_album_info(url)
            if album is not None:
                albums.append(album)
        return albums

    def get_album_info(self, url: str) -> Optional[AlbumInfo]:
        """Return an AlbumInfo object for a bandcamp album page.
        If it's a link to a track instead, return that track.
        """
        html = self._get(url)
        if not html:
            return None

        try:
            meta = _parse_metadata(html, url)
            tracks_html = html.find(id=HTML_ID_TRACKS)
            if not tracks_html:
                return _albuminfo_from_meta(meta, [_trackinfo_from_meta(meta, html)])

            tracks = []
            for row in tracks_html.find_all(class_=HTML_CLASS_TRACK):
                tracks.append(self._parse_album_track(row, url, meta["artist"]))

        except (ValueError, TypeError, AttributeError) as e:
            self._report("Unexpected html while scraping album", e, url)
            return None
        return _albuminfo_from_meta(meta, tracks)

    def get_tracks(self, query: str) -> List[TrackInfo]:
        """Returns a list of TrackInfo objects for a bandcamp search query."""
        track_urls = self._search(query, BANDCAMP_TRACK)
        return [self.get_track_info(url) for url in track_urls]

    def get_track_info(self, url: str) -> Optional[TrackInfo]:
        """Returns a TrackInfo object for a bandcamp track page."""
        html = self._get(url)
        if not html:
            return None

        meta = _parse_metadata(html, url)
        if self.config["split_artist_title"]:
            artist_from_title, meta["title"] = self._split_artist_title(meta["title"])
            if artist_from_title:
                meta["artist"] = artist_from_title

        return _trackinfo_from_meta(meta, html)

    def add_lyrics(self, item: Any, write: bool = False) -> None:
        """Fetch and store lyrics for a single item. If ``write``, then the
        lyrics will also be written to the file itself."""
        # Skip if the item already has lyrics.
        if item.lyrics:
            self._report("lyrics already present: {0}", item, level="INFO")
            return

        lyrics = self.get_item_lyrics(item)
        if not lyrics:
            self._report("lyrics not found: {0}", item, level="INFO")
            return

        self._report("fetched lyrics: {0}", item, level="INFO")
        item.lyrics = lyrics
        if write:
            item.try_write()
        item.store()

    def get_item_lyrics(self, item: Any) -> Optional[str]:
        """Get the lyrics for item from bandcamp."""
        # The track id is the bandcamp url when item.data_source is bandcamp.
        html = self._get(item.mb_trackid)
        if not html:
            return None
        lyrics = html.find(attrs={"class": "lyricsText"})
        if lyrics:
            return lyrics.text  # type: ignore[no-any-return]
        return None

    def _search(self, query, search_type=BANDCAMP_ALBUM, page=1):
        # type: (str, str, int) -> List[str]
        """Returns a list of bandcamp urls for items of type search_type
        matching the query.
        """
        if search_type not in [BANDCAMP_ARTIST, BANDCAMP_ALBUM, BANDCAMP_TRACK]:
            self._report("Invalid type for search: {0}".format(search_type), level="INFO")
            return []

        urls: List[str] = []
        # Search bandcamp until min_candidates results have been found or
        # we hit the last page in the results.
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

            # Stop searching if we are on the last page.
            if not results.find("a", attrs={"class": "next"}):
                break
            page += 1

        return urls

    def _parse_album_track(self, track_html, album_url, album_artist):
        # type: (element.Tag, str, str) -> TrackInfo
        """Returns a TrackInfo derived from the html describing a track in a
        bandcamp album page.
        """
        info: List[str] = []
        for el in track_html.text.replace("\n", "").split("  "):
            el.strip()
            if all([el, el != "info", el != "buy track"]):
                info.append(el)

        if len(info) == 2:
            track = _quick_track_data(info)
        else:
            track = _volatile_track_data(track_html)
        length = _duration_from_track_html(track["duration"])

        artist, title = _split_artist_title(track["title"])
        if not artist:
            artist = album_artist

        track_el = track_html.find(href=re.compile("/track"))
        track_url = album_url.split("/album")[0] + track_el["href"]
        return TrackInfo(
            title,
            track_url,
            index=track["index"],
            track_alt=track["track_alt"],
            length=length,
            data_url=track_url,
            artist=artist,
        )


class BandcampAlbumArt(RequestsHandler, fetchart.RemoteArtSource):
    NAME = "Bandcamp"

    def get(self, album: AlbumInfo, *args: Tuple[Any]) -> Optional[Iterator[str]]:
        """Return the url for the cover from the bandcamp album page.
        This only returns cover art urls for bandcamp albums (by id).
        """
        field = album.mb_albumid
        if isinstance(field, six.string_types) and "bandcamp" in field:
            html = self._get(field)
            if not html:
                return None

            try:
                album_html = BeautifulSoup(html.text, "html.parser").find(id="tralbumArt")
                image_url = album_html.find("a", attrs={"class": "popupImage"})["href"]
                yield self._candidate(url=image_url, match=fetchart.Candidate.MATCH_EXACT)
            except ValueError as e:
                self._report("Unexpected html error fetching bandcamp album art: ", e)


class BandcampException(Exception):
    pass
