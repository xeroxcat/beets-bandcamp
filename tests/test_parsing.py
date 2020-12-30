import pytest
from beets.autotag.hooks import AlbumInfo

from beetsplug.bandcamp import BandcampPlugin, Metaguru

# mypy: allow-untyped-defs

COMMON_FIELDS = ["image", "album_id", "artist_id"]
TRACK_FIELDS = {
    "artist",
    # "artist_credit",  # the original version ... RR4
    "artist_id",
    "data_source",
    "data_url",
    # "disctitle",
    "index",
    "length",
    # "lyricist",
    "media",
    # "medium",
    # "medium_index",
    # "medium_total",
    # "release_track_id",
    "title",
    "track_alt",
    "track_id",
}


ALBUM_FIELDS = [
    "album",
    "album_id",
    "artist",
    "artist_id",
    "tracks",
    # "asin",
    "albumtype",
    "va",
    "year",
    "month",
    "day",
    "label",
    # "mediums",
    # "releasegroup_id",
    "catalognum",
    # "script",
    # "language",
    "country",
    "albumstatus",
    "media",
    # "albumdisambig",
    # "releasegroupdisambig",
    # TODO: "artist_credit",
    "original_year",
    "original_month",
    "original_day",
    "data_source",
    "data_url",
]


def check_album(actual: AlbumInfo, expected: AlbumInfo) -> None:
    for field in ALBUM_FIELDS:
        if field != "tracks":
            assert getattr(actual, field) == getattr(expected, field)
            continue

        assert hasattr(actual, "tracks")

        expected.tracks.sort(key=lambda t: t.index)
        actual.tracks.sort(key=lambda t: t.index)
        for idx, expected_track in enumerate(expected.tracks):
            assert vars(actual.tracks[idx]) == vars(expected_track)


@pytest.mark.need_connection
def test_get_html():
    """Check whether content is being returned."""
    url = "https://ute-rec.bandcamp.com/album/ute004"
    should_contain = "UTE004 by Mikkel Rev, released 17 July 2020"

    plugin = BandcampPlugin()
    html = plugin._get(url)

    assert html
    assert should_contain in html


@pytest.mark.need_connection
def test_return_none_for_gibberish():
    """Check whether None is being returned."""
    url = "https://ute-rec.bandcamp.com/somegibberish2113231"

    plugin = BandcampPlugin()
    html = plugin._get(url)

    assert not html


@pytest.mark.need_connection
def test_search():
    query = "matriark"
    search_type = "track"
    expect_to_find = "https://mega-tech.bandcamp.com/track/matriark-arangel"

    plugin = BandcampPlugin()
    urls = plugin._search(query, search_type)

    assert expect_to_find in urls


@pytest.mark.need_connection
def test_get_single_track_album(single_track_release):
    _, expected = single_track_release
    expected_track = expected.singleton
    url = expected.album_id

    plugin = BandcampPlugin()
    actual = plugin.get_track_info(url)

    for field in TRACK_FIELDS:
        assert getattr(actual, field) == getattr(expected_track, field)


@pytest.mark.need_connection
def test_track_url_while_searching_album(single_track_album_search):
    _, expected = single_track_album_search
    url = expected.album_id

    plugin = BandcampPlugin()
    actual = plugin.get_album_info(url)
    check_album(actual, expected.albuminfo)


@pytest.mark.parsing
def test_parse_single_track_release(single_track_release):
    html, expected = single_track_release
    guru = Metaguru(html)

    for field in COMMON_FIELDS:
        assert getattr(guru, field) == getattr(expected, field)

    assert vars(guru.singleton) == vars(expected.singleton)


@pytest.mark.parsing
def test_parse_album_or_comp(multitracks):
    html, expected = multitracks
    guru = Metaguru(html)

    check_album(guru.albuminfo, expected.albuminfo)
