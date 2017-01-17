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
from troveclient.osc.v1 import database_backups
from troveclient.tests.osc.v1 import fakes


class TestBackups(fakes.TestDatabasev1):
    fake_backups = fakes.FakeBackups()

    def setUp(self):
        super(TestBackups, self).setUp()
        self.mock_client = self.app.client_manager.database
        self.backup_client = self.app.client_manager.database.backups


class TestBackupList(TestBackups):

    defaults = {
        'datastore': None,
        'limit': None,
        'marker': None
    }

    columns = database_backups.ListDatabaseBackups.columns
    values = ('bk-1234', '1234', 'bkp_1', 'COMPLETED', None,
              '2015-05-16T14:23:08')

    def setUp(self):
        super(TestBackupList, self).setUp()
        self.cmd = database_backups.ListDatabaseBackups(self.app, None)
        data = [self.fake_backups.get_backup_bk_1234()]
        self.backup_client.list.return_value = common.Paginated(data)

    def test_backup_list_defaults(self):
        parsed_args = self.check_parser(self.cmd, [], [])
        columns, data = self.cmd.take_action(parsed_args)
        self.backup_client.list.assert_called_once_with(**self.defaults)
        self.assertEqual(self.columns, columns)
        self.assertEqual([self.values], data)
