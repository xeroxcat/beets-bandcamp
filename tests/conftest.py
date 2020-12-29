"""Data prep / fixtures for tests."""
import codecs
from dataclasses import dataclass
from datetime import date
from typing import List, Tuple

import pytest
from beets.autotag.hooks import AlbumInfo, TrackInfo

from beetsplug.bandcamp import COUNTRY, DATA_SOURCE, MEDIA

# mypy: no-warn-return-any


@dataclass
class ReleaseInfo:
    image: str
    album: str
    album_id: str
    albumartist: str
    artist_id: str
    label: str
    release_date: date
    va: bool
    track_count: int
    singleton = None  # type: TrackInfo
    albuminfo = None  # type: AlbumInfo

    def trackinfo(self, index: int, info: Tuple) -> TrackInfo:
        if len(info) == 4:
            track_url, artist, title, length = info
            alt = None
        else:
            track_url, artist, title, length, alt = info

        return TrackInfo(
            title,
            track_url,
            index=index,
            length=length,
            data_url=track_url,
            artist=artist,
            artist_id=self.artist_id,
            track_alt=alt,
            data_source=DATA_SOURCE,
            media=MEDIA,
        )

    def set_singleton(self, artist: str, title: str, length: int) -> None:
        self.singleton = TrackInfo(
            title,
            self.album_id,
            artist=artist,
            artist_id=self.artist_id,
            length=length,
            data_url=self.album_id,
            data_source=DATA_SOURCE,
            media=MEDIA,
        )

    def set_albuminfo(self, tracks: List[Tuple]) -> None:
        self.albuminfo = AlbumInfo(
            self.album,
            self.album_id,
            self.albumartist,
            self.artist_id,
            tracks=[self.trackinfo(idx, track) for idx, track in enumerate(tracks, 1)],
            data_url=self.album_id,
            year=self.release_date.year,
            month=self.release_date.month,
            day=self.release_date.day,
            original_year=self.release_date.year,
            original_month=self.release_date.month,
            original_day=self.release_date.day,
            label=self.label,
            va=self.va,
            data_source=DATA_SOURCE,
            media=MEDIA,
            country=COUNTRY,
        )


@pytest.fixture
def single_track_release() -> Tuple[str, ReleaseInfo]:
    """Single track as a release on its own."""
    test_html_file = "tests/single.html"
    info = ReleaseInfo(  # expected
        **{
            "image": "https://f4.bcbits.com/img/a2036476476_10.jpg",
            "album": "Matriark - Arangel",
            "album_id": "https://mega-tech.bandcamp.com/track/matriark-arangel",
            "albumartist": "Megatech",
            "artist_id": "https://mega-tech.bandcamp.com",
            "label": "Megatech",
            "release_date": date(2020, 11, 9),
            "track_count": 1,
            "va": False,
        }
    )
    info.set_singleton("Matriark", "Arangel", 421)
    return codecs.open(test_html_file).read(), info


@pytest.fixture
def single_track_album_search() -> Tuple[str, ReleaseInfo]:
    """Single track which is part of an album release."""
    test_html_file = "tests/single_track.html"
    album_artist = "Alpha Tracks"
    info = ReleaseInfo(  # expected
        **{
            "image": "https://f4.bcbits.com/img/a0610664056_10.jpg",
            "album": "SINE03",
            "album_id": "https://sinensis-ute.bandcamp.com/album/sine03",
            "albumartist": album_artist,
            "artist_id": "https://sinensis-ute.bandcamp.com",
            "label": "Sinensis",
            "release_date": date(2020, 6, 16),
            "track_count": 2,
            "va": False,
        }
    )
    turl = "https://sinensis-ute.bandcamp.com/track"
    tracks = [
        (f"{turl}/live-at-parken", album_artist, "Live At PARKEN", 3600),
        (f"{turl}/odondo", album_artist, "Odondo", 371),
    ]
    info.set_albuminfo(tracks)
    return codecs.open(test_html_file).read(), info


