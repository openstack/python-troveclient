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
from troveclient.osc.v1 import database_clusters
from troveclient.tests.osc.v1 import fakes


class TestClusters(fakes.TestDatabasev1):
    fake_clusters = fakes.FakeClusters()

    def setUp(self):
        super(TestClusters, self).setUp()
        self.mock_client = self.app.client_manager.database
        self.cluster_client = self.app.client_manager.database.clusters


class TestClusterList(TestClusters):

    defaults = {
        'limit': None,
        'marker': None
    }

    columns = database_clusters.ListDatabaseClusters.columns
    values = ('cls-1234', 'test-clstr', 'vertica', '7.1', 'NONE')

    def setUp(self):
        super(TestClusterList, self).setUp()
        self.cmd = database_clusters.ListDatabaseClusters(self.app, None)
        data = [self.fake_clusters.get_clusters_cls_1234()]
        self.cluster_client.list.return_value = common.Paginated(data)

    def test_cluster_list_defaults(self):
        parsed_args = self.check_parser(self.cmd, [], [])
        columns, data = self.cmd.take_action(parsed_args)
        self.cluster_client.list.assert_called_once_with(**self.defaults)
        self.assertEqual(self.columns, columns)
        self.assertEqual([self.values], data)
