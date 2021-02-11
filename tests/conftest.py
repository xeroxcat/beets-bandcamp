"""Data prep / fixtures for tests."""
import codecs
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Sequence, Tuple

import pytest
from beets.autotag.hooks import AlbumInfo, TrackInfo

from beetsplug.bandcamp._metaguru import DATA_SOURCE, NEW_BEETS, OFFICIAL

JSONDict = Dict[str, Any]


@dataclass
class ReleaseInfo:
    image: str
    album_id: str
    artist_id: str
    track_count: int
    media: str
    disctitle: str
    singleton = None  # type: TrackInfo
    albuminfo = None  # type: AlbumInfo

    def trackinfo(self, index: int, info: Tuple) -> TrackInfo:
        if len(info) == 4:
            track_id, artist, title, length = info
            alt = None
        else:
            track_id, artist, title, length, alt = info
        track_url = f"{self.artist_id}/track/{track_id}"

        return TrackInfo(
            title,
            track_url,
            index=index,
            length=length,
            data_url=self.album_id,
            artist=artist,
            artist_id=self.artist_id,
            track_alt=alt,
            data_source=DATA_SOURCE,
            media=self.media,
            medium=1,
            medium_index=index,
            medium_total=self.track_count,
            disctitle=self.disctitle,
        )

    def set_singleton(self, artist: str, title: str, length: int) -> None:
        self.singleton = TrackInfo(
            title,
            self.album_id,
            artist=artist,
            artist_id=self.artist_id,
            length=length,
            index=1,
            data_url=self.album_id,
            data_source=DATA_SOURCE,
            media=self.media,
        )

    def set_albuminfo(self, tracks: Sequence[Tuple], **kwargs) -> None:
        data = dict(
            data_url=self.album_id,
            year=kwargs["release_date"].year,
            month=kwargs["release_date"].month,
            day=kwargs["release_date"].day,
            label=kwargs["label"],
            va=kwargs["va"],
            albumtype=kwargs["albumtype"],
            catalognum=kwargs["catalognum"],
            country=kwargs["country"],
            mediums=kwargs["mediums"],
            albumstatus=OFFICIAL,
            media=self.media,
            data_source=DATA_SOURCE,
        )
        tracks = [self.trackinfo(idx, track) for idx, track in enumerate(tracks, 1)]
        if not NEW_BEETS:
            self.albuminfo = AlbumInfo(
                data["album"],
                self.album_id,
                data["albumartist"],
                self.artist_id,
                **data,
            )
        else:
            data.update(
                album=kwargs["album"],
                album_id=self.album_id,
                albumartist=kwargs["albumartist"],
                artist_id=self.artist_id,
            )
            self.albuminfo = AlbumInfo(tracks, **data)


@pytest.fixture
def single_track_release() -> Tuple[str, ReleaseInfo]:
    """Single track as a release on its own."""
    test_html_file = "tests/single.html"
    info = ReleaseInfo(
        image="https://f4.bcbits.com/img/a2036476476_10.jpg",
        artist_id="https://mega-tech.bandcamp.com",
        album_id="https://mega-tech.bandcamp.com/track/matriark-arangel",
        track_count=1,
        media="Digital Media",
        disctitle="",
    )
    info.set_singleton(artist="Matriark", title="Arangel", length=421)
    return codecs.open(test_html_file).read(), info


@pytest.fixture
def single_track_album_search() -> Tuple[str, ReleaseInfo]:
    """Single track which is part of an album release."""
    album_artist = "Alpha Tracks"
    track_url = "https://sinensis-ute.bandcamp.com/track/odondo"
    info = ReleaseInfo(
        image="https://f4.bcbits.com/img/a0610664056_10.jpg",
        artist_id="https://sinensis-ute.bandcamp.com",
        album_id="https://sinensis-ute.bandcamp.com/album/sine03",
        track_count=2,
        media="CD",
        disctitle="CD",
    )
    tracks = [
        ("live-at-parken", album_artist, "Live At PARKEN", 3600),
        ("odondo", album_artist, "Odondo", 371),
    ]
    info.set_albuminfo(
        tracks,
        album="SINE03",
        albumartist=album_artist,
        label="Sinensis",
        albumtype="ep",
        catalognum="SINE03",
        release_date=date(2020, 6, 16),
        va=False,
        country="NO",
        mediums=1,
    )
    return track_url, info


def album() -> Tuple[str, ReleaseInfo]:
    """An album with a single artist."""
    test_html_file = "tests/album.html"
    album_artist = "Mikkel Rev"
    info = ReleaseInfo(
        image="https://f4.bcbits.com/img/a1035657740_10.jpg",
        artist_id="https://ute-rec.bandcamp.com",
        album_id="https://ute-rec.bandcamp.com/album/ute004",
        track_count=4,
        media="Vinyl",
        disctitle='12" Vinyl',
    )
    tracks = [
        (
            "the-human-experience-empathy-mix",
            album_artist,
            "The Human Experience (Empathy Mix)",
            504,
        ),
        ("parallell", album_artist, "Parallell", 487),
        ("formulae", album_artist, "Formulae", 431),
        ("biotope", album_artist, "Biotope", 421),
    ]
    info.set_albuminfo(
        tracks,
        album="UTE004",
        albumartist=album_artist,
        albumtype="ep",
        catalognum="UTE004",
        label="Ute.Rec",
        release_date=date(2020, 7, 17),
        va=False,
        country="NO",
        mediums=1,
    )
    return codecs.open(test_html_file).read(), info


