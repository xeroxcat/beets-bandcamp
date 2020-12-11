"""Data prep / fixtures for tests."""
import codecs
from dataclasses import dataclass
from datetime import date
from functools import partial
from typing import Tuple

import pytest
from beets.autotag.hooks import AlbumInfo, TrackInfo
from bs4 import BeautifulSoup

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
    albuminfo = None  # type: AlbumInfo


@pytest.fixture
def Pot() -> "partial[BeautifulSoup]":
    return partial(BeautifulSoup, features="html.parser")


@pytest.fixture
def single_track_soup(Pot) -> Tuple[BeautifulSoup, str, ReleaseInfo]:
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
        data_source="bandcamp",
        media="Digital Media",
    )
    info.albuminfo = None
    return (Pot(codecs.open(test_html_file, "r", "utf-8").read()), url, info)


def album_soup(Pot) -> Tuple[BeautifulSoup, str, ReleaseInfo]:
    test_html_file = "tests/album.html"
    url = "https://ute-rec.bandcamp.com/album/ute004"
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
    tracks = [
        TrackInfo(
            "The Human Experience (Empathy Mix)",
            "https://ute-rec.bandcamp.com/track/the-human-experience-empathy-mix",
            index=1,
            length=504,
            data_url="https://ute-rec.bandcamp.com/track/the-human-experience-empathy-mix",
            artist=info.artist,
        ),
        TrackInfo(
            "Parallell",
            "https://ute-rec.bandcamp.com/track/parallell",
            index=2,
            length=487,
            data_url="https://ute-rec.bandcamp.com/track/parallell",
            artist=info.artist,
        ),
        TrackInfo(
            "Formulae",
            "https://ute-rec.bandcamp.com/track/formulae",
            index=3,
            length=431,
            data_url="https://ute-rec.bandcamp.com/track/formulae",
            artist=info.artist,
        ),
        TrackInfo(
            "Biotope",
            "https://ute-rec.bandcamp.com/track/biotope",
            index=4,
            length=421,
            data_url="https://ute-rec.bandcamp.com/track/biotope",
            artist=info.artist,
        ),
    ]
    info.albuminfo = AlbumInfo(
        info.album,
        url,
        info.artist,
        url,
        tracks,
        data_url=url,
        year=info.release_date.year,
        month=info.release_date.month,
        day=info.release_date.day,
        label=info.label,
        data_source="bandcamp",
        media="Digital Media",
        country="XW",
        )
    return (Pot(codecs.open(test_html_file, "r", "utf-8").read()), url, info)

def compilation_soup(Pot) -> Tuple[BeautifulSoup, str, ReleaseInfo]:
    test_html_file = "tests/compilation.html"
    url = "https://ismusberlin.bandcamp.com/album/ismva0033"
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
    tracks = [  # checking the first two will suffice
        TrackInfo(
            "Zebar & Zimo - Wish Granter (Original Mix)",
            "https://ismusberlin.bandcamp.com/track/zebar-zimo-wish-granter-original-mix",
            index=1,
            length=414,
            data_url="https://ismusberlin.bandcamp.com/track/zebar-zimo-wish-granter-original-mix",
            artist="Zebar & Zimo",
        ),
        TrackInfo(
            "Alpha Tracks - Valimba (Original Mix)",
            "https://ismusberlin.bandcamp.com/track/alpha-tracks-valimba-original-mix",
            index=2,
            length=361,
            data_url="https://ismusberlin.bandcamp.com/track/alpha-tracks-valimba-original-mix",
            artist="Alpha Tracks",
        ),
    ]

    info.standalone_trackinfo = None
    info.albuminfo = AlbumInfo(
        info.album,
        url,
        info.artist,
        url,
        tracks,
        data_url=url,
        year=info.release_date.year,
        month=info.release_date.month,
        day=info.release_date.day,
        label=info.label,
        data_source="bandcamp",
        media="Digital Media",
        country="XW",
    )
    return (Pot(codecs.open(test_html_file, "r", "utf-8").read()), url, info)


@pytest.fixture(params=[album_soup, compilation_soup])
def album_comp_soup(request, Pot):
    yield request.param(Pot)


# One track release: "https://mega-tech.bandcamp.com/track/matriark-arangel"
# Album: https://ute-rec.bandcamp.com/album/ute004"
# Single track from EP (1hr long) https://sinensis-ute.bandcamp.com/track/live-at-parken
# Compilation: https://ismusberlin.bandcamp.com/album/ismva0033
# Single track from comp: https://ismusberlin.bandcamp.com/track/zwyrg-point-of-no-return-original-mix
