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

import mock

from osc_lib import utils

from troveclient.osc.v1 import database_logs
from troveclient.tests.osc.v1 import fakes


class TestLogs(fakes.TestDatabasev1):
    fake_logs = fakes.FakeLogs()

    def setUp(self):
        super(TestLogs, self).setUp()
        self.instance_client = self.app.client_manager.database.instances


class TestLogList(TestLogs):

    columns = database_logs.ListDatabaseLogs.columns
    values = [('general', 'USER', 'Partial', '128', '4096', 'data_logs',
               'mysql-general'),
              ('slow_query', 'USER', 'Ready', '0', '128', 'None', 'None')]

    def setUp(self):
        super(TestLogList, self).setUp()
        self.cmd = database_logs.ListDatabaseLogs(self.app, None)
        data = self.fake_logs.get_logs()
        self.instance_client.log_list.return_value = data

    @mock.patch.object(utils, 'find_resource')
    def test_log_list(self, mock_find):
        args = ['instance']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)
