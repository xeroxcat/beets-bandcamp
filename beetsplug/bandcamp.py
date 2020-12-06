# Copyright (C) 2015 Ariel George
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; version 2.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""Adds bandcamp album search support to the autotagger. Requires the
BeautifulSoup library.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import re
from datetime import datetime
from typing import Dict, Optional, Tuple, Union

import beets
import beets.ui
import isodate
import requests
import six
from beets import plugins
from beets.autotag.hooks import AlbumInfo, Distance, TrackInfo
from bs4 import BeautifulSoup, element

from beetsplug import fetchart

USER_AGENT = 'beets/{0} +http://beets.radbox.org/'.format(beets.__version__)
BANDCAMP_SEARCH = 'http://bandcamp.com/search?q={query}&page={page}'
BANDCAMP_ALBUM = 'album'
BANDCAMP_ARTIST = 'band'
BANDCAMP_TRACK = 'track'
ARTIST_TITLE_DELIMITER = ' - '
HTML_ID_TRACKS = 'track_table'
HTML_CLASS_TRACK = 'track_row_view'

WORLDWIDE = 'XW'
DIGITAL_MEDIA = 'Digital Media'
BANDCAMP = 'bandcamp'


class BandcampPlugin(plugins.BeetsPlugin):

    def __init__(self):
        super(BandcampPlugin, self).__init__()
        self.config.add({
            'source_weight': 0.5,
            'min_candidates': 5,
            'lyrics': False,
            'art': False,
            'split_artist_title': False
        })
        self.import_stages = [self.imported]
        self.register_listener('pluginload', self.loaded)

    def loaded(self):
        # Add our own artsource to the fetchart plugin.
        # FIXME: This is ugly, but i didn't find another way to extend fetchart
        # without declaring a new plugin.
        if self.config['art']:
            for plugin in plugins.find_plugins():
                if isinstance(plugin, fetchart.FetchArtPlugin):
                    plugin.sources = [BandcampAlbumArt(plugin._log, self.config)] + plugin.sources
                    fetchart.ART_SOURCES['bandcamp'] = BandcampAlbumArt
                    fetchart.SOURCE_NAMES[BandcampAlbumArt] = 'bandcamp'
                    break

    def album_distance(self, items, album_info, mapping):
        """Returns the album distance.
        """
        dist = Distance()
        if hasattr(album_info, 'data_source') and album_info.data_source == 'bandcamp':
            dist.add('source', self.config['source_weight'].as_number())
        return dist

    def candidates(self, items, artist, album, va_likely, extra_tags=None):
        """Returns a list of AlbumInfo objects for bandcamp search results
        matching an album and artist (if not various).
        """
        return self.get_albums(album)

    def album_for_id(self, album_id):
        """Fetches an album by its bandcamp ID and returns an AlbumInfo object
        or None if the album is not found.
        """
        # We use album url as id, so we just need to fetch and parse the
        # album page.
        url = album_id
        return self.get_album_info(url)

    def item_candidates(self, item, artist, album):
        """Returns a list of TrackInfo objects from a bandcamp search matching
        a singleton.
        """
        if item.title:
            return self.get_tracks(item.title)
        if item.album:
            return self.get_tracks(item.album)
        if item.artist:
            return self.get_tracks(item.artist)
        return []

    def track_for_id(self, track_id):
        """Fetches a track by its bandcamp ID and returns a TrackInfo object
        or None if the track is not found.
        """
        url = track_id
        return self.get_track_info(url)

    def imported(self, session, task):
        """Import hook for fetching lyrics from bandcamp automatically.
        """
        if self.config['lyrics']:
            for item in task.imported_items():
                # Only fetch lyrics for items from bandcamp
                if hasattr(item, 'data_source') and item.data_source == 'bandcamp':
                    self.add_lyrics(item, True)

    def get_albums(self, query):
        """Returns a list of AlbumInfo objects for a bandcamp search query.
        """
        albums = []
        for url in self._search(query, BANDCAMP_ALBUM):
            album = self.get_album_info(url)
            if album is not None:
                albums.append(album)
        return albums

    @staticmethod
    def _get_album_metadata(meta: str, url: str) -> Dict[str, Union[str, datetime]]:
        meta_lines = [line for line in meta.splitlines() if line]

        # <release-name> by <artist>, released <day-of-the-month> <month-name> <year>
        core_data = next(filter(lambda x: " by " in x and ", released " in x, meta_lines))
        album, artist_date = core_data.split(" by ")
        artist, human_date = artist_date.split(", released ")

        # Even though there is an item_id in some urls in bandcamp, it's not
        # visible on the page and you can't search by the id, so we need to use
        # the url as id.
        return {
            "album": album,
            "album_id": url,
            "artist_url": url.split('/album/')[0],
            "artist": artist,
            "date": datetime.strptime(human_date, "%d %B %Y")
        }

    def get_album_info(self, url):
        """Returns an AlbumInfo object for a bandcamp album page.
        """
        def _report(msg: str, e: Exception, url: str = None) -> None:
            self._log.debug(f"{msg} {url!r}: {e}")

        try:
            html = self._get(url)
        except requests.exceptions.RequestException as e:
            _report("Communication error while fetching album", e, url)
        try:
            meta = html.find('meta')['content']  # contains all we need really
            alb = self._get_album_metadata(meta, url)
            tracks = []
            for row in html.find(id=HTML_ID_TRACKS).find_all(class_=HTML_CLASS_TRACK):
                try:
                    track = self._parse_album_track(row, url, alb['artist'])
                except BandcampException as e:
                    _report('Error: ', e, url)
                tracks.append(track)
        except (TypeError, AttributeError) as e:
            _report("Unexpected html while scraping album", e, url)

        return AlbumInfo(
            alb['album'],
            alb['album_id'],
            alb['artist'],
            alb['artist_url'],
            tracks,
            year=alb['date'].year,
            month=alb['date'].month,
            day=alb['date'].day,
            country=WORLDWIDE,
            media=DIGITAL_MEDIA,
            data_source=BANDCAMP,
            data_url=url
        )

    def get_tracks(self, query):
        """Returns a list of TrackInfo objects for a bandcamp search query.
        """
        track_urls = self._search(query, BANDCAMP_TRACK)
        return [self.get_track_info(url) for url in track_urls]

    def get_track_info(self, url):
        """Returns a TrackInfo object for a bandcamp track page.
        """
        try:
            html = self._get(url)
            name_section = html.find(id='name-section')
            title = name_section.find(attrs={'itemprop': 'name'}).text.strip()
            artist_url = url.split('/track/')[0]
            artist = name_section.find(attrs={'itemprop': 'byArtist'}).text.strip()
            if self.config['split_artist_title']:
                artist_from_title, title = self._split_artist_title(title)
                if artist_from_title is not None:
                    artist = artist_from_title

            try:
                duration = html.find('meta', attrs={'itemprop': 'duration'})['content']
                track_length = float(duration)
                if track_length == 0:
                    track_length = None
            except TypeError:
                track_length = None

            return TrackInfo(title, url, length=track_length, artist=artist,
                             artist_id=artist_url, data_source='bandcamp',
                             media='Digital Media', data_url=url)
        except requests.exceptions.RequestException as e:
            self._log.debug("Communication error while fetching track {0!r}: "
                            "{1}".format(url, e))

    def add_lyrics(self, item, write = False):
        """Fetch and store lyrics for a single item. If ``write``, then the
        lyrics will also be written to the file itself."""
        # Skip if the item already has lyrics.
        if item.lyrics:
            self._log.info('lyrics already present: {0}', item)
            return

        lyrics = self.get_item_lyrics(item)

        if lyrics:
            self._log.info('fetched lyrics: {0}', item)
        else:
            self._log.info('lyrics not found: {0}', item)
            return

        item.lyrics = lyrics

        if write:
            item.try_write()
        item.store()

    def get_item_lyrics(self, item):
        """Get the lyrics for item from bandcamp.
        """
        try:
            # The track id is the bandcamp url when item.data_source is bandcamp.
            html = self._get(item.mb_trackid)
            lyrics = html.find(attrs={'class': 'lyricsText'})
            if lyrics:
                return lyrics.text
        except requests.exceptions.RequestException as e:
            self._log.debug("Communication error while fetching lyrics for track {0!r}: "
                            "{1}".format(item.mb_trackid, e))
        return None

    def _search(self, query, search_type=BANDCAMP_ALBUM, page=1):
        """Returns a list of bandcamp urls for items of type search_type
        matching the query.
        """
        if search_type not in [BANDCAMP_ARTIST, BANDCAMP_ALBUM, BANDCAMP_TRACK]:
            self._log.debug('Invalid type for search: {0}'.format(search_type))
            return None

        try:
            urls = []
            # Search bandcamp until min_candidates results have been found or
            # we hit the last page in the results.
            while len(urls) < self.config['min_candidates'].as_number():
                self._log.debug('Searching {}, page {}'.format(search_type, page))
                results = self._get(BANDCAMP_SEARCH.format(query=query, page=page))
                clazz = 'searchresult {0}'.format(search_type)
                for result in results.find_all('li', attrs={'class': clazz}):
                    a = result.find(attrs={'class': 'heading'}).a
                    if a is not None:
                        urls.append(a['href'].split('?')[0])

                # Stop searching if we are on the last page.
                if not results.find('a', attrs={'class': 'next'}):
                    break
                page += 1

            return urls
        except requests.exceptions.RequestException as e:
            self._log.debug("Communication error while searching page {0} for {1!r}: "
                            "{2}".format(page, query, e))
            return []

    def _get(self, url):
        """Returns a BeautifulSoup object with the contents of url.
        """
        headers = {'User-Agent': USER_AGENT}
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        return BeautifulSoup(r.text, 'html.parser')

    @staticmethod
    def _parse_album_track(track_html: element.Tag, album_url: str, album_artist: str) -> TrackInfo:
        """Returns a TrackInfo derived from the html describing a track in a
        bandcamp album page.
        """
        info = list(filter(
                lambda x: x and "info" not in x and "buy track" not in x,
                map(lambda x: x.strip(), track_html.text.replace("\n", "").split("  "))
            )
        )
        if len(info) == 2:
            index_title, duration = info[0], info[1]
            index, title = index_title.split(".")
        else:
            index = track_html.find(class_='track_number').text.replace(".", "")
            title = track_html.find(class_='track-title').text
            duration = track_html.find(class_='time').text.replace("\n", "").replace(" ", "")

        split_duration = duration.split(":")
        hours = "0"
        if len(split_duration) == 3:
            hours = split_duration[0]
            split_duration.remove(hours)
        minutes, seconds = duration.split(':')
        preparse_duration = f'PT{hours}H{minutes}M{seconds}S'
        track_length = isodate.parse_duration(preparse_duration).total_seconds()

        artist, title = _split_artist_title(title)
        if not artist:
            artist = album_artist

        track_url = track_html.find(href=re.compile('/track'))
        if track_url is None:
            raise BandcampException(f'No track url (id) for track {index} - {title}')
        track_id = album_url.split("/album")[0] + track_url['href']

        return TrackInfo(title, track_id, index=index, length=track_length, artist=artist)


