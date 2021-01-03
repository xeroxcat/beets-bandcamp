import pytest

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
    urls = plugin._search(query, search_type)

    assert expect_to_find in urls


@pytest.mark.parsing
def test_get_single_track_album(single_track_release):
    _, expected = single_track_release
    expected_track = expected.singleton
    url = expected.album_id

    plugin = BandcampPlugin()
    actual = plugin.get_track_info(url)

    assert vars(actual) == vars(expected_track)


@pytest.mark.parsing
def test_track_url_while_searching_album(single_track_album_search):
    """If a `track` url was given as the Id searching for an `album`, the
    plugin handles this and returns the album in question."""
    track_url, expected_release = single_track_album_search
    expected = expected_release.albuminfo

    plugin = BandcampPlugin()
    actual = plugin.get_album_info(track_url)

    expected.tracks.sort(key=lambda t: t.index)
    actual.tracks.sort(key=lambda t: t.index)
    for actual_track, expected_track in zip(actual.tracks, expected.tracks):
        assert vars(actual_track) == vars(expected_track)

    actual.tracks = None
    expected.tracks = None
    assert vars(actual) == vars(expected)
