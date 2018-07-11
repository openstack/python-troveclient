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

from osc_lib import utils

from troveclient import common
from troveclient import exceptions
from troveclient.osc.v1 import database_configurations
from troveclient.tests.osc.v1 import fakes


class TestConfigurations(fakes.TestDatabasev1):
    fake_configurations = fakes.FakeConfigurations()
    fake_configuration_params = fakes.FakeConfigurationParameters()

    def setUp(self):
        super(TestConfigurations, self).setUp()
        self.mock_client = self.app.client_manager.database
        self.configuration_client = (self.app.client_manager.database.
                                     configurations)
        self.instance_client = self.app.client_manager.database.instances
        self.configuration_params_client = (self.app.client_manager.
                                            database.configuration_parameters)


class TestConfigurationList(TestConfigurations):
    defaults = {
        'limit': None,
        'marker': None
    }

    columns = database_configurations.ListDatabaseConfigurations.columns
    values = ('c-123', 'test_config', '', 'mysql', '5.6')

    def setUp(self):
        super(TestConfigurationList, self).setUp()
        self.cmd = database_configurations.ListDatabaseConfigurations(self.app,
                                                                      None)
        data = [self.fake_configurations.get_configurations_c_123()]
        self.configuration_client.list.return_value = common.Paginated(data)

    def test_configuration_list_defaults(self):
        parsed_args = self.check_parser(self.cmd, [], [])
        columns, data = self.cmd.take_action(parsed_args)
        self.configuration_client.list.assert_called_once_with(**self.defaults)
        self.assertEqual(self.columns, columns)
        self.assertEqual([tuple(self.values)], data)


class TestConfigurationShow(TestConfigurations):

    values = ('2015-05-16T10:24:28', 'mysql', '5.6', '', 'c-123',
              'test_config', '2015-05-16T10:24:29', '{"max_connections": 5}')

    def setUp(self):
        super(TestConfigurationShow, self).setUp()
        self.cmd = database_configurations.ShowDatabaseConfiguration(self.app,
                                                                     None)
        self.data = self.fake_configurations.get_configurations_c_123()
        self.configuration_client.get.return_value = self.data
        self.columns = (
            'created',
            'datastore_name',
            'datastore_version_name',
            'description',
            'id',
            'name',
            'updated',
            'values',
        )

    def test_show(self):
        args = ['c-123']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)


