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
    track_count: int
    standalone_trackinfo = None  # type: TrackInfo
    _albuminfo = None  # type: AlbumInfo

    @property
    def albuminfo(self) -> AlbumInfo:
        return self._albuminfo

    def set_albuminfo(self, url: str, tracks: List[TrackInfo]) -> None:
        trackinfos = [
            TrackInfo(
                title,
                track_url,
                index=index,
                length=length,
                data_url=track_url,
                artist=artist,
            )
            for index, (track_url, artist, title, length) in enumerate(tracks, 1)
        ]
        self._albuminfo = AlbumInfo(
            self.album,
            url,
            self.album_artist,
            url,  # TODO: check mb instead
            trackinfos,
            data_url=url,
            year=self.release_date.year,
            month=self.release_date.month,
            day=self.release_date.day,
            label=self.label,
            data_source=DATA_SOURCE,
            media=MEDIA,
            country=COUNTRY,
        )


@pytest.fixture
def single_track_release_soup() -> Tuple[str, ReleaseInfo]:
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


def single_track_soup() -> Tuple[str, ReleaseInfo]:
    test_html_file = "tests/single_track.html"
    # url = "https://sinensis-ute.bandcamp.com/track/live-at-parken"
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
        }
    )
    turl = "https://sinensis-ute.bandcamp.com/track"
    tracks = [
        (f"{turl}/live-at-parken", album_artist, "Live At PARKEN", 3600),
        (f"{turl}/odondo", album_artist, "Odondo", 371),
    ]
    info.set_albuminfo(album_url, tracks)
    return codecs.open(test_html_file, "r", "utf-8").read(), info


def album_soup() -> Tuple[str, ReleaseInfo]:
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


def compilation_soup() -> Tuple[str, ReleaseInfo]:
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


@pytest.fixture(params=[single_track_soup, album_soup, compilation_soup])
def multitracks_soup(request) -> Tuple[str, ReleaseInfo]:
    return request.param()


# One track release: "https://mega-tech.bandcamp.com/track/matriark-arangel"
# Album: https://ute-rec.bandcamp.com/album/ute004"
# Compilation: https://ismusberlin.bandcamp.com/album/ismva0033
# Single track from EP (1hr long) https://sinensis-ute.bandcamp.com/track/live-at-parken
# Single track from comp: https://ismusberlin.bandcamp.com/track/zwyrg-point-of-no-return-original-mix  # noqa
# Single track release: https://lowincomesquad.bandcamp.com/track/li-ingle009-ytp-how-much-do-u-fucking-like-acid  # noqa
