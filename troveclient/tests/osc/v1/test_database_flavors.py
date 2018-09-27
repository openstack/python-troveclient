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

from troveclient.osc.v1 import database_flavors
from troveclient.tests.osc.v1 import fakes


class TestFlavors(fakes.TestDatabasev1):
    fake_flavors = fakes.FakeFlavors()

    def setUp(self):
        super(TestFlavors, self).setUp()
        self.mock_client = self.app.client_manager.database
        self.flavor_client = self.app.client_manager.database.flavors


class TestFlavorList(TestFlavors):
    columns = database_flavors.ListDatabaseFlavors.columns
    values = (1, 'm1.tiny', 512, '', '', '')

    def setUp(self):
        super(TestFlavorList, self).setUp()
        self.cmd = database_flavors.ListDatabaseFlavors(self.app, None)
        self.data = [self.fake_flavors.get_flavors_1()]
        self.flavor_client.list.return_value = self.data
        self.flavor_client.list_datastore_version_associated_flavors. \
            return_value = self.data

    def test_flavor_list_defaults(self):
        parsed_args = self.check_parser(self.cmd, [], [])
        columns, values = self.cmd.take_action(parsed_args)
        self.flavor_client.list.assert_called_once_with()
        self.assertEqual(self.columns, columns)
        self.assertEqual([self.values], values)

    def test_flavor_list_with_optional_args(self):
        args = ['--datastore-type', 'mysql',
                '--datastore-version-id', '5.6']
        parsed_args = self.check_parser(self.cmd, args, [])
        list_flavor_dict = {'datastore': 'mysql',
                            'version_id': '5.6'}
        columns, values = self.cmd.take_action(parsed_args)
        self.flavor_client.list_datastore_version_associated_flavors. \
            assert_called_once_with(**list_flavor_dict)
        self.assertEqual(self.columns, columns)
        self.assertEqual([self.values], values)


class TestFlavorShow(TestFlavors):

    values = (1, 'm1.tiny', 512)

    def setUp(self):
        super(TestFlavorShow, self).setUp()
        self.cmd = database_flavors.ShowDatabaseFlavor(self.app, None)
        self.data = self.fake_flavors.get_flavors_1()
        self.flavor_client.get.return_value = self.data
        self.columns = (
            'id',
            'name',
            'ram',
        )

    def test_flavor_show_defaults(self):
        args = ['m1.tiny']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)
