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
from troveclient.osc.v1 import database_users
from troveclient.tests.osc.v1 import fakes


class TestUsers(fakes.TestDatabasev1):
    fake_users = fakes.FakeUsers()

    def setUp(self):
        super(TestUsers, self).setUp()
        self.user_client = self.app.client_manager.database.users


class TestDatabaseUserCreate(TestUsers):

    def setUp(self):
        super(TestDatabaseUserCreate, self).setUp()
        self.cmd = database_users.CreateDatabaseUser(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_user_create(self, mock_find):
        args = ['instance1', 'user1', 'password1']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        user = {'name': 'user1', 'password': 'password1', 'databases': []}
        self.user_client.create.assert_called_with('instance1', [user])
        self.assertIsNone(result)

    @mock.patch.object(utils, 'find_resource')
    def test_user_create_with_optional_args(self, mock_find):
        args = ['instance2', 'user2', 'password2',
                '--host', '1.1.1.1',
                '--databases', 'db1', 'db2']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        user = {'name': 'user2', 'password': 'password2',
                'host': '1.1.1.1',
                'databases': [{'name': 'db1'}, {'name': 'db2'}]}
        self.user_client.create.assert_called_with('instance2', [user])
        self.assertIsNone(result)


class TestUserList(TestUsers):
    columns = database_users.ListDatabaseUsers.columns
    values = ('harry', '%', 'db1')

    def setUp(self):
        super(TestUserList, self).setUp()
        self.cmd = database_users.ListDatabaseUsers(self.app, None)
        data = [self.fake_users.get_instances_1234_users_harry()]
        self.user_client.list.return_value = common.Paginated(data)

    @mock.patch.object(utils, 'find_resource')
    def test_user_list_defaults(self, mock_find):
        args = ['my_instance']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.user_client.list.assert_called_once_with(*args)
        self.assertEqual(self.columns, columns)
        self.assertEqual([self.values], data)


class TestUserShow(TestUsers):
    values = ([{'name': 'db1'}], '%', 'harry')

    def setUp(self):
        super(TestUserShow, self).setUp()
        self.cmd = database_users.ShowDatabaseUser(self.app, None)
        self.data = self.fake_users.get_instances_1234_users_harry()
        self.user_client.get.return_value = self.data
        self.columns = (
            'databases',
            'host',
            'name',
        )

    @mock.patch.object(utils, 'find_resource')
    def test_user_show_defaults(self, mock_find):
        args = ['my_instance', 'harry']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)


class TestDatabaseUserDelete(TestUsers):

    def setUp(self):
        super(TestDatabaseUserDelete, self).setUp()
        self.cmd = database_users.DeleteDatabaseUser(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_user_delete(self, mock_find):
        args = ['userinstance', 'user1', '--host', '1.1.1.1']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.user_client.delete.assert_called_with('userinstance',
                                                   'user1',
                                                   '1.1.1.1')
        self.assertIsNone(result)

    @mock.patch.object(utils, 'find_resource')
    def test_user_delete_without_host(self, mock_find):
        args = ['userinstance2', 'user1']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.user_client.delete.assert_called_with('userinstance2',
                                                   'user1',
                                                   None)
        self.assertIsNone(result)

    @mock.patch.object(utils, 'find_resource')
    def test_user_delete_with_exception(self, mock_find):
        args = ['userfakeinstance', 'db1', '--host', '1.1.1.1']
        parsed_args = self.check_parser(self.cmd, args, [])

        mock_find.side_effect = exceptions.CommandError
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)


class TestDatabaseUserGrantAccess(TestUsers):

    def setUp(self):
        super(TestDatabaseUserGrantAccess, self).setUp()
        self.cmd = database_users.GrantDatabaseUserAccess(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_user_grant_access(self, mock_find):
        args = ['userinstance', 'user1', '--host', '1.1.1.1', 'db1']
        verifylist = [
            ('instance', 'userinstance'),
            ('name', 'user1'),
            ('host', '1.1.1.1'),
            ('databases', ['db1']),
        ]
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, verifylist)
        result = self.cmd.take_action(parsed_args)
        self.assertIsNone(result)


class TestDatabaseUserRevokeAccess(TestUsers):

    def setUp(self):
        super(TestDatabaseUserRevokeAccess, self).setUp()
        self.cmd = database_users.RevokeDatabaseUserAccess(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_user_grant_access(self, mock_find):
        args = ['userinstance', 'user1', '--host', '1.1.1.1', 'db1']
        verifylist = [
            ('instance', 'userinstance'),
            ('name', 'user1'),
            ('host', '1.1.1.1'),
            ('databases', 'db1'),
        ]
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, verifylist)
        result = self.cmd.take_action(parsed_args)
        self.assertIsNone(result)


class TestDatabaseUserShowAccess(TestUsers):
    columns = database_users.ShowDatabaseUserAccess.columns
    values = [('db_1',), ('db_2',)]

    def setUp(self):
        super(TestDatabaseUserShowAccess, self).setUp()
        self.cmd = database_users.ShowDatabaseUserAccess(self.app, None)
        self.data = self.fake_users.get_instances_1234_users_access()
        self.user_client.list_access.return_value = self.data

    @mock.patch.object(utils, 'find_resource')
    def test_user_grant_access(self, mock_find):
        args = ['userinstance', 'user1', '--host', '1.1.1.1']
        verifylist = [
            ('instance', 'userinstance'),
            ('name', 'user1'),
            ('host', '1.1.1.1'),
        ]
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)


class TestDatabaseUserUpdateAttributes(TestUsers):

    def setUp(self):
        super(TestDatabaseUserUpdateAttributes, self).setUp()
        self.cmd = database_users.UpdateDatabaseUserAttributes(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_user__update_attributes(self, mock_find):
        args = ['userinstance',
                'user1',
                '--host', '1.1.1.1',
                '--new_name', 'user2',
                '--new_password', '111111',
                '--new_host', '1.1.1.2']
        verifylist = [
            ('instance', 'userinstance'),
            ('name', 'user1'),
            ('host', '1.1.1.1'),
            ('new_name', 'user2'),
            ('new_password', '111111'),
            ('new_host', '1.1.1.2'),
        ]
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, verifylist)
        result = self.cmd.take_action(parsed_args)
        self.assertIsNone(result)
