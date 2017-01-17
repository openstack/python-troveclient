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
from troveclient.osc.v1 import datastores
from troveclient.tests.osc.v1 import fakes


class TestDatastores(fakes.TestDatabasev1):
    fake_datastores = fakes.FakeDatastores()

    def setUp(self):
        super(TestDatastores, self).setUp()
        self.datastore_client = self.app.client_manager.database.datastores


class TestDatastoreList(TestDatastores):
    columns = datastores.ListDatastores.columns
    values = ('d-123', 'mysql')

    def setUp(self):
        super(TestDatastoreList, self).setUp()
        self.cmd = datastores.ListDatastores(self.app, None)
        data = [self.fake_datastores.get_datastores_d_123()]
        self.datastore_client.list.return_value = common.Paginated(data)

    def test_datastore_list_defaults(self):
        parsed_args = self.check_parser(self.cmd, [], [])
        columns, data = self.cmd.take_action(parsed_args)
        self.datastore_client.list.assert_called_once_with()
        self.assertEqual(self.columns, columns)
        self.assertEqual([self.values], data)
