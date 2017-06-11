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