def album_with_track_alt() -> Tuple[str, ReleaseInfo]:
    """An album with alternative track indexes."""
    test_html_file = "tests/track_alt.html"
    artist_id = "https://foldrecords.bandcamp.com"
    info = ReleaseInfo(
        image="https://f4.bcbits.com/img/a2798384948_10.jpg",
        artist_id=artist_id,
        album_id=f"{artist_id}/album/fld001-gareth-wild-common-assault-ep",
        track_count=6,
        media="Vinyl",
        disctitle="FLD001 - Common Assault EP",
    )
    tracks = [
        (
            "a1-gareth-wild-live-wire",
            "Gareth Wild",
            "Live Wire",
            357,
            "A1",
        ),
        (
            "a2-gareth-wild-live-wire-roll-dann-remix",
            "Gareth Wild",
            "Live Wire ( Roll Dann Remix )",
            351,
            "A2",
        ),
        (
            "a3-gareth-wild-dds-locked-groove",
            "Gareth Wild",
            "DDS [Locked Groove]",
            20,
            "A3",
        ),
        (
            "aa1-gareth-wild-common-assault",
            "Gareth Wild",
            "Common Assault",
            315,
            "AA1",
        ),
        (
            "aa2-gareth-wild-saturn-storm",
            "Gareth Wild",
            "Saturn Storm",
            365,
            "AA2",
        ),
        (
            "aa3-gareth-wild-quadrant-locked-groove",
            "Gareth Wild",
            "Quadrant [Locked Groove]",
            20,
            "AA3",
        ),
    ]
    info.set_albuminfo(
        tracks,
        album="FLD001 // Gareth Wild - Common Assault EP",
        albumartist="Gareth Wild",
        albumtype="ep",
        catalognum="FLD001",
        label="FOLD RECORDS",
        release_date=date(2020, 11, 2),
        va=False,
        country="GB",
        mediums=1,
    )
    return codecs.open(test_html_file).read(), info


def compilation() -> Tuple[str, ReleaseInfo]:
    """An album with various artists."""
    test_html_file = "tests/compilation.html"
    info = ReleaseInfo(
        image="https://f4.bcbits.com/img/a4292881830_10.jpg",
        artist_id="https://ismusberlin.bandcamp.com",
        album_id="https://ismusberlin.bandcamp.com/album/ismva0033",
        track_count=13,
        media="Digital Media",
        disctitle="",
    )
    tracks = [
        (
            "zebar-zimo-wish-granter-original-mix",
            "Zebar & Zimo",
            "Wish Granter (Original Mix)",
            414,
        ),
        (
            "alpha-tracks-valimba-original-mix",
            "Alpha Tracks",
            "Valimba (Original Mix)",
            361,
        ),
    ]
    info.set_albuminfo(
        tracks,
        album="ISMVA003.3",
        albumartist="Various Artists",
        albumtype="compilation",
        catalognum="ISMVA003.3",
        label="Ismus",
        release_date=date(2020, 11, 29),
        va=True,
        country="DE",
        mediums=1,
    )
    return codecs.open(test_html_file).read(), info


def ep() -> Tuple[str, ReleaseInfo]:
    """An EP with various artists."""
    test_html_file = "tests/ep.html"
    info = ReleaseInfo(
        image="https://f4.bcbits.com/img/a4292881830_10.jpg",
        artist_id="https://fallingapart.bandcamp.com",
        album_id="https://fallingapart.bandcamp.com/album/fa010-kickdown-vienna",
        track_count=4,
        media="Vinyl",
        disctitle='12" Vinyl',
    )
    tracks = [
        (
            "je-nne-the-devils-not-s-bl-ck-s-he-is-p-inted-h-rd-mix",
            "jeånne",
            "the devil's not ås blåck ås he is påinted (hård mix)",
            385,
        ),
        (
            "je-nne-the-p-th-to-p-r-dise-begins-in-hell",
            "jeånne",
            "the påth to pårådise begins in hell",
            333,
        ),
        (
            "dj-disrespect-vienna-warm-up-mix",
            "DJ DISRESPECT",
            "VIENNA (WARM UP MIX",
            315,
        ),
        (
            "dj-disrespect-transition-athletic-mix",
            "DJ DISRESPECT",
            "TRANSITION (ATHLETIC MIX)",
            333,
        ),
    ]
    info.set_albuminfo(
        tracks,
        album="fa010 | Kickdown Vienna",
        albumartist="jeånne, DJ DISRESPECT",
        albumtype="ep",
        catalognum="fa010",
        label="falling apart",
        release_date=date(2020, 10, 9),
        va=False,
        country="DE",
        mediums=1,
    )
    return codecs.open(test_html_file).read(), info


@pytest.fixture
def ep_album() -> Tuple[str, ReleaseInfo]:
    return ep()


@pytest.fixture(params=[album, album_with_track_alt, compilation, ep])
def multitracks(request) -> Tuple[str, ReleaseInfo]:
    return request.param()
