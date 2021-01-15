import pytest

from beetsplug.bandcamp._metaguru import Metaguru, urlify

pytestmark = pytest.mark.parsing


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("LI$INGLE010 - cyberflex - LEVEL X", "li-ingle010-cyberflex-level-x"),
        ("LI$INGLE007 - Re:drum - Movin'", "li-ingle007-re-drum-movin"),
        ("X23 & Høbie - Exhibit A", "x23-h-bie-exhibit-a"),
    ],
)
def test_convert_title(title, expected):
    assert urlify(title) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (
            "Title",
            {"track_alt": None, "artist": None, "title": "Title"},
        ),
        (
            "Artist - Title",
            {"track_alt": None, "artist": "Artist", "title": "Title"},
        ),
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
        (
            "LI$INGLE010 - cyberflex - LEVEL X",
            {"track_alt": None, "artist": "cyberflex", "title": "LEVEL X"},
        ),
    ],
)
def test_parse_track_name(name, expected):
    actual = Metaguru.parse_track_name(name)
    assert actual == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Berlin, Germany", "DE"),
        ("Oslo, Norway", "NO"),
        ("London, UK", "GB"),
        ("Malmö, Sweden", "SE"),
        ("UK", "GB"),
        ("Seattle, Washington", "US"),
        ("Los Angeles, California", "US"),
        ("New York", "US"),
        ("No Ones, Land", "XW"),
        ("", "XW"),
    ],
)
def test_parse_country(name, expected):
    line = f'<span class="location secondaryText">{name}</span>'
    actual = Metaguru(line).country
    assert actual == expected


@pytest.mark.parametrize(
    ("album", "expected"),
    [
        ("Tracker-229 [PRH-002]", "PRH-002"),
        ("[PRH-002] Tracker-229", "PRH-002"),
        ("Tracker-229 PRH-002", "Tracker-229"),
        ("ISMVA003.2", "ISMVA003.2"),
        ("UTC003-CD", "UTC003"),
        ("UTC-003", "UTC-003"),
        ("EP [SINDEX008]", "SINDEX008"),
    ],
)
def test_parse_catalognum(album, expected):
    guru = Metaguru("")
    guru.meta = {"name": album}
    assert guru.catalognum == expected


def test_parse_single_track_release(single_track_release):
    html, expected = single_track_release
    guru = Metaguru(html)

    assert vars(guru.singleton) == vars(expected.singleton)


def test_parse_album_or_comp(multitracks):
    html, expected_release = multitracks
    guru = Metaguru(html)

    expected_disctitles = expected_release.disctitles.values()
    albums = list(guru.albums)

    assert len(albums) == len(expected_disctitles)

    test_release = None
    for album in albums:
        disctitle = album.tracks[0].disctitle
        assert disctitle in expected_disctitles
        if album.media == expected_release.media:
            test_release = album

    expected = expected_release.albuminfo

    assert hasattr(test_release, "tracks")
    assert len(test_release.tracks) == expected_release.track_count

    expected.tracks.sort(key=lambda t: t.index)
    test_release.tracks.sort(key=lambda t: t.index)

    for test_release_track, expected_track in zip(test_release.tracks, expected.tracks):
        assert vars(test_release_track) == vars(expected_track)
    test_release.tracks = None
    expected.tracks = None

    assert vars(test_release) == vars(expected)
