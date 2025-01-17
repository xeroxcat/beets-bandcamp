"""End to end tests aimed at catching html updates on bandcamp side."""
import pytest
from beets.library import Item

from beetsplug.bandcamp import BandcampPlugin

pytestmark = pytest.mark.need_connection


def test_get_html():
    """Check whether content is being returned."""
    url = "https://ute-rec.bandcamp.com/album/ute004"
    should_contain = "UTE004 by Mikkel Rev, released 17 July 2020"

    plugin = BandcampPlugin()
    html = plugin._get(url)

    assert html
    assert should_contain in html


def test_return_none_for_gibberish():
    """Check whether None is being returned."""
    url = "https://ute-rec.bandcamp.com/somegibberish2113231"

    plugin = BandcampPlugin()
    html = plugin._get(url)

    assert not html


def test_search():
    query = "matriark"
    search_type = "track"
    expect_to_find = "https://mega-tech.bandcamp.com/track/matriark-arangel"

    plugin = BandcampPlugin()
    urls = list(plugin._search(query, search_type))

    assert expect_to_find in urls


def test_get_single_track_album(single_track_release):
    _, expected = single_track_release
    expected_track = expected.singleton
    url = expected.album_id

    plugin = BandcampPlugin()
    actual = plugin.get_track_info(url)

    assert vars(actual) == vars(expected_track)


def check_album(actual, expected):
    expected.tracks.sort(key=lambda t: t.index)
    actual.tracks.sort(key=lambda t: t.index)

    for actual_track, expected_track in zip(actual.tracks, expected.tracks):
        assert vars(actual_track) == vars(expected_track)
    actual.tracks = None
    expected.tracks = None

    assert vars(actual) == vars(expected)


def test_track_url_while_searching_album(single_track_album_search):
    """If a `track` url was given as the ID searching for an `album`, the
    plugin handles it and returns the album.
    """
    track_url, expected_release = single_track_album_search
    plugin = BandcampPlugin()

    album = plugin.get_album_info(track_url)

    assert album
    check_album(album, expected_release.albuminfo)


def test_candidates(ep_album):
    _, expected_release = ep_album
    expected_album = expected_release.albuminfo
    plugin = BandcampPlugin()

    albums = plugin.candidates([], expected_album.artist, expected_album.album, False)

    assert albums
    check_album(next(albums), expected_album)


def test_singleton_item_candidates(single_track_release):
    """Normally it takes ~10s to search and find a match."""
    _, expected_release = single_track_release
    expected = expected_release.singleton
    pl = BandcampPlugin()

    candidates = pl.item_candidates(Item(), expected.artist, expected.title)
    for track in candidates:
        if track.title == expected.title:
            assert vars(track) == vars(expected)
            break
    else:
        pytest.fail("Expected singleton was not returned.")


def test_singleton_cheat_mode(single_track_release):
    """In the cheat mode it should take around 1-2s to match a singleton."""
    _, expected_release = single_track_release
    expected = expected_release.singleton
    pl = BandcampPlugin()
    item = Item()
    item.comments = "Visit " + expected.artist_id
    item.title = expected.artist + " - " + expected.title

    candidates = pl.item_candidates(item, expected.artist, item.title)
    track = next(candidates)
    assert vars(track) == vars(expected)
