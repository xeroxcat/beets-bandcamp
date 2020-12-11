from functools import partial

import pytest

from beetsplug.bandcamp import Metaguru


def test_init(single_track_soup) -> None:
    soup, url, _ = single_track_soup

    guru = Metaguru(soup, url)

    assert guru.soup == soup
    assert isinstance(guru.metasoup, partial)
    assert guru.url == url


def test_parse_single_track(single_track_soup) -> None:
    soup, url, expected = single_track_soup
    guru = Metaguru(soup, url)

    assert guru.title == expected.title
    assert guru.type == expected.type
    assert guru.image == expected.image
    assert guru.album == expected.album
    assert guru.artist == expected.artist
    assert guru.label == expected.label
    assert guru.description == expected.description
    assert guru.release_date == expected.release_date
    assert vars(guru.standalone_trackinfo) == vars(expected.standalone_trackinfo)
    if not expected.albuminfo:
        assert not guru.albuminfo
    else:
        assert vars(guru.albuminfo) == vars(expected.albuminfo)


def test_parse_album_or_comp(album_comp_soup) -> None:
    soup, url, expected = album_comp_soup
    guru = Metaguru(soup, url)

    assert guru.title == expected.title
    assert guru.type == expected.type
    assert guru.image == expected.image
    assert guru.album == expected.album
    assert guru.artist == expected.artist
    assert guru.label == expected.label
    assert guru.description == expected.description
    assert guru.release_date == expected.release_date
    assert len(guru.raw_tracks) == expected.track_count
    # assert guru.standalone_trackinfo is None
    for track, expected_track in zip(guru.albuminfo.tracks, expected.albuminfo.tracks):
        assert vars(track) == vars(expected_track)

    for key in vars(expected.albuminfo).keys():
        if key != "tracks":
            assert getattr(guru.albuminfo, key) == getattr(expected.albuminfo, key)
