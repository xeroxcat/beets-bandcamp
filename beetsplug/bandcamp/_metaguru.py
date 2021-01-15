"""Module for parsing bandcamp metadata."""
import json
import re
from datetime import date, datetime
from functools import reduce
from math import floor
from string import ascii_lowercase, digits
from typing import Any, Dict, Iterator, List, Optional, Pattern

from beets import __version__ as beets_version
from beets.autotag.hooks import AlbumInfo, TrackInfo
from cached_property import cached_property
from packaging.version import parse
from pycountry import countries, subdivisions

NEW_BEETS = True
if parse(beets_version) < parse("1.5.0"):
    NEW_BEETS = False


JSONDict = Dict[str, Any]

ALBUM_STATUS = "Official"
COUNTRY_OVERRIDES = {"UK": "GB"}
DATE_FORMAT = "%d %B %Y"
DATA_SOURCE = "bandcamp"
DEFAULT_COUNTRY = "XW"
DEFAULT_MEDIA = "Digital Media"
MEDIA_MAP = {
    "VinylFormat": "Vinyl",
    "CDFormat": "CD",
    "CassetteFormat": "Cassette",
    "DigitalFormat": DEFAULT_MEDIA,
}
VALID_URL_CHARS = {*ascii_lowercase, *digits}

_catalognum = r"[^\d\W]+[_\W]?\d+(?:\W\d|CD)?"
PATTERNS = {
    "meta": re.compile(r".*datePublished.*", flags=re.MULTILINE),
    "quick_catalognum": re.compile(rf"\[({_catalognum})\]"),
    "catalognum": re.compile(rf"(^{_catalognum})"),
    "country": re.compile(r'location\ssecondaryText">(?:[\w\s]*, )?([\w\s,]+){1,4}'),
    "label": re.compile(r'og:site_name".*content="([^"]*)"'),
    "lyrics": re.compile(r'"lyrics":({[^}]*})'),
    "release_date": re.compile(r" released (.*)"),
    "track_name": re.compile(
        r"""
((?P<track_alt>[ABCDEFGH]{1,3}\d\d?)[^\w]*)?
(\s?(?P<artist>[^-]*[^ ])\s?-\s?)?
(?P<title>[^-]*$)""",
        re.VERBOSE,
    ),
    "vinyl_name": re.compile(
        r'(?P<count>[1-5]|([Ss]ing|[Dd]oub|[Tt]rip)le )( ?x? ?)(?P<type>(7|10|12)" Vinyl)'
    ),
}


def urlify(pretty_string: str) -> str:
    """Make a string bandcamp-url-compatible."""
    return reduce(
        lambda p, n: p + n
        if n in VALID_URL_CHARS
        else p + "-"
        if not p.endswith("-")
        else p,
        pretty_string.lower(),
        "",
    ).strip("-")