def album() -> Tuple[str, ReleaseInfo]:
    """An album with a single artist."""
    test_html_file = "tests/album.html"
    album_artist = "Mikkel Rev"
    info = ReleaseInfo(
        **{
            "image": "https://f4.bcbits.com/img/a1035657740_10.jpg",
            "album": "UTE004",
            "album_id": "https://ute-rec.bandcamp.com/album/ute004",
            "albumartist": album_artist,
            "artist_id": "https://ute-rec.bandcamp.com",
            "label": "Ute.Rec",
            "release_date": date(2020, 7, 17),
            "track_count": 4,
            "va": False,
        }
    )
    turl = "https://ute-rec.bandcamp.com/track"
    tracks = [
        (
            f"{turl}/the-human-experience-empathy-mix",
            album_artist,
            "The Human Experience (Empathy Mix)",
            504,
        ),
        (f"{turl}/parallell", album_artist, "Parallell", 487),
        (f"{turl}/formulae", album_artist, "Formulae", 431),
        (f"{turl}/biotope", album_artist, "Biotope", 421),
    ]
    info.set_albuminfo(tracks)
    return codecs.open(test_html_file).read(), info


def album_with_track_alt() -> Tuple[str, ReleaseInfo]:
    """An album with alternative track indexes."""
    test_html_file = "tests/track_alt.html"
    info = ReleaseInfo(
        **{
            "image": "https://f4.bcbits.com/img/a2798384948_10.jpg",
            "album": "FLD001 // Gareth Wild - Common Assault EP",
            "album_id": "https://foldrecords.bandcamp.com/album/fld001-gareth-wild-common-assault-ep",
            "albumartist": "Gareth Wild",
            "artist_id": "https://foldrecords.bandcamp.com",
            "label": "Fold Records",
            "release_date": date(2020, 11, 29),
            "track_count": 6,
            "va": False,
        }
    )
    turl = "https://foldrecords.bandcamp.com/track"
    tracks = [
        (
            f"{turl}/a1-gareth-wild-live-wire",
            "Gareth Wild",
            "Live Wire",
            357,
            "A1",
        ),
        (
            f"{turl}/a2-gareth-wild-live-wire-roll-dann-remix",
            "Gareth Wild",
            "Live Wire ( Roll Dann Remix )",
            351,
            "A2",
        ),
        (
            f"{turl}/a3-gareth-wild-dds-locked-groove",
            "Gareth Wild",
            "DDS [Locked Groove]",
            20,
            "A3",
        ),
        (
            f"{turl}/aa1-gareth-wild-common-assault",
            "Gareth Wild",
            "Common Assault",
            315,
            "AA1",
        ),
        (
            f"{turl}/aa2-gareth-wild-saturn-storm",
            "Gareth Wild",
            "Saturn Storm",
            365,
            "AA2",
        ),
        (
            f"{turl}/aa3-gareth-wild-quadrant-locked-groove",
            "Gareth Wild",
            "Quadrant [Locked Groove]",
            414,
            "AA3",
        ),
    ]
    info.set_albuminfo(tracks)
    return codecs.open(test_html_file).read(), info


def compilation() -> Tuple[str, ReleaseInfo]:
    """An album with various artists."""
    test_html_file = "tests/compilation.html"
    info = ReleaseInfo(
        **{
            "image": "https://f4.bcbits.com/img/a4292881830_10.jpg",
            "album": "ISMVA003.3",
            "album_id": "https://ismusberlin.bandcamp.com/album/ismva0033",
            "albumartist": "Ismus",
            "artist_id": "https://ismusberlin.bandcamp.com",
            "label": "Ismus",
            "release_date": date(2020, 11, 29),
            "track_count": 13,
            "va": True,
        }
    )
    turl = "https://ismusberlin.bandcamp.com/track"
    tracks = [
        (
            f"{turl}/zebar-zimo-wish-granter-original-mix",
            "Zebar & Zimo",
            "Wish Granter (Original Mix)",
            414,
        ),
        (
            f"{turl}/alpha-tracks-valimba-original-mix",
            "Alpha Tracks",
            "Valimba (Original Mix)",
            361,
        ),
    ]
    info.set_albuminfo(tracks)
    return codecs.open(test_html_file).read(), info


@pytest.fixture(params=[album, compilation])
def multitracks(request) -> Tuple[str, ReleaseInfo]:
    return request.param()


# One track release: "https://mega-tech.bandcamp.com/track/matriark-arangel"
# Album: https://ute-rec.bandcamp.com/album/ute004"
# Compilation: https://ismusberlin.bandcamp.com/album/ismva0033
# Single track from EP (1hr long) https://sinensis-ute.bandcamp.com/track/live-at-parken
# Single track from comp: https://ismusberlin.bandcamp.com/track/zwyrg-point-of-no-return-original-mix  # noqa
# Single track release: https://lowincomesquad.bandcamp.com/track/li-ingle009-ytp-how-much-do-u-fucking-like-acid  # noqa
