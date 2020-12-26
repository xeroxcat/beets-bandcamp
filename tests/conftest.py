"""Data prep / fixtures for tests."""
import codecs
from dataclasses import dataclass
from datetime import date
from functools import partial
from typing import Callable, List, Tuple

import pytest
from beets.autotag.hooks import AlbumInfo, TrackInfo
from bs4 import BeautifulSoup

from beetsplug.bandcamp import COUNTRY, DATA_SOURCE, MEDIA

# mypy: no-warn-return-any


@dataclass
class ReleaseInfo:
    title: str  # <album>, <label>
    type: str  # song or album
    image: str  # url
    album: str  # <artist> - <single>
    artist: str
    label: str
    description: str
    release_date: date
    track_count: int
    standalone_trackinfo = None  # type: TrackInfo
    _albuminfo = None  # type: AlbumInfo

    @property
    def albuminfo(self) -> AlbumInfo:
        return self._albuminfo

    def set_albuminfo(self, url: str, tracks: List[TrackInfo]) -> None:
        self._albuminfo = AlbumInfo(
            self.album,
            url,
            self.artist,
            url,  # TODO: check mb instead
            tracks,
            data_url=url,
            year=self.release_date.year,
            month=self.release_date.month,
            day=self.release_date.day,
            label=self.label,
            data_source=DATA_SOURCE,
            media=MEDIA,
            country=COUNTRY,
        )


def pot() -> Callable[..., BeautifulSoup]:
    return partial(BeautifulSoup, features="html.parser")


@pytest.fixture
def single_track_soup() -> Tuple[BeautifulSoup, str, ReleaseInfo]:
    test_html_file = "tests/single.html"
    url = "https://mega-tech.bandcamp.com/track/matriark-arangel"
    info = ReleaseInfo(  # expected
        **{
            "title": "Matriark - Arangel, by Megatech",
            "type": "song",
            "image": "https://f4.bcbits.com/img/a2036476476_5.jpg",
            "album": "Matriark - Arangel",
            "artist": "Megatech",
            "label": "Megatech",
            "description": " track by Megatech ",
            "release_date": date(2020, 11, 9),
            "track_count": 1,
        }
    )
    info.standalone_trackinfo = TrackInfo(
        info.album,
        url,
        length=421,
        artist=info.artist,
        artist_id=url,
        data_url=url,
        data_source=DATA_SOURCE,
        media=MEDIA,
    )
    return (
        BeautifulSoup(codecs.open(test_html_file, "r", "utf-8").read(), "html.parser"),
        url,
        info,
    )


def album_soup() -> Tuple[BeautifulSoup, str, ReleaseInfo]:
    test_html_file = "tests/album.html"
    url = "https://ute-rec.bandcamp.com/album/ute004"
    tracks = [
        "https://ute-rec.bandcamp.com/track/the-human-experience-empathy-mix",
        "https://ute-rec.bandcamp.com/track/parallell",
        "https://ute-rec.bandcamp.com/track/formulae",
        "https://ute-rec.bandcamp.com/track/biotope",
    ]
    info = ReleaseInfo(
        **{
            "title": "UTE004, by Mikkel Rev",
            "type": "album",
            "image": "https://f4.bcbits.com/img/a1035657740_5.jpg",
            "album": "UTE004",
            "artist": "Mikkel Rev",
            "label": "Ute.Rec",
            "description": "4 track album",
            "release_date": date(2020, 7, 17),
            "track_count": 4,
        }
    )
    trackinfos = [
        TrackInfo(
            "The Human Experience (Empathy Mix)",
            tracks[0],
            index=1,
            length=504,
            data_url=tracks[0],
            artist=info.artist,
        ),
        TrackInfo(
            "Parallell",
            tracks[1],
            index=2,
            length=487,
            data_url=tracks[1],
            artist=info.artist,
        ),
        TrackInfo(
            "Formulae",
            tracks[2],
            index=3,
            length=431,
            data_url=tracks[2],
            artist=info.artist,
        ),
        TrackInfo(
            "Biotope",
            tracks[3],
            index=4,
            length=421,
            data_url=tracks[3],
            artist=info.artist,
        ),
    ]
    info.set_albuminfo(url, trackinfos)
    return (
        BeautifulSoup(codecs.open(test_html_file, "r", "utf-8").read(), "html.parser"),
        url,
        info,
    )


def compilation_soup() -> Tuple[BeautifulSoup, str, ReleaseInfo]:
    test_html_file = "tests/compilation.html"
    url = "https://ismusberlin.bandcamp.com/album/ismva0033"
    tracks = [
        "https://ismusberlin.bandcamp.com/track/zebar-zimo-wish-granter-original-mix",
        "https://ismusberlin.bandcamp.com/track/alpha-tracks-valimba-original-mix",
    ]
    info = ReleaseInfo(
        **{
            "title": "ISMVA003.3, by Ismus",
            "type": "album",
            "image": "https://f4.bcbits.com/img/a4292881830_5.jpg",
            "album": "ISMVA003.3",
            "artist": "Ismus",
            "label": "Ismus",
            "description": "13 track album",
            "release_date": date(2020, 11, 29),
            "track_count": 13,
        }
    )
    trackinfos = [  # checking the first two will suffice
        TrackInfo(
            "Zebar & Zimo - Wish Granter (Original Mix)",
            tracks[0],
            index=1,
            length=414,
            data_url=tracks[0],
            artist="Zebar & Zimo",
        ),
        TrackInfo(
            "Alpha Tracks - Valimba (Original Mix)",
            tracks[1],
            index=2,
            length=361,
            data_url=tracks[1],
            artist="Alpha Tracks",
        ),
    ]
    info.set_albuminfo(url, trackinfos)
    return (
        BeautifulSoup(codecs.open(test_html_file, "r", "utf-8").read(), "html.parser"),
        url,
        info,
    )


@pytest.fixture(params=[album_soup, compilation_soup])
def multitracks_soup(request) -> Tuple[BeautifulSoup, str, ReleaseInfo]:
    return request.param()


# One track release: "https://mega-tech.bandcamp.com/track/matriark-arangel"
# Album: https://ute-rec.bandcamp.com/album/ute004"
# Single track from EP (1hr long) https://sinensis-ute.bandcamp.com/track/live-at-parken
# Compilation: https://ismusberlin.bandcamp.com/album/ismva0033
# Single track from comp: https://ismusberlin.bandcamp.com/track/zwyrg-point-of-no-return-original-mix  # noqa
# Single track release: https://lowincomesquad.bandcamp.com/track/li-ingle009-ytp-how-much-do-u-fucking-like-acid  # noqa
