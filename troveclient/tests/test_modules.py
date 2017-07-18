# Copyright 2016 Tesora, Inc.
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
#

import mock
import os
import testtools

from troveclient.v1 import modules


class TestModules(testtools.TestCase):
    def setUp(self):
        super(TestModules, self).setUp()

        self.mod_init_patcher = mock.patch(
            'troveclient.v1.modules.Module.__init__',
            mock.Mock(return_value=None))
        self.addCleanup(self.mod_init_patcher.stop)
        self.mod_init_patcher.start()
        self.mods_init_patcher = mock.patch(
            'troveclient.v1.modules.Modules.__init__',
            mock.Mock(return_value=None))
        self.addCleanup(self.mods_init_patcher.stop)
        self.mods_init_patcher.start()

        self.module_name = 'mod_1'
        self.module_id = 'mod-id'
        self.module = mock.Mock()
        self.module.id = self.module_id
        self.module.name = self.module_name

        self.modules = modules.Modules()
        self.modules.api = mock.Mock()
        self.modules.api.client = mock.Mock()
        self.modules.resource_class = mock.Mock(return_value=self.module_name)

    def tearDown(self):
        super(TestModules, self).tearDown()

    def test_create(self):
        def side_effect_func(path, body, mod):
            return path, body, mod

        text_contents = "my_contents"
        binary_contents = os.urandom(20)
        for contents in [text_contents, binary_contents]:
            self.modules._create = mock.Mock(side_effect=side_effect_func)
            path, body, mod = self.modules.create(
                self.module_name, "test", contents,
                description="my desc",
                all_tenants=False,
                datastore="ds",
                datastore_version="ds-version",
                auto_apply=True,
                visible=True,
                live_update=False,
                priority_apply=False,
                apply_order=5,
                full_access=True)
            self.assertEqual("/modules", path)
            self.assertEqual("module", mod)
            self.assertEqual(self.module_name, body["module"]["name"])
            self.assertEqual("ds", body["module"]["datastore"]["type"])
            self.assertEqual("ds-version",
                             body["module"]["datastore"]["version"])
            self.assertFalse(body["module"]["all_tenants"])
            self.assertTrue(body["module"]["auto_apply"])
            self.assertTrue(body["module"]["visible"])
            self.assertFalse(body["module"]["live_update"])
            self.assertFalse(body["module"]["priority_apply"])
            self.assertEqual(5, body["module"]["apply_order"])
            self.assertTrue(body["module"]["full_access"])

    def test_update(self):
        resp = mock.Mock()
        resp.status_code = 200
        body = {'module': None}
        self.modules.api.client.put = mock.Mock(return_value=(resp, body))
        self.modules.update(self.module_id)
        self.modules.update(self.module_id, name='new_name')
        self.modules.update(self.module)
        self.modules.update(self.module, name='new_name')
        resp.status_code = 500
        self.assertRaises(Exception, self.modules.update, self.module_name)

    def test_list(self):
        page_mock = mock.Mock()
        self.modules._paginated = page_mock
        limit = "test-limit"
        marker = "test-marker"
        self.modules.list(limit, marker)
        page_mock.assert_called_with(
            "/modules", "modules", limit, marker, query_strings=None)

    def test_get(self):
        def side_effect_func(path, inst):
            return path, inst

        self.modules._get = mock.Mock(side_effect=side_effect_func)
        self.assertEqual(
            ('/modules/%s' % self.module_name, 'module'),
            self.modules.get(self.module_name))

    def test_delete(self):
        resp = mock.Mock()
        resp.status_code = 200
        body = None
        self.modules.api.client.delete = mock.Mock(return_value=(resp, body))
        self.modules.delete(self.module_name)
        self.modules.delete(self.module)
        resp.status_code = 500
        self.assertRaises(Exception, self.modules.delete, self.module_name)

    def _test_instances(self, expected_query=None):
        page_mock = mock.Mock()
        self.modules._paginated = page_mock
        limit = "test-limit"
        marker = "test-marker"
        if not expected_query:
            expected_query = {}
        self.modules.instances(self.module_name, limit, marker,
                               **expected_query)
        page_mock.assert_called_with("/modules/mod_1/instances",
                                     "instances", limit, marker,
                                     query_strings=expected_query)

    def test_instance_count(self):
        expected_query = {'include_clustered': True,
                          'count_only': True}
        self._test_instances(expected_query)

    def test_instances(self):
        expected_query = {'include_clustered': True}
        self._test_instances(expected_query)

    def test_reapply(self):
        resp = mock.Mock()
        resp.status_code = 200
        body = None
        self.modules.api.client.put = mock.Mock(return_value=(resp, body))
        self.modules.reapply(self.module_name)
        self.modules.reapply(self.module)
        resp.status_code = 500
        self.assertRaises(Exception, self.modules.reapply, self.module_name)
