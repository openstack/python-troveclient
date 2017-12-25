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

"""Database v1 Databases action implementations"""

from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils

from troveclient.i18n import _


class CreateDatabase(command.Command):

    _description = _("Creates a database on an instance.")

    def get_parser(self, prog_name):
        parser = super(CreateDatabase, self).get_parser(prog_name)
        parser.add_argument(
            "instance",
            metavar="<instance>",
            help=_("ID or name of the instance."),
        )
        parser.add_argument(
            "name",
            metavar="<name>",
            help=_("Name of the database."),
        )
        parser.add_argument(
            "--character_set",
            metavar="<character_set>",
            help=_("Optional character set for database."),
        )
        parser.add_argument(
            "--collate",
            metavar="<collate>",
            help=_("Optional collation type for database."),
        )
        return parser

    def take_action(self, parsed_args):
        manager = self.app.client_manager.database
        databases = manager.databases
        instance = utils.find_resource(manager.instances, parsed_args.instance)
        database_dict = {'name': parsed_args.name}
        if parsed_args.collate:
            database_dict['collate'] = parsed_args.collate
        if parsed_args.character_set:
            database_dict['character_set'] = parsed_args.character_set
        databases.create(instance, [database_dict])


class ListDatabases(command.Lister):

    _description = _("Get a list of all Databases from the instance.")
    columns = ['Name']

    def get_parser(self, prog_name):
        parser = super(ListDatabases, self).get_parser(prog_name)
        parser.add_argument(
            dest='instance',
            metavar='<instance>',
            help=_('ID or name of the instance.')
        )
        return parser

    def take_action(self, parsed_args):
        manager = self.app.client_manager.database
        databases = manager.databases
        instance = utils.find_resource(manager.instances, parsed_args.instance)
        items = databases.list(instance)
        dbs = items
        while items.next:
            items = databases.list(instance, marker=items.next)
            dbs += items
        dbs = [utils.get_item_properties(db, self.columns) for db in dbs]
        return self.columns, dbs


class DeleteDatabase(command.Command):

    _description = _("Deletes a database from an instance.")

    def get_parser(self, prog_name):
        parser = super(DeleteDatabase, self).get_parser(prog_name)
        parser.add_argument(
            dest='instance',
            metavar='<instance>',
            help=_('ID or name of the instance.')
        )
        parser.add_argument(
            dest='database',
            metavar='<database>',
            help=_('Name of the database.')
        )
        return parser

    def take_action(self, parsed_args):
        manager = self.app.client_manager.database
        databases = manager.databases
        try:
            instance = utils.find_resource(manager.instances,
                                           parsed_args.instance)
            databases.delete(instance, parsed_args.database)
        except Exception as e:
            msg = (_("Failed to delete database %(database)s: %(e)s")
                   % {'database': parsed_args.database, 'e': e})
            raise exceptions.CommandError(msg)
