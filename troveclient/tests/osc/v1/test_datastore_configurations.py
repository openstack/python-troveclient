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

import json
from unittest import mock

from troveclient import exceptions
from troveclient.osc.v1 import datastore_configurations
from troveclient.tests.osc.v1 import fakes


class TestDatastoreConfigurations(fakes.TestDatabasev1):

    def setUp(self):
        super(TestDatastoreConfigurations, self).setUp()
        self.configuration_client = (
            self.app.client_manager.database.mgmt_configs
        )


class TestUpdateAllDatastoreConfiguration(TestDatastoreConfigurations):

    def setUp(self):
        super(TestUpdateAllDatastoreConfiguration, self).setUp()
        self.cmd = datastore_configurations.UpdateAllDatastoreConfiguration(
            self.app, None)

    def test_update_all(self):
        body = {
            'configuration-parameters': [{
                'name': 'config_name',
                'restart_required': False,
                'type': 'integer',
                'max': 1000,
                'min': 1,
            }]
        }
        args = ['version-id', 'validation-rules.json']
        verifylist = [
            ('datastore_version', 'version-id'),
            ('configuration_file', 'validation-rules.json'),
        ]
        parsed_args = self.check_parser(self.cmd, args, verifylist)

        mock_file = mock.mock_open(read_data=json.dumps(body))
        with mock.patch('builtins.open', mock_file):
            result = self.cmd.take_action(parsed_args)

        mock_file.assert_called_once_with(
            'validation-rules.json', encoding='utf-8')
        self.configuration_client.update_all.assert_called_once_with(
            'version-id', body['configuration-parameters'])
        self.assertIsNone(result)

    def test_update_all_invalid_json(self):
        args = ['version-id', 'validation-rules.json']
        parsed_args = self.check_parser(self.cmd, args, [])

        mock_file = mock.mock_open(read_data='{invalid-json')
        with mock.patch('builtins.open', mock_file):
            self.assertRaises(
                exceptions.CommandError, self.cmd.take_action, parsed_args)

        self.configuration_client.update_all.assert_not_called()

    def test_update_all_error(self):
        body = {'configuration-parameters': []}
        args = ['version-id', 'validation-rules.json']
        parsed_args = self.check_parser(self.cmd, args, [])
        self.configuration_client.update_all.side_effect = (
            exceptions.CommandError)

        mock_file = mock.mock_open(read_data=json.dumps(body))
        with mock.patch('builtins.open', mock_file):
            self.assertRaises(
                exceptions.CommandError, self.cmd.take_action, parsed_args)

        self.configuration_client.update_all.assert_called_once_with(
            'version-id', [])


class TestDeleteAllDatastoreConfiguration(TestDatastoreConfigurations):

    def setUp(self):
        super(TestDeleteAllDatastoreConfiguration, self).setUp()
        self.cmd = datastore_configurations.DeleteAllDatastoreConfiguration(
            self.app, None)

    def test_delete_all(self):
        args = ['version-id']
        verifylist = [
            ('datastore_version', 'version-id'),
        ]
        parsed_args = self.check_parser(self.cmd, args, verifylist)

        result = self.cmd.take_action(parsed_args)
        self.configuration_client.delete_all.assert_called_once_with(
            'version-id')
        self.assertIsNone(result)

    def test_delete_all_error(self):
        args = ['version-id']
        parsed_args = self.check_parser(self.cmd, args, [])
        self.configuration_client.delete_all.side_effect = (
            exceptions.CommandError)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)
