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

from unittest import mock

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


class TestShowDatabaseInstanceLog(TestLogs):

    def setUp(self):
        super(TestShowDatabaseInstanceLog, self).setUp()
        self.cmd = database_logs.ShowDatabaseInstanceLog(self.app, None)
        self.columns = (
            'container',
            'metafile',
            'name',
            'pending',
            'prefix',
            'published',
            'status',
            'type',
        )

    @mock.patch.object(utils, 'find_resource')
    def test_show_instance_log(self, mock_find):
        mock_find.return_value = 'fake_instance_id'
        data = self.fake_logs.get_logs()[0]
        self.instance_client.log_show.return_value = data

        args = ['instance', 'logname']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, values = self.cmd.take_action(parsed_args)

        self.assertEqual(self.columns, columns)
        self.assertCountEqual(data.to_dict().values(), values)


class TestSetDatabaseInstanceLog(TestLogs):
    def setUp(self):
        super(TestSetDatabaseInstanceLog, self).setUp()
        self.cmd = database_logs.SetDatabaseInstanceLog(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_set_instance_log(self, mock_find):
        mock_find.return_value = 'fake_instance_id'
        data = self.fake_logs.get_logs()[0]
        data.status = 'Ready'
        self.instance_client.log_action.return_value = data

        args = ['instance1', 'log_name', '--enable']
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)

        self.instance_client.log_action.assert_called_once_with(
            'fake_instance_id', 'log_name',
            enable=True,
            disable=False,
            discard=False,
            publish=False
        )
