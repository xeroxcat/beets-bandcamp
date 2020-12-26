from functools import partial

from beetsplug.bandcamp import Metaguru

MAIN_FIELDS = [
    "title",
    "type",
    "image",
    "album",
    "artist",
    "label",
    "description",
    "release_date",
]

ALBUM_FIELDS = [
    "album",
    "album_id",
    "artist",
    "artist_id",
    "tracks",
    # "asin",
    # "albumtype",
    # TODO: "va",
    "year",
    "month",
    "day",
    "label",
    # "mediums",
    # TODO: "artist_sort",
    # "releasegroup_id",
    # TODO: "catalognum",
    # "script",
    # "language",
    "country",
    # TODO: "albumstatus",
    "media",
    # "albumdisambig",
    # "releasegroupdisambig",
    # TODO: "artist_credit",
    # "original_year",
    # "original_month",
    # "original_day",
    "data_source",  # bandcamp
    "data_url",
]


def test_init(single_track_release_soup) -> None:
    soup, url, _ = single_track_release_soup

    guru = Metaguru(soup, url)

    assert guru.soup == soup
    assert isinstance(guru.metasoup, partial)
    assert guru.url == url


def test_parse_single_track_release(single_track_release_soup) -> None:
    soup, url, expected = single_track_release_soup
    guru = Metaguru(soup, url)

    for field in MAIN_FIELDS:
        assert getattr(guru, field) == getattr(expected, field)

    assert vars(guru.standalone_trackinfo) == vars(expected.standalone_trackinfo)


def test_parse_album_or_comp(multitracks_soup) -> None:
    soup, url, expected = multitracks_soup
    guru = Metaguru(soup, url)

    for field in MAIN_FIELDS:
        assert getattr(guru, field) == getattr(expected, field)

    assert len(guru.raw_tracks) == expected.track_count
    assert guru.standalone_trackinfo is None

    if not expected.albuminfo:
        assert not guru.albuminfo
        return

    for field in ALBUM_FIELDS:
        if field == "tracks":
            assert hasattr(guru.albuminfo, "tracks")

            expected.albuminfo.tracks.sort(key=lambda t: t.index)
            guru.albuminfo.tracks.sort(key=lambda t: t.index)
            for n, expected_track in enumerate(expected.albuminfo.tracks):
                assert vars(guru.albuminfo.tracks[n]) == vars(expected_track)
        else:
            assert getattr(guru.albuminfo, field) == getattr(expected.albuminfo, field)
