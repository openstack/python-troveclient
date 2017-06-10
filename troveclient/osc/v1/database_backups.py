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

"""Database v1 Backups action implementations"""

from osc_lib.command import command
from osc_lib import utils as osc_utils

from troveclient.i18n import _


class ListDatabaseBackups(command.Lister):

    _description = _("List database backups")
    columns = ['ID', 'Instance ID', 'Name', 'Status', 'Parent ID',
               'Updated']

    def get_parser(self, prog_name):
        parser = super(ListDatabaseBackups, self).get_parser(prog_name)
        parser.add_argument(
            '--limit',
            dest='limit',
            metavar='<limit>',
            default=None,
            help=_('Return up to N number of the most recent bcakups.')
        )
        parser.add_argument(
            '--marker',
            dest='marker',
            metavar='<ID>',
            type=str,
            default=None,
            help=_('Begin displaying the results for IDs greater than the'
                   'specified marker. When used with :option:`--limit,` set'
                   'this to the last ID displayed in the previous run.')
        )
        parser.add_argument(
            '--datastore',
            dest='datastore',
            metavar='<datastore>',
            default=None,
            help=_('ID or name of the datastore (to filter backups by).')
        )
        return parser

    def take_action(self, parsed_args):
        database_backups = self.app.client_manager.database.backups
        items = database_backups.list(limit=parsed_args.limit,
                                      datastore=parsed_args.datastore,
                                      marker=parsed_args.marker)
        backups = items
        while items.next and not parsed_args.limit:
            items = database_backups.list(marker=items.next)
            backups += items
        backups = [osc_utils.get_item_properties(b, self.columns)
                   for b in backups]
        return self.columns, backups
