#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Calibre Plugin for CrossRef metadata import

Somewhat derived from https://github/maxchaos/calibre-crossref, but without
the dependency on Habanero and Requests.

Licenced under the MIT licence
"""
from __future__ import division

from calibre.ebooks.metadata.sources.base import Source
from calibre.ebooks.metadata.book.base import Metadata

import json
import urllib
import datetime


class CrossrefSource(Source):
    """Crossref Metatdata Source plugin"""

    name = 'CrossRef'
    description = 'Query crossref.org for metadata'
    action_type = 'current'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'John Beard'
    version = (1, 0, 0)
    minimum_calibre_version = (0, 8, 0)

    capabilities = frozenset(['identify'])
    touched_fields = frozenset(
        ['title', 'authors', 'publisher', 'pubdate', 'series', 'series_index']
    )

    def identify(self,
                 log, result_queue, abort,
                 title=None, authors=None, identifiers=None,
                 timeout=30):
        """Implement the Calibre Metadata Source plugin indentify method:

        Take information about the work (title, authors, DOI, etc) and
        look up on Crossref for matches, present these to the user
        """

        getter = CrossrefApiShim(CrossrefBasicApiProvider(), log)

        cands = []

        # Dispatch to the correct API interface according to the data we have
        if identifiers is not None and "doi" in identifiers:
            cands = getter.query_doi(identifiers['doi'])
        elif title:
            cands = getter.query_title(title, authors)

        for c in cands:
            result_queue.put(c)


class CrossrefApiShim(object):
    """Shim class between the plugin and a CrossRef API provider. The provider
    is currently a basic implementation, but could be expanded to something
    like Habanero in future.

    This class returns Calibre-compatible metadata, translated from whatever
    data structures the Crossref API provides (JSON).
    """

    def __init__(self, provider, log):
        self.api = provider
        self.log = log

        # list of fields we actually care about
        self.select = [
                'DOI', 'title', 'author', 'container-title', 'issued',
                'published-print', 'publisher',
                'volume', 'issue', 'page']

        self.limit = 5

    def _log_json_error(self, json):
        self.log.error(
            'Received message with status "{status}" '
            'and message type {messagetype}.\n '
            'Message is "{message}".'
            .format(status=json['status'],
                    messagetype=json['message-type'],
                    message=json['message'][0]['message']))

    def query_doi(self, doi):
        """
        Look up a work by DOI - should provide 0 or 1 results
        """

        self.log.debug("Getting work metadata by DOI: %s" % doi)

        id_dict = {'doi': doi}

        json = self.api.works(
            ids=id_dict, select=self.select, limit=self.limit)

        if json['status'] != 'ok':
            self._log_json_error(json)
            return None

        works = [json['message']]
        return [self._parse_work(work) for work in works]

    def query_title(self, title, authors):

        author_str = ' '.join(authors) if authors else None

        self.log.debug('Getting work by title "{title}" and authors "{author}"'
                       .format(title=title, author=author_str))

        json = self.api.works(query_author=author_str, query_title=title,
                              select=self.select, limit=self.limit)

        if json['status'] != 'ok':
            self._log_json_error(json)
            return None

        works = json['message']['items']
        return [self._parse_work(work) for work in works]

    def _parse_work(self, work):
        """Convert a list of works returned in CrossRef JSON to Calibre
        Metadata objects
        """

        title = work.get('title')[0]
        authors = self._parse_authors(work)

        # Now we have a title - init Calibre Metadata
        mi = Metadata(title, authors)

        doi = work.get('DOI')
        if doi:
            mi.set_identifier('doi', doi)

        pubdate = self._parse_pubdate(work)
        if pubdate:
            mi.pubdate = pubdate

        publisher = self._parse_publisher(work)
        if publisher:
            mi.publisher = publisher

        series = self._parse_series(work)
        if series:
            mi.series = series[0]
            mi.series_index = series[1]

        return mi

    def _parse_authors(self, json):
        json_authors = json.get('author', [])
        authors = []

        for author in json_authors:
            author_parts = [
                    author.get('given', ''),
                    author.get('family', '')]
            # Trim empty parts
            author_parts = [a for a in author_parts if a]
            authors.append(' '.join(author_parts))

        if not authors:
            authors = u'Unknown'

        return authors

    def _parse_pubdate(self, json):
        """Get publication date from json info"""

        date = None

        issued = json.get('issued')
        if issued is not None:
            date = self._parse_date(issued)

        pubprint = json.get('published-print')
        if date is None and pubprint is not None:
            date = self._parse_date(pubprint)

        event = json.get('work')
        if date is None and event is not None:
            # prefer start date
            event_date = event.get('start') or event.get('end')

            if event_date is not None:
                date = self._parse_date(event_date)

        # return whatever we found, or None if all failed
        return date

    def _parse_date(self, json_date):

        date_parts = json_date.get('date-parts')[0][:3]

        if len(date_parts) < 1:
            return None

        date = None

        # Default dates
        date_ints = [int(date_parts[0]), 1, 1]

        for i in range(1, len(date_parts)):
            date_ints[i] = int(date_parts[i])

        from calibre.utils.date import utc_tz
        date = datetime.datetime(*(d for d in date_ints), tzinfo=utc_tz)
        return date

    def _parse_publisher(self, json):

        return json.get('publisher')

    def _parse_series(self, json):

        series = json.get('container-title')

        if series is None:
            return None

        series = series[0]

        vol = int(json.get('volume', '1'))

        # hack for issues A-B which happens sometimes
        iss = int(json.get('issue', '1').split('-')[0])

        print(vol, iss)

        s_index = vol + (iss / 100)

        return (series, s_index)


class CrossrefBasicApiProvider(object):
    """
    Implement a very basic CrossRef API service, somewhat like Habanero, but
    just for the bits we need for this plugin.

    This class returns raw JSON from the Crossref API

    TODO: Allow to add email/API key
    """

    def works(self, ids=None, query=None, limit=None, select=None, **kwargs):
        """Basic implementation of the parts of the Habanero works interface
        that we need.

        If IDs is given with a DOI, this is used directly to return a single
        work.

        Otherwise, if a query is given, this is passed in directly
        """

        if ids is not None and 'doi' in ids:
            return self._work_by_doi(ids['doi'])
        else:
            # construct a generic query request
            rq_data = {
                'query': query,
                'rows': limit,
                'select': ','.join(select),
            }

            # strip empty fields
            rq_data = dict((k, v) for k, v in rq_data.items() if v)

            # Add kwarg queries (like query_title)
            rq_data.update(self._filter_query_dict(kwargs))

            # Rename query filters
            rq_data = self._rename_query_filters(rq_data)

            return self._works_by_query(rq_data)

        # unknown parameter combination
        return None

    def _filter_query_dict(self, x):
        """Find query_ prefixed dict items and return dict of only them"""
        return dict((k, x[k]) for k, v in x.items() if k.find('query_') == 0)

    def _rename_query_filters(self, x):
        """Transform kwarg parameter names into equivalents for the CrossRef
        API (stolen from Habanero)"""
        newkeys = [v.replace('container_title', 'container-title') for v in x]
        newkeys = [v.replace('query_', 'query.') for v in newkeys]
        mapping = dict(zip(x.keys(), newkeys))
        return {mapping[k]: v for k, v in x.items()}

    def _get_api_json(self, url):
        """Get JSON from an API URL.

        Returns None when there's an error
        """

        handle = urllib.urlopen(url)

        # Failed to get a good API hit - could just be unknown DOI, or a
        # malformed API query
        if handle.code != 200:
            return None

        data = handle.read()

        try:
            json_data = json.loads(data)
        except ValueError:
            # JSON decode error
            return None

        return json_data

    def _work_by_doi(self, doi):

        # Note: DOI is _not_ escaped, the slash is correct
        url = "https://api.crossref.org/works/" + doi

        return self._get_api_json(url)

    def _works_by_query(self, query_dict):

        query_str = urllib.urlencode(query_dict)
        url = "https://api.crossref.org/works?{query}".format(query=query_str)

        print(url)

        return self._get_api_json(url)
