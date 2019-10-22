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
from osc_lib import exceptions
from osc_lib import utils as osc_utils
import six

from troveclient.i18n import _


def set_attributes_for_print_detail(backup):
    info = backup._info.copy()
    if hasattr(backup, 'datastore'):
        info['datastore'] = backup.datastore['type']
        info['datastore_version'] = backup.datastore['version']
        info['datastore_version_id'] = backup.datastore['version_id']
    return info


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
                   'specified marker. When used with ``--limit``, set '
                   'this to the last ID displayed in the previous run.')
        )
        parser.add_argument(
            '--datastore',
            dest='datastore',
            metavar='<datastore>',
            default=None,
            help=_('ID or name of the datastore (to filter backups by).')
        )
        parser.add_argument(
            '--instance-id',
            default=None,
            help=_('Filter backups by database instance ID.')
        )
        parser.add_argument(
            '--all-projects',
            action='store_true',
            help=_('Get all the backups of all the projects(Admin only).')
        )
        return parser

    def take_action(self, parsed_args):
        database_backups = self.app.client_manager.database.backups
        items = database_backups.list(limit=parsed_args.limit,
                                      datastore=parsed_args.datastore,
                                      marker=parsed_args.marker,
                                      instance_id=parsed_args.instance_id,
                                      all_projects=parsed_args.all_projects)
        backups = items
        while items.next and not parsed_args.limit:
            items = database_backups.list(
                marker=items.next,
                datastore=parsed_args.datastore,
                instance_id=parsed_args.instance_id,
                all_projects=parsed_args.all_projects
            )
            backups += items

        backups = [osc_utils.get_item_properties(b, self.columns)
                   for b in backups]

        return self.columns, backups


class ListDatabaseInstanceBackups(command.Lister):

    _description = _("Lists available backups for an instance.")
    columns = ['ID', 'Instance ID', 'Name', 'Status', 'Parent ID',
               'Updated']

    def get_parser(self, prog_name):
        parser = super(ListDatabaseInstanceBackups, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            help=_('ID or name of the instance.')
        )
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
                   'specified marker. When used with ``--limit``, set '
                   'this to the last ID displayed in the previous run.')
        )
        return parser

    def take_action(self, parsed_args):
        database_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(database_instances,
                                           parsed_args.instance)
        items = database_instances.backups(instance, limit=parsed_args.limit,
                                           marker=parsed_args.marker)
        backups = items
        while items.next and not parsed_args.limit:
            items = database_instances.backups(instance, marker=items.next)
            backups += items
        backups = [osc_utils.get_item_properties(b, self.columns)
                   for b in backups]
        return self.columns, backups


class ShowDatabaseBackup(command.ShowOne):

    _description = _("Shows details of a database backup")

    def get_parser(self, prog_name):
        parser = super(ShowDatabaseBackup, self).get_parser(prog_name)
        parser.add_argument(
            'backup',
            metavar='<backup>',
            help=_('ID or name of the backup'),
        )
        return parser

    def take_action(self, parsed_args):
        database_backups = self.app.client_manager.database.backups
        backup = osc_utils.find_resource(database_backups, parsed_args.backup)
        backup = set_attributes_for_print_detail(backup)
        return zip(*sorted(six.iteritems(backup)))


class DeleteDatabaseBackup(command.Command):

    _description = _("Deletes a backup.")

    def get_parser(self, prog_name):
        parser = super(DeleteDatabaseBackup, self).get_parser(prog_name)
        parser.add_argument(
            'backup',
            metavar='<backup>',
            help=_('ID or name of the backup.')
        )
        return parser

    def take_action(self, parsed_args):
        database_backups = self.app.client_manager.database.backups
        try:
            backup = osc_utils.find_resource(database_backups,
                                             parsed_args.backup)
            database_backups.delete(backup)
        except Exception as e:
            msg = (_("Failed to delete backup %(backup)s: %(e)s")
                   % {'backup': parsed_args.backup, 'e': e})
            raise exceptions.CommandError(msg)


class CreateDatabaseBackup(command.ShowOne):

    _description = _("Creates a backup of an instance.")

    def get_parser(self, prog_name):
        parser = super(CreateDatabaseBackup, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            help=_('ID or name of the instance.')
        )
        parser.add_argument(
            'name',
            metavar='<name>',
            help=_('Name of the backup.')
        )
        parser.add_argument(
            '--description',
            metavar='<description>',
            default=None,
            help=_('An optional description for the backup.')
        )
        parser.add_argument(
            '--parent',
            metavar='<parent>',
            default=None,
            help=_('Optional ID of the parent backup to perform an'
                   ' incremental backup from.')
        )
        parser.add_argument(
            '--incremental',
            action='store_true',
            default=False,
            help=_('Create an incremental backup based on the last'
                   ' full or incremental backup. It will create a'
                   ' full backup if no existing backup found.')
        )
        return parser

    def take_action(self, parsed_args):
        manager = self.app.client_manager.database
        database_backups = manager.backups
        instance = osc_utils.find_resource(manager.instances,
                                           parsed_args.instance)
        backup = database_backups.create(parsed_args.name,
                                         instance,
                                         description=parsed_args.description,
                                         parent_id=parsed_args.parent,
                                         incremental=parsed_args.incremental)
        backup = set_attributes_for_print_detail(backup)
        return zip(*sorted(six.iteritems(backup)))


class DeleteDatabaseBackupExecution(command.Command):

    _description = _("Deletes an execution.")

    def get_parser(self, prog_name):
        parser = super(DeleteDatabaseBackupExecution, self).get_parser(
            prog_name)
        parser.add_argument(
            'execution',
            metavar='<execution>',
            help=_('ID of the execution to delete.')
        )
        return parser

    def take_action(self, parsed_args):
        database_backups = self.app.client_manager.database.backups
        database_backups.execution_delete(parsed_args.execution)
