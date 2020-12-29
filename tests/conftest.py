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
    type: str  # song or album
    image: str  # url
    album: str  # <artist> - <single>
    album_artist: str
    label: str
    release_date: date
    va: bool
    track_count: int
    standalone_trackinfo = None  # type: TrackInfo
    _albuminfo = None  # type: AlbumInfo

    @property
    def albuminfo(self) -> AlbumInfo:
        return self._albuminfo

    @staticmethod
    def trackinfo(index: int, info: Tuple) -> TrackInfo:
        if len(info) == 4:
            track_url, artist, title, length = info  # type: str, str, str, int
            alt = None
        else:
            track_url, artist, title, length, alt = info  # type: str, str, str, int, bool

        return TrackInfo(
            title,
            track_url,
            index=index,
            length=length,
            data_url=track_url,
            artist=artist,
            track_alt=alt,
            data_source=DATA_SOURCE,
            media=MEDIA,
        )

    def set_albuminfo(self, url: str, tracks: List[Tuple]) -> None:
        self._albuminfo = AlbumInfo(
            self.album,
            url,
            self.album_artist,
            url,  # TODO: check mb instead
            tracks=[self.trackinfo(idx, track) for idx, track in enumerate(tracks, 1)],
            data_url=url,
            year=self.release_date.year,
            month=self.release_date.month,
            day=self.release_date.day,
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
    url = "https://mega-tech.bandcamp.com/track/matriark-arangel"
    info = ReleaseInfo(  # expected
        **{
            "type": "MusicRecording, Product",
            "image": "https://f4.bcbits.com/img/a2036476476_10.jpg",
            "album": "Matriark - Arangel",
            "album_artist": "Megatech",
            "label": "Megatech",
            "release_date": date(2020, 11, 9),
            "track_count": 1,
            "va": False,
        }
    )
    info.standalone_trackinfo = TrackInfo(
        info.album,
        url,
        length=421,
        artist=info.album_artist,
        artist_id=url,
        data_url=url,
        data_source=DATA_SOURCE,
        media=MEDIA,
    )
    return codecs.open(test_html_file, "r", "utf-8").read(), info


def single_track() -> Tuple[str, ReleaseInfo]:
    """Single track which is part of an album release."""
    test_html_file = "tests/single_track.html"
    album_url = "https://sinensis-ute.bandcamp.com/album/sine03"
    album_artist = "Alpha Tracks"
    info = ReleaseInfo(  # expected
        **{
            "type": "MusicAlbum",
            "image": "https://f4.bcbits.com/img/a0610664056_10.jpg",
            "album": "SINE03",
            "album_artist": album_artist,
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
    info.set_albuminfo(album_url, tracks)
    return codecs.open(test_html_file, "r", "utf-8").read(), info


def album() -> Tuple[str, ReleaseInfo]:
    """An album with a single artist."""
    test_html_file = "tests/album.html"
    url = "https://ute-rec.bandcamp.com/album/ute004"
    album_artist = "Mikkel Rev"
    info = ReleaseInfo(
        **{
            "type": "MusicAlbum",
            "image": "https://f4.bcbits.com/img/a1035657740_10.jpg",
            "album": "UTE004",
            "album_artist": album_artist,
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
    info.set_albuminfo(url, tracks)
    return codecs.open(test_html_file, "r", "utf-8").read(), info


def album_with_track_alt() -> Tuple[str, ReleaseInfo]:
    """An album with alternative track indexes."""
    test_html_file = "tests/track_alt.html"
    url = "https://foldrecords.bandcamp.com/album/fld001-gareth-wild-common-assault-ep"
    info = ReleaseInfo(
        **{
            "type": "Product, MusicRelease",
            "image": "https://f4.bcbits.com/img/a2798384948_10.jpg",
            "album": "FLD001 // Gareth Wild - Common Assault EP",
            "album_artist": "Gareth Wild",
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
    info.set_albuminfo(url, tracks)
    return codecs.open(test_html_file, "r", "utf-8").read(), info


def compilation() -> Tuple[str, ReleaseInfo]:
    """An album with various artists."""
    test_html_file = "tests/compilation.html"
    url = "https://ismusberlin.bandcamp.com/album/ismva0033"
    info = ReleaseInfo(
        **{
            "type": "MusicAlbum",
            "image": "https://f4.bcbits.com/img/a4292881830_10.jpg",
            "album": "ISMVA003.3",
            "album_artist": "Ismus",
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
    info.set_albuminfo(url, tracks)
    return codecs.open(test_html_file, "r", "utf-8").read(), info


@pytest.fixture(params=[single_track, album, compilation])
def multitracks(request) -> Tuple[str, ReleaseInfo]:
    return request.param()


# One track release: "https://mega-tech.bandcamp.com/track/matriark-arangel"
# Album: https://ute-rec.bandcamp.com/album/ute004"
# Compilation: https://ismusberlin.bandcamp.com/album/ismva0033
# Single track from EP (1hr long) https://sinensis-ute.bandcamp.com/track/live-at-parken
# Single track from comp: https://ismusberlin.bandcamp.com/track/zwyrg-point-of-no-return-original-mix  # noqa
# Single track release: https://lowincomesquad.bandcamp.com/track/li-ingle009-ytp-how-much-do-u-fucking-like-acid  # noqa
