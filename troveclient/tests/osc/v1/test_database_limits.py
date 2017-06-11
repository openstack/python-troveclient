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
from troveclient.osc.v1 import database_limits
from troveclient.tests.osc.v1 import fakes


class TestLimits(fakes.TestDatabasev1):
    fake_limits = fakes.FakeLimits()

    def setUp(self):
        super(TestLimits, self).setUp()
        self.limit_client = self.app.client_manager.database.limits


class TestLimitList(TestLimits):
    columns = database_limits.ListDatabaseLimits.columns
    non_absolute_values = (200, 'DELETE', 200, 'MINUTE')

    def setUp(self):
        super(TestLimitList, self).setUp()
        self.cmd = database_limits.ListDatabaseLimits(self.app, None)
        data = [self.fake_limits.get_absolute_limits(),
                self.fake_limits.get_non_absolute_limits()]
        self.limit_client.list.return_value = common.Paginated(data)

    def test_limit_list_defaults(self):
        parsed_args = self.check_parser(self.cmd, [], [])
        columns, data = self.cmd.take_action(parsed_args)
        self.limit_client.list.assert_called_once_with()
        self.assertEqual(self.columns, columns)
        self.assertEqual([self.non_absolute_values], data)
