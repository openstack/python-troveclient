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

"""Database v1 Users action implementations"""

from osc_lib.command import command
from osc_lib import utils

from troveclient.i18n import _


class ListDatabaseUsers(command.Lister):

    _description = _("Lists the users for an instance.")
    columns = ['Name', 'Host', 'Databases']

    def get_parser(self, prog_name):
        parser = super(ListDatabaseUsers, self).get_parser(prog_name)
        parser.add_argument(
            dest='instance',
            metavar='<instance>',
            help=_('ID of the instance.')
        )
        return parser

    def take_action(self, parsed_args):
        db_users = self.app.client_manager.database.users
        items = db_users.list(parsed_args.instance)
        users = items
        while (items.next):
            items = db_users.list(parsed_args.instance, marker=items.next)
            users += items
        for user in users:
            db_names = [db['name'] for db in user.databases]
            user.databases = ', '.join(db_names)
        users = [utils.get_item_properties(u, self.columns) for u in users]
        return self.columns, users
