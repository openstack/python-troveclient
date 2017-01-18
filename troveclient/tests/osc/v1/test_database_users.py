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
from troveclient.osc.v1 import database_users
from troveclient.tests.osc.v1 import fakes


class TestUsers(fakes.TestDatabasev1):
    fake_users = fakes.FakeUsers()

    def setUp(self):
        super(TestUsers, self).setUp()
        self.user_client = self.app.client_manager.database.users


class TestUserList(TestUsers):
    columns = database_users.ListDatabaseUsers.columns
    values = ('harry', '%', 'db1')

    def setUp(self):
        super(TestUserList, self).setUp()
        self.cmd = database_users.ListDatabaseUsers(self.app, None)
        data = [self.fake_users.get_instances_1234_users_harry()]
        self.user_client.list.return_value = common.Paginated(data)

    def test_user_list_defaults(self):
        args = ['my_instance']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.user_client.list.assert_called_once_with(*args)
        self.assertEqual(self.columns, columns)
        self.assertEqual([self.values], data)
