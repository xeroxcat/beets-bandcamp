from datetime import datetime

import pytest

from beetsplug.bandcamp import BandcampPlugin, _parse_metadata


def test_plugin_found():
    assert BandcampPlugin()


def test_parse_album_metadata(html_meta):
    expected = html_meta["expected_data"]

    test_html, test_url = html_meta["html"], html_meta["url"]
    actual = _parse_metadata(test_html, test_url)

    assert actual == expected


def test_parse_track(tracks_soup):
    expected_tracks = tracks_soup["expected_data"]
    plugin = BandcampPlugin()
    input_track_soups = tracks_soup["soup"].find_all(class_="track_row_view")
    for soup, expected in zip(input_track_soups, expected_tracks):
        actual = plugin._parse_album_track(
            soup,
            tracks_soup["url"],
            tracks_soup["album_artist"],
        )
        assert vars(actual) == vars(expected)
