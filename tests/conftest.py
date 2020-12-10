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
    info = ReleaseInfo(
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


@pytest.fixture
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
    return (Pot(codecs.open(test_html_file, "r", "utf-8").read()), url, info)

    # info.albuminfo = AlbumInfo(
    #     info.album,
    #     url,
    #     info.artist,
    #     url,
    #     [info.standalone_trackinfo],
    #     data_url=url,
    #     year=2020,
    #     month=11,
    #     day=9,
    #     label=info.label,
    #     data_source="bandcamp",
    #     media="Digital Media",
    #     country="XW",
    #     )


# One track release: "https://mega-tech.bandcamp.com/track/matriark-arangel"
# Album: https://ute-rec.bandcamp.com/album/ute004"
# Single track from EP (1hr long) https://sinensis-ute.bandcamp.com/track/live-at-parken
# Compilation: https://ismusberlin.bandcamp.com/album/ismva0033
# Single track from comp: https://ismusberlin.bandcamp.com/track/zwyrg-point-of-no-return-original-mix
