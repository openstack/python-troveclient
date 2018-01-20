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

from troveclient.osc.v1 import database_quota
from troveclient.tests.osc.v1 import fakes


class TestQuota(fakes.TestDatabasev1):
    fake_quota = fakes.FakeQuota()

    def setUp(self):
        super(TestQuota, self).setUp()
        self.mock_client = self.app.client_manager.database
        self.quota_client = self.app.client_manager.database.quota


class TestQuotaShow(TestQuota):
    columns = database_quota.ShowDatabaseQuota.columns
    values = [('instances', 2, 1, 10),
              ('backups', 4, 3, 50),
              ('volumes', 6, 5, 40)]

    def setUp(self):
        super(TestQuotaShow, self).setUp()
        self.cmd = database_quota.ShowDatabaseQuota(self.app, None)
        self.data = self.fake_quota.get_quotas()
        self.quota_client.show.return_value = self.data

    def test_show_quotas(self):
        args = ['tenant_id']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)


class TestQuotaUpdate(TestQuota):

    def setUp(self):
        super(TestQuotaUpdate, self).setUp()
        self.cmd = database_quota.UpdateDatabaseQuota(self.app, None)
        self.data = self.fake_quota.fake_instances_quota
        self.quota_client.update.return_value = self.data

    def test_update_quota(self):
        args = ['tenant_id', 'instances', '51']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(('instances',), columns)
        self.assertEqual((51,), data)
