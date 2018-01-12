#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import mock

from osc_lib import exceptions
from osc_lib import utils

from troveclient.osc.v1 import database_root
from troveclient.tests.osc.v1 import fakes


class TestRoot(fakes.TestDatabasev1):
    fake_root = fakes.FakeRoot()

    def setUp(self):
        super(TestRoot, self).setUp()
        self.mock_client = self.app.client_manager.database
        self.root_client = self.app.client_manager.database.root


class TestRootEnable(TestRoot):

    def setUp(self):
        super(TestRootEnable, self).setUp()
        self.cmd = database_root.EnableDatabaseRoot(self.app, None)
        self.data = {
            'instance': self.fake_root.post_instance_1234_root(),
            'cluster': self.fake_root.post_cls_1234_root()
        }
        self.columns = ('name', 'password',)

    @mock.patch.object(utils, 'find_resource')
    def test_enable_instance_1234_root(self, mock_find):
        self.root_client.create_instance_root.return_value = (
            self.data['instance'])
        args = ['1234']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(('root', 'password',), data)

    @mock.patch.object(utils, 'find_resource')
    def test_enable_cluster_1234_root(self, mock_find):
        mock_find.side_effect = [exceptions.CommandError(),
                                 (None, 'cluster')]
        self.root_client.create_cluster_root.return_value = (
            self.data['cluster'])
        args = ['1234']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(('root', 'password',), data)

    @mock.patch.object(utils, 'find_resource')
    def test_enable_instance_root_with_password(self, mock_find):
        args = ['1234', '--root_password', 'secret']
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)
        self.root_client.create_instance_root(None,
                                              root_password='secret')

    @mock.patch.object(utils, 'find_resource')
    def test_enable_cluster_root_with_password(self, mock_find):
        args = ['1234', '--root_password', 'secret']
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)
        self.root_client.create_cluster_root(None,
                                             root_password='secret')


class TestRootDisable(TestRoot):

    def setUp(self):
        super(TestRootDisable, self).setUp()
        self.cmd = database_root.DisableDatabaseRoot(self.app, None)
        self.data = self.fake_root.delete_instance_1234_root()

    @mock.patch.object(utils, 'find_resource')
    def test_disable_instance_1234_root(self, mock_find):
        self.root_client.disable_instance_root.return_value = self.data
        args = ['1234']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.root_client.disable_instance_root.assert_called_with('1234')
        self.assertIsNone(result)


class TestRootShow(TestRoot):

    def setUp(self):
        super(TestRootShow, self).setUp()
        self.cmd = database_root.ShowDatabaseRoot(self.app, None)
        self.data = {
            'instance': self.fake_root.get_instance_1234_root(),
            'cluster': self.fake_root.get_cls_1234_root()
        }
        self.columns = ('is_root_enabled',)

    @mock.patch.object(utils, 'find_resource')
    def test_show_instance_1234_root(self, mock_find):
        self.root_client.is_instance_root_enabled.return_value = (
            self.data['instance'])
        args = ['1234']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(('True',), data)

    @mock.patch.object(utils, 'find_resource')
    def test_show_cluster_1234_root(self, mock_find):
        mock_find.side_effect = [exceptions.CommandError(),
                                 (None, 'cluster')]
        self.root_client.is_cluster_root_enabled.return_value = (
            self.data['cluster'])
        args = ['1234']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(('True',), data)
