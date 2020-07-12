# Copyright 2020 Catalyst Cloud
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from troveclient.osc.v1 import database_backup_strategy
from troveclient.tests.osc.v1 import fakes
from troveclient.v1 import backup_strategy


class TestBackupStrategy(fakes.TestDatabasev1):
    def setUp(self):
        super(TestBackupStrategy, self).setUp()
        self.manager = self.app.client_manager.database.backup_strategies


class TestBackupStrategyList(TestBackupStrategy):
    def setUp(self):
        super(TestBackupStrategyList, self).setUp()
        self.cmd = database_backup_strategy.ListDatabaseBackupStrategies(
            self.app, None)

    def test_list(self):
        item = backup_strategy.BackupStrategy(
            None,
            {
                'project_id': 'fake_project_id',
                'instance_id': 'fake_instance_id',
                'swift_container': 'fake_container'
            }
        )
        self.manager.list.return_value = [item]

        parsed_args = self.check_parser(self.cmd, [], [])
        columns, data = self.cmd.take_action(parsed_args)

        self.manager.list.assert_called_once_with(instance_id=None,
                                                  project_id=None)
        self.assertEqual(
            database_backup_strategy.ListDatabaseBackupStrategies.columns,
            columns)
        self.assertEqual(
            [('fake_project_id', 'fake_instance_id', 'fake_container')],
            data)


class TestBackupStrategyCreate(TestBackupStrategy):
    def setUp(self):
        super(TestBackupStrategyCreate, self).setUp()
        self.cmd = database_backup_strategy.CreateDatabaseBackupStrategy(
            self.app, None)

    def test_create(self):
        args = ['--instance-id', 'fake_instance_id', '--swift-container',
                'fake_container']
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)

        self.manager.create.assert_called_once_with(
            instance_id='fake_instance_id',
            swift_container='fake_container'
        )


class TestBackupStrategyDelete(TestBackupStrategy):
    def setUp(self):
        super(TestBackupStrategyDelete, self).setUp()
        self.cmd = database_backup_strategy.DeleteDatabaseBackupStrategy(
            self.app, None)

    def test_delete(self):
        args = ['--instance-id', 'fake_instance_id', '--project-id',
                'fake_project']
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)

        self.manager.delete.assert_called_once_with(
            project_id='fake_project',
            instance_id='fake_instance_id',
        )
