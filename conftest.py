"""Fixtures / data prep for testing."""
from datetime import datetime

import pytest
from beets.autotag.hooks import TrackInfo
from bs4 import BeautifulSoup

COMP_META_SOUP = BeautifulSoup(
    """
<meta content="
01010100 Various Artists 001 by 01010100 Records, released 14 August 2020

1. Achat - Kamino Disrespect
2. DAKTIK - Circus Of Delirium
3. SlugoS - Naturaleza Muerta

[TVA001]
" name="description"/>
    """,
    features="html.parser",
)

ALBUM_META_SOUP = BeautifulSoup(
    """
<meta content="
Ekkert nema ískaldur veruleikinn by KULDABOLI, released 04 December 2020

1. Ég er bara ég
2. Ískaldur veruleikinn
3. Finn innri frið
4. Afi kenndi mér íslensku
5. Kuklari
6. Fönix úr ösku

Kuldaboli returns to bbbbbb records, this time with a 6-track EP on which his \
idiosyncratic sound of icy, cryptic electro fully emerges. BBB015 being the second \
release of Kuldaboli on bbbbbb records is destined to be a historical release for the \
Icelandic dance music scene and a very important one for Kuldaboli’s legacy.
The EP title ‘Ekkert nema ískaldur veruleikinn’ roughly translates to “nothing but the \
ice cold reality” and that is exactly what is delivered across the six tracks laden \
with poetic lyrics and spoken word.
" name="description"/>
    """,
    features="html.parser",
)

SINGLEARTIST_TRACK_SOUP = BeautifulSoup(
    """
<tr class="track_row_view linked" rel="tracknum=5">
<td class="play-col"><a aria-label="Play Kuklari" role="button">\
<div class="play_status disabled"></div></a></td>
<td class="track-number-col"><div class="track_number secondaryText">5.</div></td>
<td class="title-col">
<div class="title">
<a href="/track/kuklari"><span class="track-title">Kuklari</span></a>
<span class="time secondaryText">

            05:50

        </span>
</div>
</td>
<td class="info-col"><div class="info_link"><a href="/track/kuklari"></a></div></td>
<td class="download-col">
<div class="dl_link">
<a href="/track/kuklari?action=download">

        buy track

</a>
</div></td>
</tr>,
    """,
    features="html.parser",
)

COMP_TRACK_SOUP = BeautifulSoup(
    """
<tr class="track_row_view linked" rel="tracknum=1">
<td class="play-col"><a aria-label="Play Zebar &amp; Zimo - Wish Granter (Original Mix)" \
role="button"><div class="play_status disabled"></div></a></td>
<td class="track-number-col"><div class="track_number secondaryText">1.</div></td>
<td class="title-col">
<div class="title">
<a href="/track/zebar-zimo-wish-granter-original-mix"><span class="track-title">Zebar \
&amp; Zimo - Wish Granter (Original Mix)</span></a>
<span class="time secondaryText">

            06:54

        </span>
</div>
</td>
<td class="info-col"><div class="info_link">\
<a href="/track/zebar-zimo-wish-granter-original-mix"></a></div></td>
<td class="download-col">
<div class="dl_link">
<a href="/track/zebar-zimo-wish-granter-original-mix?action=download">

        buy track

</a>
</div></td>
</tr>
    """,
    features="html.parser",
)


def comp_meta():
    """Provide an example of html soup (compilation) metadata with expected values."""
    return {
        "html": COMP_META_SOUP,
        "url": "https://01010100.bandcamp.com/album/01010100-various-artists-001",
        "expected_data": {
            "album": "01010100 Various Artists 001",
            "album_id": "https://01010100.bandcamp.com/album/01010100-various-artists-001",
            # "album_id": -1,
            "artist": "01010100 Records",
            "artist_url": "https://01010100.bandcamp.com",
            "date": datetime(2020, 8, 14),
        },
    }


def album_meta():
    """Provide an example of html soup (album) metadata with expected values."""
    return {
        "html": ALBUM_META_SOUP,
        "url": "https://bbbbbbrecors.bandcamp.com/album/ekkert-nema-skaldur-veruleikinn",
        "expected_data": {
            "album": "Ekkert nema ískaldur veruleikinn",
            "album_id": "https://bbbbbbrecors.bandcamp.com/album/ekkert-nema-skaldur-veruleikinn",
            # "album_id": -1,
            "artist": "KULDABOLI",
            "artist_url": "https://bbbbbbrecors.bandcamp.com",
            "date": datetime(2020, 12, 4),
        },
    }


@pytest.fixture(params=[comp_meta, album_meta])
def html_meta(request):
    """Provide all html metas one by one for testing."""
    yield request.param()


def singleartist_track_soup():
    """Provide a track soup made by a single artist - artist here isn't available."""
    return {
        "soup": SINGLEARTIST_TRACK_SOUP,
        "url": "https://bbbbbbrecors.bandcamp.com/album/ekkert-nema-skaldur-veruleikinn",
        "album_artist": "Kuldaboli",
        "expected_data": [
            TrackInfo(
                "Kuklari",
                "https://bbbbbbrecors.bandcamp.com/track/kuklari",
                # -1,
                data_url="https://bbbbbbrecors.bandcamp.com/track/kuklari",
                index="5",
                length=350.0,
                artist="Kuldaboli",
            ),
        ],
    }


def comp_track_soup():
    """Provide a track soup from a compilation - artist is available."""
    return {
        "soup": COMP_TRACK_SOUP,
        "url": "https://ismusberlin.bandcamp.com/album/ismva0033",
        "album_artist": "Ismus",
        "expected_data": [
            TrackInfo(
                "Wish Granter (Original Mix)",
                "https://ismusberlin.bandcamp.com/track/zebar-zimo-wish-granter-original-mix",
                # -1,
                data_url="https://ismusberlin.bandcamp.com/track/zebar-zimo-wish-granter-original-mix",
                index="1",
                length=414.0,
                artist="Zebar & Zimo",
            ),
        ],
    }


@pytest.fixture(params=[singleartist_track_soup, comp_track_soup])
def tracks_soup(request):
    """Provide various track soups."""
    yield request.param()