class TestConfigurationParameterList(TestConfigurations):

    columns = database_configurations.\
        ListDatabaseConfigurationParameters.columns
    values = ('connect_timeout', 'integer', 2, 31536000, 'false')

    def setUp(self):
        super(TestConfigurationParameterList, self).setUp()
        self.cmd = database_configurations.\
            ListDatabaseConfigurationParameters(self.app, None)
        data = [self.fake_configuration_params.get_params_connect_timeout()]
        self.configuration_params_client.parameters.return_value =\
            common.Paginated(data)
        self.configuration_params_client.parameters_by_version.return_value =\
            common.Paginated(data)

    def test_configuration_parameters_list_defaults(self):
        args = ['d-123', '--datastore', 'mysql']
        verifylist = [
            ('datastore_version', 'd-123'),
            ('datastore', 'mysql'),
        ]
        parsed_args = self.check_parser(self.cmd, args, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual([tuple(self.values)], data)

    def test_configuration_parameters_list_with_version_id_exception(self):
        args = [
            'd-123',
        ]
        verifylist = [
            ('datastore_version', 'd-123'),
        ]
        parsed_args = self.check_parser(self.cmd, args, verifylist)
        self.assertRaises(exceptions.NoUniqueMatch,
                          self.cmd.take_action,
                          parsed_args)


class TestConfigurationParameterShow(TestConfigurations):

    values = ('d-123', 31536000, 2, 'connect_timeout', 'false', 'integer')

    def setUp(self):
        super(TestConfigurationParameterShow, self).setUp()
        self.cmd = database_configurations. \
            ShowDatabaseConfigurationParameter(self.app, None)
        data = self.fake_configuration_params.get_params_connect_timeout()
        self.configuration_params_client.get_parameter.return_value = data
        self.configuration_params_client.\
            get_parameter_by_version.return_value = data
        self.columns = (
            'datastore_version_id',
            'max',
            'min',
            'name',
            'restart_required',
            'type',
        )

    def test_configuration_parameter_show_defaults(self):
        args = ['d-123', 'connect_timeout', '--datastore', 'mysql']
        verifylist = [
            ('datastore_version', 'd-123'),
            ('parameter', 'connect_timeout'),
            ('datastore', 'mysql'),
        ]
        parsed_args = self.check_parser(self.cmd, args, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)

    def test_configuration_parameter_show_with_version_id_exception(self):
        args = [
            'd-123',
            'connect_timeout',
        ]
        verifylist = [
            ('datastore_version', 'd-123'),
            ('parameter', 'connect_timeout'),
        ]
        parsed_args = self.check_parser(self.cmd, args, verifylist)
        self.assertRaises(exceptions.NoUniqueMatch,
                          self.cmd.take_action,
                          parsed_args)


class TestDatabaseConfigurationDelete(TestConfigurations):

    def setUp(self):
        super(TestDatabaseConfigurationDelete, self).setUp()
        self.cmd = database_configurations.\
            DeleteDatabaseConfiguration(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_configuration_delete(self, mock_find):
        args = ['config1']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.configuration_client.delete.assert_called_with('config1')
        self.assertIsNone(result)

    @mock.patch.object(utils, 'find_resource')
    def test_configuration_delete_with_exception(self, mock_find):
        args = ['fakeconfig']
        parsed_args = self.check_parser(self.cmd, args, [])

        mock_find.side_effect = exceptions.CommandError
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)


class TestConfigurationCreate(TestConfigurations):

    values = ('2015-05-16T10:24:28', 'mysql', '5.6', '', 'c-123',
              'test_config', '2015-05-16T10:24:29', '{"max_connections": 5}')

    def setUp(self):
        super(TestConfigurationCreate, self).setUp()
        self.cmd = database_configurations.\
            CreateDatabaseConfiguration(self.app, None)
        self.data = self.fake_configurations.get_configurations_c_123()
        self.configuration_client.create.return_value = self.data
        self.columns = (
            'created',
            'datastore_name',
            'datastore_version_name',
            'description',
            'id',
            'name',
            'updated',
            'values',
        )

    def test_configuration_create_return_value(self):
        args = ['c-123', '{"max_connections": 5}',
                '--description', 'test_config',
                '--datastore', 'mysql',
                '--datastore_version', '5.6']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)

    def test_configuration_create(self):
        args = ['cgroup1', '{"param1": 1, "param2": 2}']
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)
        self.configuration_client.create.assert_called_with(
            'cgroup1',
            '{"param1": 1, "param2": 2}',
            description=None,
            datastore=None,
            datastore_version=None)

    def test_configuration_create_with_optional_args(self):
        args = ['cgroup2', '{"param3": 3, "param4": 4}',
                '--description', 'cgroup 2',
                '--datastore', 'mysql',
                '--datastore_version', '5.6']
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)
        self.configuration_client.create.assert_called_with(
            'cgroup2',
            '{"param3": 3, "param4": 4}',
            description='cgroup 2',
            datastore='mysql',
            datastore_version='5.6')


class TestConfigurationAttach(TestConfigurations):

    def setUp(self):
        super(TestConfigurationAttach, self).setUp()
        self.cmd = database_configurations.\
            AttachDatabaseConfiguration(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_configuration_attach(self, mock_find):
        args = ['instance1', 'config1']
        mock_find.side_effect = ['instance1', 'config1']
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.instance_client.modify.assert_called_with('instance1', 'config1')
        self.assertIsNone(result)


class TestConfigurationDetach(TestConfigurations):

    def setUp(self):
        super(TestConfigurationDetach, self).setUp()
        self.cmd = database_configurations.\
            DetachDatabaseConfiguration(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_configuration_detach(self, mock_find):
        args = ['instance2']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.instance_client.modify.assert_called_with('instance2')
        self.assertIsNone(result)


class TestConfigurationInstancesList(TestConfigurations):
    defaults = {
        'limit': None,
        'marker': None
    }

    columns = (
        database_configurations.ListDatabaseConfigurationInstances.columns)
    values = [('1', 'instance-1'),
              ('2', 'instance-2')]

    def setUp(self):
        super(TestConfigurationInstancesList, self).setUp()
        self.cmd = database_configurations.ListDatabaseConfigurationInstances(
            self.app, None)
        data = (
            self.fake_configurations.get_configuration_instances())
        self.configuration_client.instances.return_value = common.Paginated(
            data)

    @mock.patch.object(utils, 'find_resource')
    def test_configuration_instances_list(self, mock_find):
        args = ['c-123']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)


class TestConfigurationDefault(TestConfigurations):

    values = ('2', '98', '1', '15M')

    def setUp(self):
        super(TestConfigurationDefault, self).setUp()
        self.cmd = database_configurations.DefaultDatabaseConfiguration(
            self.app, None)
        self.data = (
            self.fake_configurations.get_default_configuration())
        self.instance_client.configuration.return_value = self.data
        self.columns = (
            'innodb_log_files_in_group',
            'max_user_connections',
            'skip-external-locking',
            'tmp_table_size',
        )

    @mock.patch.object(utils, 'find_resource')
    def test_default_database_configuration(self, mock_find):
        args = ['1234']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)
