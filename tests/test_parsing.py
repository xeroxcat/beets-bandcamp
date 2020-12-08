from datetime import date
from functools import partial

import pytest

from beetsplug.bandcamp import Metaguru


@pytest.fixture
def url():
    return "https://mega-tech.bandcamp.com/track/matriark-arangel"


@pytest.fixture
def guru(track_meta_soup, url):
    return Metaguru(track_meta_soup, url)


def test_init(track_meta_soup):

    guru = Metaguru(track_meta_soup, url)

    assert guru.soup_pot == track_meta_soup
    assert isinstance(guru.metasoup, partial)
    assert guru.url == url


def test_parse_properties(guru):
    assert guru.title == "Matriark - Arangel, by Megatech"
    assert guru.type == "song"
    assert guru.image == "https://f4.bcbits.com/img/a2036476476_5.jpg"
    assert guru.album == "Matriark - Arangel"
    assert guru.artist == "Megatech"
    assert guru.label == "Megatech"
    assert guru.description == " track by Megatech "


def test_parse_release_date(guru):
    assert guru.release_date == date(2020, 11, 9)


def test_parse_track(guru):
    assert len(guru.tracks) == 1
