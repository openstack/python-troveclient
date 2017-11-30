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

"""Database v1 Configurations action implementations"""

import json
from osc_lib.command import command
from osc_lib import utils as osc_utils
import six

from troveclient.i18n import _


def set_attributes_for_print_detail(configuration):
    info = configuration._info.copy()
    info['values'] = json.dumps(configuration.values)
    del info['datastore_version_id']
    return info


class ListDatabaseConfigurations(command.Lister):

    _description = _("List database configurations")
    columns = ['ID', 'Name', 'Description', 'Datastore Name',
               'Datastore Version Name']

    def get_parser(self, prog_name):
        parser = super(ListDatabaseConfigurations, self).get_parser(prog_name)
        parser.add_argument(
            '--limit',
            dest='limit',
            metavar='<limit>',
            type=int,
            default=None,
            help=_('Limit the number of results displayed.')
        )
        parser.add_argument(
            '--marker',
            dest='marker',
            metavar='<ID>',
            help=_('Begin displaying the results for IDs greater than the '
                   'specified marker. When used with --limit, set this to '
                   'the last ID displayed in the previous run.')
        )
        return parser

    def take_action(self, parsed_args):
        db_configurations = self.app.client_manager.database.configurations
        config = db_configurations.list(limit=parsed_args.limit,
                                        marker=parsed_args.marker)
        config = [osc_utils.get_item_properties(c, self.columns)
                  for c in config]
        return self.columns, config


class ShowDatabaseConfiguration(command.ShowOne):
    _description = _("Shows details of a database configuration group.")

    def get_parser(self, prog_name):
        parser = super(ShowDatabaseConfiguration, self).get_parser(prog_name)
        parser.add_argument(
            'configuration_group',
            metavar='<configuration_group>',
            help=_('ID or name of the configuration group'),
        )
        return parser

    def take_action(self, parsed_args):
        db_configurations = self.app.client_manager.database.configurations
        configuration = osc_utils.find_resource(
            db_configurations, parsed_args.configuration_group)
        configuration = set_attributes_for_print_detail(configuration)
        return zip(*sorted(six.iteritems(configuration)))
