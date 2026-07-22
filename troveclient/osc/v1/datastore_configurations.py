#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Database v1 Datastores action implementations"""

import json

from osc_lib.command import command

from troveclient import exceptions
from troveclient.i18n import _


class UpdateAllDatastoreConfiguration(command.Command):

    _description = _("Updates all configuration parameters for "
                     "a datastore version.")

    def get_parser(self, prog_name):
        parser = super(
            UpdateAllDatastoreConfiguration, self).get_parser(prog_name)
        parser.add_argument(
            'datastore_version',
            metavar='<datastore_version>',
            help=_('ID of the datastore version.')
        )
        parser.add_argument(
            'configuration_file',
            metavar='<configuration_file>',
            help=_('Path to a JSON with validation rules.')
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.database.mgmt_configs

        try:
            with open(parsed_args.configuration_file,
                      encoding='utf-8') as config_file:
                body = json.load(config_file)

            client.update_all(parsed_args.datastore_version,
                              body['configuration-parameters'])
        except Exception as exc:
            msg = _("Failed to update datastore configuration parameters: "
                    "%s") % exc
            raise exceptions.CommandError(msg)


class DeleteAllDatastoreConfiguration(command.Command):

    _description = _("Deletes all configuration parameters for "
                     "a datastore version.")

    def get_parser(self, prog_name):
        parser = super(
            DeleteAllDatastoreConfiguration, self).get_parser(prog_name)
        parser.add_argument(
            'datastore_version',
            metavar='<datastore_version>',
            help=_('ID of the datastore version.')
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.database.mgmt_configs

        try:
            client.delete_all(parsed_args.datastore_version)
        except Exception as exc:
            msg = _("Failed to delete datastore configuration parameters: "
                    "%s") % exc
            raise exceptions.CommandError(msg)
