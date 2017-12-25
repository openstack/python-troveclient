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

from troveclient import common
from troveclient.osc.v1 import databases
from troveclient.tests.osc.v1 import fakes


class TestDatabases(fakes.TestDatabasev1):
    fake_databases = fakes.FakeDatabases()

    def setUp(self):
        super(TestDatabases, self).setUp()
        self.mock_client = self.app.client_manager.database
        self.database_client = self.app.client_manager.database.databases


class TestDatabaseCreate(TestDatabases):

    def setUp(self):
        super(TestDatabaseCreate, self).setUp()
        self.cmd = databases.CreateDatabase(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_database_create(self, mock_find):
        args = ['instance1', 'db1']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.database_client.create.assert_called_with('instance1',
                                                       [{'name': 'db1'}])
        self.assertIsNone(result)

    @mock.patch.object(utils, 'find_resource')
    def test_database_create_with_optional_args(self, mock_find):
        args = ['instance2', 'db2',
                '--character_set', 'utf8',
                '--collate', 'utf8_general_ci']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        database_dict = {'name': 'db2',
                         'collate': 'utf8_general_ci',
                         'character_set': 'utf8'}
        result = self.cmd.take_action(parsed_args)
        self.database_client.create.assert_called_with('instance2',
                                                       [database_dict])
        self.assertIsNone(result)


class TestDatabaseList(TestDatabases):
    columns = databases.ListDatabases.columns
    values = ('fakedb1',)

    def setUp(self):
        super(TestDatabaseList, self).setUp()
        self.cmd = databases.ListDatabases(self.app, None)
        data = [self.fake_databases.get_databases_1()]
        self.database_client.list.return_value = common.Paginated(data)

    @mock.patch.object(utils, 'find_resource')
    def test_database_list_defaults(self, mock_find):
        args = ['my_instance']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.database_client.list.assert_called_once_with(args[0])
        self.assertEqual(self.columns, columns)
        self.assertEqual([tuple(self.values)], data)


class TestDatabaseDelete(TestDatabases):

    def setUp(self):
        super(TestDatabaseDelete, self).setUp()
        self.cmd = databases.DeleteDatabase(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_database_delete(self, mock_find):
        args = ['instance1', 'db1']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.database_client.delete.assert_called_with('instance1', 'db1')
        self.assertIsNone(result)

    @mock.patch.object(utils, 'find_resource')
    def test_database_delete_with_exception(self, mock_find):
        args = ['fakeinstance', 'db1']
        parsed_args = self.check_parser(self.cmd, args, [])

        mock_find.side_effect = exceptions.CommandError
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)
