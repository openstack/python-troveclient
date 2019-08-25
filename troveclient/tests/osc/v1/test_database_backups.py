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
from troveclient.osc.v1 import database_backups
from troveclient.tests.osc.v1 import fakes


class TestBackups(fakes.TestDatabasev1):
    fake_backups = fakes.FakeBackups()

    def setUp(self):
        super(TestBackups, self).setUp()
        self.mock_client = self.app.client_manager.database
        self.backup_client = self.app.client_manager.database.backups
        self.instance_client = self.app.client_manager.database.instances


class TestBackupList(TestBackups):

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

        params = {
            'datastore': None,
            'limit': None,
            'marker': None,
            'instance_id': None,
            'all_projects': False
        }

        self.backup_client.list.assert_called_once_with(**params)
        self.assertEqual(self.columns, columns)
        self.assertEqual([self.values], data)

    def test_backup_list_by_instance_id(self):
        parsed_args = self.check_parser(self.cmd, ["--instance-id", "fake_id"],
                                        [])
        self.cmd.take_action(parsed_args)

        params = {
            'datastore': None,
            'limit': None,
            'marker': None,
            'instance_id': 'fake_id',
            'all_projects': False
        }

        self.backup_client.list.assert_called_once_with(**params)

    def test_backup_list_all_projects(self):
        parsed_args = self.check_parser(self.cmd, ["--all-projects"], [])
        self.cmd.take_action(parsed_args)

        params = {
            'datastore': None,
            'limit': None,
            'marker': None,
            'instance_id': None,
            'all_projects': True
        }

        self.backup_client.list.assert_called_once_with(**params)


class TestBackupListInstance(TestBackups):

    defaults = {
        'limit': None,
        'marker': None
    }

    columns = database_backups.ListDatabaseInstanceBackups.columns
    values = ('bk-1234', '1234', 'bkp_1', 'COMPLETED', None,
              '2015-05-16T14:23:08')

    def setUp(self):
        super(TestBackupListInstance, self).setUp()
        self.cmd = database_backups.ListDatabaseInstanceBackups(self.app, None)
        data = [self.fake_backups.get_backup_bk_1234()]
        self.instance_client.backups.return_value = common.Paginated(data)

    @mock.patch.object(utils, 'find_resource')
    def test_backup_list_defaults(self, mock_find):
        args = ['1234']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.instance_client.backups.assert_called_once_with('1234',
                                                             **self.defaults)
        self.assertEqual(self.columns, columns)
        self.assertEqual([self.values], data)


class TestBackupShow(TestBackups):

    values = ('2015-05-16T14:22:28', 'mysql', '5.6', 'v-56', None, 'bk-1234',
              '1234',
              'http://backup_srvr/database_backups/bk-1234.xbstream.gz.enc',
              'bkp_1', None, 0.11, 'COMPLETED', '2015-05-16T14:23:08')

    def setUp(self):
        super(TestBackupShow, self).setUp()
        self.cmd = database_backups.ShowDatabaseBackup(self.app, None)
        self.data = self.fake_backups.get_backup_bk_1234()
        self.backup_client.get.return_value = self.data
        self.columns = (
            'created',
            'datastore',
            'datastore_version',
            'datastore_version_id',
            'description',
            'id',
            'instance_id',
            'locationRef',
            'name',
            'parent_id',
            'size',
            'status',
            'updated',
        )

    def test_show(self):
        args = ['bkp_1']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)


class TestDatabaseBackupDelete(TestBackups):

    def setUp(self):
        super(TestDatabaseBackupDelete, self).setUp()
        self.cmd = database_backups.DeleteDatabaseBackup(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_backup_delete(self, mock_find):
        args = ['backup1']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.backup_client.delete.assert_called_with('backup1')
        self.assertIsNone(result)

    @mock.patch.object(utils, 'find_resource')
    def test_backup_delete_with_exception(self, mock_find):
        args = ['fakebackup']
        parsed_args = self.check_parser(self.cmd, args, [])

        mock_find.side_effect = exceptions.CommandError
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)


class TestBackupCreate(TestBackups):

    values = ('2015-05-16T14:22:28', 'mysql', '5.6', 'v-56', None, 'bk-1234',
              '1234',
              'http://backup_srvr/database_backups/bk-1234.xbstream.gz.enc',
              'bkp_1', None, 0.11, 'COMPLETED', '2015-05-16T14:23:08')

    def setUp(self):
        super(TestBackupCreate, self).setUp()
        self.cmd = database_backups.CreateDatabaseBackup(self.app, None)
        self.data = self.fake_backups.get_backup_bk_1234()
        self.backup_client.create.return_value = self.data
        self.columns = (
            'created',
            'datastore',
            'datastore_version',
            'datastore_version_id',
            'description',
            'id',
            'instance_id',
            'locationRef',
            'name',
            'parent_id',
            'size',
            'status',
            'updated',
        )

    def test_backup_create_return_value(self):
        args = ['1234', 'bk-1234']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)

    @mock.patch.object(utils, 'find_resource')
    def test_backup_create(self, mock_find):
        args = ['1234', 'bk-1234-1']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)
        self.backup_client.create.assert_called_with('bk-1234-1',
                                                     '1234',
                                                     description=None,
                                                     parent_id=None,
                                                     incremental=False)

    @mock.patch.object(utils, 'find_resource')
    def test_incremental_backup_create(self, mock_find):
        args = ['1234', 'bk-1234-2', '--description', 'backup 1234',
                '--parent', '1234-1', '--incremental']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)
        self.backup_client.create.assert_called_with('bk-1234-2',
                                                     '1234',
                                                     description='backup 1234',
                                                     parent_id='1234-1',
                                                     incremental=True)


class TestDatabaseBackupExecutionDelete(TestBackups):

    def setUp(self):
        super(TestDatabaseBackupExecutionDelete, self).setUp()
        self.cmd = database_backups.DeleteDatabaseBackupExecution(
            self.app, None)

    def test_execution_delete(self):
        args = ['execution']
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.backup_client.execution_delete.assert_called_with('execution')
        self.assertIsNone(result)
