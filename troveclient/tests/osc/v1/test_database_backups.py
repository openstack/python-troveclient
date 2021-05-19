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

from unittest import mock

from osc_lib import exceptions
from osc_lib import utils
from oslo_utils import uuidutils

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
              '2015-05-16T14:23:08', '262db161-d3e4-4218-8bde-5bd879fc3e61')

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
            'all_projects': False,
            'project_id': None
        }

        self.backup_client.list.assert_called_once_with(**params)
        self.assertEqual(self.columns, columns)
        self.assertEqual([self.values], data)

    @mock.patch('troveclient.utils.get_resource_id')
    def test_backup_list_by_instance_id(self, get_resource_id_mock):
        get_resource_id_mock.return_value = 'fake_uuid'

        parsed_args = self.check_parser(self.cmd, ["--instance-id", "fake_id"],
                                        [])
        self.cmd.take_action(parsed_args)

        params = {
            'datastore': None,
            'limit': None,
            'marker': None,
            'instance_id': 'fake_uuid',
            'all_projects': False,
            'project_id': None
        }

        self.backup_client.list.assert_called_once_with(**params)

    @mock.patch('troveclient.utils.get_resource_id')
    def test_backup_list_by_instance_name(self, get_resource_id_mock):
        get_resource_id_mock.return_value = 'fake_uuid'

        parsed_args = self.check_parser(self.cmd, ["--instance", "fake_name"],
                                        [])
        self.cmd.take_action(parsed_args)

        params = {
            'datastore': None,
            'limit': None,
            'marker': None,
            'instance_id': 'fake_uuid',
            'all_projects': False,
            'project_id': None
        }

        self.backup_client.list.assert_called_once_with(**params)
        get_resource_id_mock.assert_called_once_with(self.instance_client,
                                                     'fake_name')

    def test_backup_list_all_projects(self):
        parsed_args = self.check_parser(self.cmd, ["--all-projects"], [])
        self.cmd.take_action(parsed_args)

        params = {
            'datastore': None,
            'limit': None,
            'marker': None,
            'instance_id': None,
            'all_projects': True,
            'project_id': None
        }

        self.backup_client.list.assert_called_once_with(**params)

    def test_backup_list_by_project(self):
        parsed_args = self.check_parser(self.cmd, ["--project-id", "fake_id"],
                                        [])
        self.cmd.take_action(parsed_args)

        params = {
            'datastore': None,
            'limit': None,
            'marker': None,
            'instance_id': None,
            'all_projects': False,
            'project_id': 'fake_id'
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
              'bkp_1', None,
              '262db161-d3e4-4218-8bde-5bd879fc3e61',
              0.11, 'COMPLETED', '2015-05-16T14:23:08')

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
            'project_id',
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

    @mock.patch("troveclient.utils.get_resource_id_by_name")
    def test_backup_delete(self, mock_getid):
        args = ['backup1']
        mock_getid.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)
        self.backup_client.delete.assert_called_with('backup1')

    @mock.patch("troveclient.utils.get_resource_id_by_name")
    def test_backup_delete_with_exception(self, mock_getid):
        args = ['fakebackup']
        parsed_args = self.check_parser(self.cmd, args, [])

        mock_getid.side_effect = exceptions.CommandError
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)

    @mock.patch("troveclient.utils.get_resource_id_by_name")
    def test_backup_bulk_delete(self, mock_getid):
        backup_1 = uuidutils.generate_uuid()
        backup_2 = uuidutils.generate_uuid()
        mock_getid.return_value = backup_1

        args = ["fake_backup", backup_2]
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)

        mock_getid.assert_called_once_with(self.backup_client, "fake_backup")
        calls = [mock.call(backup_1), mock.call(backup_2)]
        self.backup_client.delete.assert_has_calls(calls)


class TestBackupCreate(TestBackups):

    values = ('2015-05-16T14:22:28', 'mysql', '5.6', 'v-56', None, 'bk-1234',
              '1234',
              'http://backup_srvr/database_backups/bk-1234.xbstream.gz.enc',
              'bkp_1', None,
              '262db161-d3e4-4218-8bde-5bd879fc3e61',
              0.11, 'COMPLETED', '2015-05-16T14:23:08')

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
            'project_id',
            'size',
            'status',
            'updated',
        )

    def test_backup_create_return_value(self):
        args = ['bk-1234', '--instance', self.random_uuid()]
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)

    @mock.patch('troveclient.utils.get_resource_id_by_name')
    def test_backup_create(self, mock_find):
        args = ['bk-1234-1', '--instance', '1234']
        mock_find.return_value = 'fake-instance-id'
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)
        self.backup_client.create.assert_called_with('bk-1234-1',
                                                     'fake-instance-id',
                                                     description=None,
                                                     parent_id=None,
                                                     incremental=False,
                                                     swift_container=None)

    @mock.patch('troveclient.utils.get_resource_id_by_name')
    def test_incremental_backup_create(self, mock_find):
        args = ['bk-1234-2', '--instance', '1234', '--description',
                'backup 1234', '--parent', '1234-1', '--incremental']
        mock_find.return_value = 'fake-instance-id'

        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)

        self.backup_client.create.assert_called_with('bk-1234-2',
                                                     'fake-instance-id',
                                                     description='backup 1234',
                                                     parent_id='1234-1',
                                                     incremental=True,
                                                     swift_container=None)

    def test_create_from_data_location(self):
        name = self.random_name('backup')
        ds_version = self.random_uuid()
        args = [name, '--restore-from', 'fake-remote-location',
                '--restore-datastore-version', ds_version, '--restore-size',
                '3']
        parsed_args = self.check_parser(self.cmd, args, [])

        self.cmd.take_action(parsed_args)

        self.backup_client.create.assert_called_with(
            name,
            None,
            restore_from='fake-remote-location',
            restore_ds_version=ds_version,
            restore_size=3,
        )

    def test_required_params_missing(self):
        args = [self.random_name('backup')]
        parsed_args = self.check_parser(self.cmd, args, [])
        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)


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
