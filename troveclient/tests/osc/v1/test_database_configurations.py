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
from troveclient.osc.v1 import database_configurations
from troveclient.tests.osc.v1 import fakes


class TestConfigurations(fakes.TestDatabasev1):
    fake_configurations = fakes.FakeConfigurations()

    def setUp(self):
        super(TestConfigurations, self).setUp()
        self.mock_client = self.app.client_manager.database
        self.configuration_client = (self.app.client_manager.database.
                                     configurations)


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
