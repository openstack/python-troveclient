# Copyright 2015 Tesora Inc.
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

from troveclient.v1 import root

"""
Unit tests for root.py
"""


class RootTest(testtools.TestCase):
    def setUp(self):
        super(RootTest, self).setUp()
        self.orig__init = root.Root.__init__
        root.Root.__init__ = mock.Mock(return_value=None)
        self.root = root.Root()
        self.root.api = mock.Mock()
        self.root.api.client = mock.Mock()

    def tearDown(self):
        super(RootTest, self).tearDown()
        root.Root.__init__ = self.orig__init

    def _get_mock_method(self):
        self._resp = mock.Mock()
        self._body = None
        self._url = None

        def side_effect_func(url, body=None):
            self._body = body
            self._url = url
            return (self._resp, body)

        return mock.Mock(side_effect=side_effect_func)

    def test_delete(self):
        self.root.api.client.delete = self._get_mock_method()
        self._resp.status_code = 200
        self.root.delete(1234)
        self.assertEqual('/instances/1234/root', self._url)
        self._resp.status_code = 400
        self.assertRaises(Exception, self.root.delete, 1234)
