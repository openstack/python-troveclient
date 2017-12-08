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
from troveclient.osc.v1 import database_instances
from troveclient.tests.osc.v1 import fakes


class TestInstances(fakes.TestDatabasev1):
    fake_instances = fakes.FakeInstances()

    def setUp(self):
        super(TestInstances, self).setUp()
        self.instance_client = self.app.client_manager.database.instances


class TestInstanceList(TestInstances):

    defaults = {
        'include_clustered': False,
        'limit': None,
        'marker': None
    }

    columns = database_instances.ListDatabaseInstances.columns
    values = ('1234', 'test-member-1', 'mysql', '5.6', 'ACTIVE', '02', 2,
              'regionOne')

    def setUp(self):
        super(TestInstanceList, self).setUp()
        self.cmd = database_instances.ListDatabaseInstances(self.app, None)
        self.data = [self.fake_instances.get_instances_1234()]
        self.instance_client.list.return_value = common.Paginated(self.data)

    def test_instance_list_defaults(self):
        parsed_args = self.check_parser(self.cmd, [], [])
        columns, data = self.cmd.take_action(parsed_args)
        self.instance_client.list.assert_called_once_with(**self.defaults)
        self.assertEqual(self.columns, columns)
        self.assertEqual([self.values], data)


class TestInstanceShow(TestInstances):

    values = ('mysql', '5.6', '02', '1234', '10.0.0.13',
              'test-member-1', 'regionOne', 'ACTIVE', 2)

    def setUp(self):
        super(TestInstanceShow, self).setUp()
        self.cmd = database_instances.ShowDatabaseInstance(self.app, None)
        self.data = self.fake_instances.get_instances_1234()
        self.instance_client.get.return_value = self.data
        self.columns = (
            'datastore',
            'datastore_version',
            'flavor',
            'id',
            'ip',
            'name',
            'region',
            'status',
            'volume',
        )

    def test_show(self):
        args = ['1234']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)


class TestDatabaseInstanceDelete(TestInstances):

    def setUp(self):
        super(TestDatabaseInstanceDelete, self).setUp()
        self.cmd = database_instances.DeleteDatabaseInstance(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_delete(self, mock_find):
        args = ['instance1']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.instance_client.delete.assert_called_with('instance1')
        self.assertIsNone(result)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_delete_with_exception(self, mock_find):
        args = ['fakeinstance']
        parsed_args = self.check_parser(self.cmd, args, [])

        mock_find.side_effect = exceptions.CommandError
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)
