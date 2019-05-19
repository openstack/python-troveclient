# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
import testtools

from troveclient import common


class CommonTest(testtools.TestCase):

    def test_check_for_exceptions(self):
        status = [400, 422, 500]
        for s in status:
            resp = mock.Mock()
            resp.status_code = s
            self.assertRaises(Exception,
                              common.check_for_exceptions, resp, "body")

    def test_append_query_strings(self):
        url = "test-url"
        self.assertEqual(url, common.append_query_strings(url))

        self.assertEqual(url, common.append_query_strings(
            url, limit=None, marker=None))

        limit = "test-limit"
        marker = "test-marker"
        result = common.append_query_strings(url, limit=limit, marker=marker)
        self.assertTrue(result.startswith(url + '?'))
        self.assertIn("limit=%s" % limit, result)
        self.assertIn("marker=%s" % marker, result)
        self.assertEqual(1, result.count('&'))

        opts = {}
        self.assertEqual(url, common.append_query_strings(
            url, limit=None, marker=None, **opts))

        opts = {'key1': 'value1', 'key2': None}
        result = common.append_query_strings(url, limit=None, marker=marker,
                                             **opts)
        self.assertTrue(result.startswith(url + '?'))
        self.assertEqual(1, result.count('&'))
        self.assertNotIn("limit=%s" % limit, result)
        self.assertIn("marker=%s" % marker, result)
        self.assertIn("key1=%s" % opts['key1'], result)
        self.assertNotIn("key2=%s" % opts['key2'], result)

        opts = {'key1': 'value1', 'key2': None, 'key3': False}
        result = common.append_query_strings(url, **opts)
        self.assertTrue(result.startswith(url + '?'))
        self.assertIn("key1=value1", result)
        self.assertNotIn("key2", result)
        self.assertIn("key3=False", result)


class PaginatedTest(testtools.TestCase):

    def setUp(self):
        super(PaginatedTest, self).setUp()
        self.items_ = ["item1", "item2"]
        self.next_marker_ = "next-marker"
        self.links_ = ["link1", "link2"]
        self.pgn = common.Paginated(self.items_, self.next_marker_,
                                    self.links_)

    def tearDown(self):
        super(PaginatedTest, self).tearDown()

    def test___init__(self):
        self.assertEqual(self.items_, self.pgn)
        self.assertEqual(self.next_marker_, self.pgn.next)
        self.assertEqual(self.links_, self.pgn.links)
