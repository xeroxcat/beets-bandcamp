import pytest

from beetsplug.bandcamp import Metaguru

pytestmark = pytest.mark.parsing

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


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (
            "A1. Artist - Title",
            {"track_alt": "A1", "artist": "Artist", "title": "Title"},
        ),
        (
            "A1- Artist - Title",
            {"track_alt": "A1", "artist": "Artist", "title": "Title"},
        ),
        (
            "A1.- Artist - Title",
            {"track_alt": "A1", "artist": "Artist", "title": "Title"},
        ),
        (
            "DJ BEVERLY HILL$ - Raw Steeze",
            {"track_alt": None, "artist": "DJ BEVERLY HILL$", "title": "Raw Steeze"},
        ),
    ],
)
def test_parse_track_name(name, expected):
    actual = Metaguru.parse_track_name(name)
    assert actual == expected


def test_parse_single_track_release(single_track_release):
    html, expected = single_track_release
    guru = Metaguru(html)

    for field in COMMON_FIELDS:
        assert getattr(guru, field) == getattr(expected, field)

    assert vars(guru.singleton) == vars(expected.singleton)


def test_parse_album_or_comp(multitracks):
    html, expected_release = multitracks
    expected = expected_release.albuminfo
    guru = Metaguru(html)
    actual = guru.albuminfo

    assert hasattr(actual, "tracks")
    expected.tracks.sort(key=lambda t: t.index)
    actual.tracks.sort(key=lambda t: t.index)
    for actual_track, expected_track in zip(actual.tracks, expected.tracks):
        assert vars(actual_track) == vars(expected_track)
