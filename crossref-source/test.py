#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# CrossRef plugin tests for calibre
# Copyright 2018 John Beard <john.j.beard@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (unicode_literals, division)

# Tests
# To run these tests, install the plugin, then use:
# calibre-debug -e test.py

if __name__ == '__main__':
    from calibre.ebooks.metadata.sources.test import (
        test_identify_plugin, title_test, authors_test)

    # List of wprks we match in the tests
    work_tests = {
        "paskin1999": [
            title_test("Toward unique identifiers", exact=True),
            authors_test(["N. Paskin"])
        ],
    }

    tests_list = [
        (
            {
                'title': 'Toward unique identifiers',
                'authors': ["N. Paskin"]
            },
            work_tests["paskin1999"]
        ),
        (
            {
                'identifiers': {
                    'doi': '10.1109/5.771073',
                },
            },
            work_tests["paskin1999"]
        ),
    ]

    test_identify_plugin("CrossRef", tests_list,
                         fail_missing_meta=False)


# vim: expandtab:shiftwidth=4:tabstop=4:softtabstop=4:textwidth=80