def _split_artist_title(title: str) -> Tuple[Optional[str], str]:
    """Returns artist and title by splitting title on ARTIST_TITLE_DELIMITER.
    """
    parts = title.split(ARTIST_TITLE_DELIMITER, maxsplit=1)
    if len(parts) == 1:
        return None, title
    return parts[0], parts[1]


class BandcampAlbumArt(fetchart.RemoteArtSource):
    NAME = u"Bandcamp"

    def get(self, album, plugin, paths):
        """Return the url for the cover from the bandcamp album page.
        This only returns cover art urls for bandcamp albums (by id).
        """
        if isinstance(album.mb_albumid, six.string_types) and 'bandcamp' in album.mb_albumid:
            try:
                headers = {'User-Agent': USER_AGENT}
                r = requests.get(album.mb_albumid, headers=headers)
                r.raise_for_status()
                album_html = BeautifulSoup(r.text, 'html.parser').find(id='tralbumArt')
                image_url = album_html.find('a', attrs={'class': 'popupImage'})['href']
                yield self._candidate(url=image_url,
                                      match=fetchart.Candidate.MATCH_EXACT)
            except requests.exceptions.RequestException as e:
                self._log.debug("Communication error getting art for {0}: {1}"
                                .format(album, e))
            except ValueError:
                pass


class BandcampException(Exception):
    pass