class Metaguru:
    html: str
    meta: JSONDict
    _media = None  # type: Dict[str, str]

    def __init__(self, html: str) -> None:
        self.html = html

        match = re.search(PATTERNS["meta"], html)
        if match:
            self.meta = json.loads(match.group())

    def _search(self, needle: Pattern[str], haystack: str = None) -> str:
        if not haystack:
            haystack = self.html
        match = re.search(needle, haystack)
        return match.groups()[0] if match else ""

    @property
    def album(self) -> str:
        # TODO: Cleanup catalogue, etc
        return self.meta["name"]

    @property
    def albumartist(self) -> str:
        return self.meta["byArtist"]["name"]

    @property
    def album_id(self) -> str:
        return self.meta["@id"]

    @property
    def artist_id(self) -> str:
        return self.meta["byArtist"]["@id"]

    @property
    def image(self) -> str:
        image = self.meta.get("image", "")
        return image[0] if isinstance(image, list) else image

    @property
    def label(self) -> str:
        return self._search(PATTERNS["label"])

    @property
    def lyrics(self) -> Optional[str]:
        # TODO: Need to test
        matches = re.findall(PATTERNS["lyrics"], self.html)
        if not matches:
            return None
        return "\n".join(json.loads(m).get("text") for m in matches)

    @property
    def release_date(self) -> date:
        datestr = self._search(PATTERNS["release_date"])
        return datetime.strptime(datestr, DATE_FORMAT).date()

    @property
    def catalognum(self) -> str:
        # TODO: Can also search the description for more info, e.g. catalog: catalognum
        return self._search(PATTERNS["quick_catalognum"], self.album) or self._search(
            PATTERNS["catalognum"], self.album
        )

    @property
    def country(self) -> str:
        country = self._search(PATTERNS["country"])
        try:
            return (
                COUNTRY_OVERRIDES.get(country)
                or getattr(countries.get(name=country, default=object), "alpha_2", None)
                or subdivisions.lookup(country).country_code
            )
        except LookupError:
            return DEFAULT_COUNTRY

    @property
    def media(self) -> str:
        if self._media:
            return MEDIA_MAP[self._media["musicReleaseFormat"]]
        return DEFAULT_MEDIA

    @property
    def disctitle(self) -> str:
        return self._media["name"]

    @cached_property
    def mediums(self) -> int:
        if self.media != "Vinyl":
            return 1

        conv = {"single": "1", "double": "2", "triple": "3"}
        match = re.search(PATTERNS["vinyl_name"], self.disctitle)
        try:
            count = match.groupdict()["count"] if match else "1"
            return int(conv.setdefault(count, "1"))
        except (AttributeError, ValueError):
            return 1

    @property
    def medium_total(self) -> int:
        """We can't tell the number of tracks in a disc for a multi-disc release."""
        # TODO: Check description
        return len(self.tracks) if self.mediums == 1 else 0

    @property
    def medium(self) -> int:
        """We can't tell the number of current disc for a multi-disc release."""
        return 1 if self.mediums == 1 else 0

    @cached_property
    def is_va(self) -> bool:
        if "Various Artists" in self.album:
            return True

        unique_artists = len({track["artist"] for track in self.tracks})
        if (
            len(self.tracks) > 4
            and "ep" not in self.disctitle.lower()
            and unique_artists > 1
        ):
            return True

        return False

    @property
    def albumtype(self) -> str:
        if self.is_va:
            return "compilation"
        if self.catalognum:
            return "ep"
        return "album"

    @staticmethod
    def parse_track_name(name: str) -> Dict[str, str]:
        return re.search(PATTERNS["track_name"], name).groupdict()  # type: ignore

    @cached_property
    def tracks(self) -> List[JSONDict]:
        # TODO: Check for 'digital' in the name
        tracks = []
        for raw_track in self.meta["track"].get("itemListElement", []):
            track = raw_track["item"]
            track.update(self.parse_track_name(track["name"]))
            if not track.get("artist"):
                track["artist"] = self.albumartist
            track["position"] = raw_track["position"]
            tracks.append(track)
        return tracks

    def _trackinfo(self, track: JSONDict) -> TrackInfo:
        if NEW_BEETS:
            trackinfo = TrackInfo(
                title=track.get("title"), track_id=track.get("url", self.album_id)
            )
        else:
            trackinfo = TrackInfo(track.get("title"), track.get("url", self.album_id))
        trackinfo.artist = track.get("artist") or self.albumartist
        trackinfo.artist_id = self.artist_id
        trackinfo.data_source = DATA_SOURCE
        trackinfo.data_url = self.album_id
        trackinfo.index = track.get("position", 1)
        trackinfo.length = floor(
            track.get("duration_secs", self.meta.get("duration_secs", 0))
        )
        trackinfo.media = self.media or DEFAULT_MEDIA
        trackinfo.track_alt = track.get("track_alt", None)
        return trackinfo

    @property
    def singleton(self) -> TrackInfo:
        return self._trackinfo(self.parse_track_name(self.album))

    @property
    def albuminfo(self) -> AlbumInfo:
        _tracks = []
        for track in self.tracks:
            _track = self._trackinfo(track)
            _track.disctitle = self.disctitle
            _track.medium = self.medium
            _track.medium_index = _track.index
            _track.medium_total = self.medium_total
            _tracks.append(_track)

        if NEW_BEETS:
            albuminfo = AlbumInfo(_tracks)
            albuminfo.album = self.album
            albuminfo.albumartist = self.albumartist
            albuminfo.album_id = self.album_id
            albuminfo.artist_id = self.artist_id
        else:
            albuminfo = AlbumInfo(
                self.album,
                self.album_id,
                self.albumartist,
                self.artist_id,
                tracks=_tracks,
            )
        albuminfo.va = self.is_va
        albuminfo.year = self.release_date.year
        albuminfo.month = self.release_date.month
        albuminfo.day = self.release_date.day
        albuminfo.label = self.label
        albuminfo.catalognum = self.catalognum
        albuminfo.albumtype = self.albumtype
        albuminfo.data_url = self.album_id
        albuminfo.albumstatus = ALBUM_STATUS
        albuminfo.country = self.country
        albuminfo.media = self.media
        albuminfo.mediums = self.mediums
        albuminfo.data_source = DATA_SOURCE
        return albuminfo

    @property
    def albums(self) -> Iterator[AlbumInfo]:
        """Return an album for each available release format."""
        try:
            for _format in self.meta["albumRelease"]:
                media = _format.get("musicReleaseFormat")
                if media:
                    self._media = _format
                    yield self.albuminfo
        except AttributeError:
            yield None
