import json
import re
from datetime import date, datetime
from math import floor
from typing import Any, Dict, List, Optional, Pattern

from beets.autotag.hooks import AlbumInfo, TrackInfo
from cached_property import cached_property
from pycountry import countries, subdivisions

JSONDict = Dict[str, Any]

DEFAULT_COUNTRY = "XW"
COUNTRY_OVERRIDES = {"UK": "GB"}
MEDIA = "Digital Media"
ALBUM_STATUS = "Official"
DATA_SOURCE = "bandcamp"
COMMON = {"data_source": DATA_SOURCE, "media": MEDIA}

TRACK_SPLIT = "-"
DATE_FORMAT = "%d %B %Y"
BLOCK_PAT = re.compile(r".*datePublished.*", flags=re.MULTILINE)
CATALOGNUM_PAT = re.compile(r"(^[^\d\W]+[_\W]?\d+(?:\W\d|CD)?)")
COUNTRY_PAT = re.compile(r'location\ssecondaryText">(?:[\w\s]*, )?([\w\s,]+){1,4}')
LABEL_PAT = re.compile(r'og:site_name".*content="([^"]*)"')
LYRICS_PAT = re.compile(r'"lyrics":({[^}]*})')
RELEASE_DATE_PAT = re.compile(r" released (.*)")
# track_alt and artist are optional in the track name
TRACK_NAME_PAT = re.compile(
    r"""
((?P<track_alt>[ABCDEFGH]{1,3}\d\d?)[^\w]*)?
((?P<artist>[^-]*[^ ])\s?-\s?)?
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

    def _search(self, what: Pattern[str], where: str = None) -> Optional[str]:
        if where:
            match = re.search(what, where)
        else:
            match = re.search(what, self.html)
        return match.groups()[0] if match else None

    @property
    def album(self) -> str:
        return self.meta["name"]

    @property
    def albumartist(self) -> str:
        return self.meta["byArtist"]["name"]

    @property
    def album_url_from_track(self) -> str:
        return self.meta["inAlbum"]["@id"]

    @property
    def album_id(self) -> str:
        return self.meta["@id"]

    @property
    def artist_id(self) -> str:
        return self.meta["byArtist"]["@id"]

    @property
    def image(self) -> str:
        image = self.meta.get("image", "")
        return str(image[0] if isinstance(image, list) else image)

    @cached_property
    def label(self) -> Optional[str]:
        return self._search(LABEL_PAT)

    @cached_property
    def lyrics(self) -> Optional[str]:
        matches = re.findall(LYRICS_PAT, self.html)
        if not matches:
            return None
        return "\n".join(json.loads(m).get("text") for m in matches)

    @cached_property
    def release_date(self) -> Optional[date]:
        date = self._search(RELEASE_DATE_PAT)
        return datetime.strptime(date, DATE_FORMAT).date() if date else None

    @cached_property
    def is_compilation(self) -> bool:
        artists = {track["artist"] for track in self.tracks}
        if len(artists) == 1 and artists.pop() == self.albumartist:
            return False
        return True

    @cached_property
    def catalognum(self) -> Optional[str]:
        return self._search(CATALOGNUM_PAT, self.album)

    @cached_property
    def albumtype(self) -> str:
        if self.is_compilation:
            return "compilation"
        if self.catalognum:
            return "ep"
        return "album"

    @cached_property
    def country(self) -> str:
        country = self._search(COUNTRY_PAT)
        try:
            return (
                COUNTRY_OVERRIDES.get(country)  # type: ignore
                or getattr(countries.get(name=country, default=object), "alpha_2", None)
                or subdivisions.lookup(country).country_code
            )
        except LookupError:
            return DEFAULT_COUNTRY

    @staticmethod
    def parse_track_name(name: str) -> Dict[str, str]:
        match = re.search(TRACK_NAME_PAT, name)
        if match:
            return match.groupdict()
        # backup option
        artist, _, title = name.rpartition(TRACK_SPLIT)
        return {"artist": artist.strip(), "title": title.strip()}

    @cached_property
    def tracks(self) -> List[JSONDict]:
        try:
            raw_tracks = self.meta["track"]["itemListElement"]
        except KeyError as exc:
            raise NoTracklistException() from exc

        tracks = []
        for raw_track in raw_tracks:
            track = raw_track["item"]
            track.update(self.parse_track_name(track["name"]))
            if not track.get("artist"):
                track["artist"] = self.albumartist
            track["position"] = raw_track["position"]
            tracks.append(track)

        return tracks

    @property
    def singleton(self) -> TrackInfo:
        track = self.parse_track_name(self.album)
        return TrackInfo(
            track["title"],
            self.album_id,
            index=1,
            length=floor(self.meta.get("duration_secs", 0)) or None,
            data_url=self.album_id,
            artist=track.get("artist", self.albumartist),
            artist_id=self.artist_id,
            track_alt=track.get("track_alt", ""),
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
            country=self.country,
            **COMMON,
        )
