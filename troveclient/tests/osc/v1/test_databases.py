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

from troveclient import common
from troveclient.osc.v1 import databases
from troveclient.tests.osc.v1 import fakes
from troveclient import utils


class TestDatabases(fakes.TestDatabasev1):
    fake_databases = fakes.FakeDatabases()

    def setUp(self):
        super(TestDatabases, self).setUp()
        self.mock_client = self.app.client_manager.database
        self.database_client = self.app.client_manager.database.databases


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
