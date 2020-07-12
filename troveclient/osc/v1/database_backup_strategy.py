# Copyright 2020 Catalyst Cloud
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from osc_lib.command import command
from osc_lib import utils as osc_utils

from troveclient.i18n import _


class ListDatabaseBackupStrategies(command.Lister):
    _description = _("List backup strategies")
    columns = ['Project ID', 'Instance ID', 'Swift Container']

    def get_parser(self, prog_name):
        parser = super(ListDatabaseBackupStrategies, self).get_parser(
            prog_name)

        parser.add_argument(
            '--instance-id',
            help=_('Filter results by database instance ID.')
        )
        parser.add_argument(
            '--project-id',
            help=_('Project ID in Keystone. Only admin user is allowed to '
                   'list backup strategy for other projects.')
        )

        return parser

    def take_action(self, parsed_args):
        manager = self.app.client_manager.database.backup_strategies
        result = manager.list(instance_id=parsed_args.instance_id,
                              project_id=parsed_args.project_id)
        backup_strategies = [osc_utils.get_item_properties(item, self.columns)
                             for item in result]

        return self.columns, backup_strategies


class CreateDatabaseBackupStrategy(command.ShowOne):
    _description = _("Creates backup strategy for the project or a particular "
                     "instance.")

    def get_parser(self, prog_name):
        parser = super(CreateDatabaseBackupStrategy, self).get_parser(
            prog_name)

        parser.add_argument(
            '--project-id',
            help=_('Project ID in Keystone. Only admin user is allowed to '
                   'create backup strategy for other projects.')
        )
        parser.add_argument(
            '--instance-id',
            help=_('Database instance ID.')
        )
        parser.add_argument(
            '--swift-container',
            help=_('The container name for storing the backup data when Swift '
                   'is used as backup storage backend.')
        )

        return parser

    def take_action(self, parsed_args):
        manager = self.app.client_manager.database.backup_strategies
        result = manager.create(
            instance_id=parsed_args.instance_id,
            swift_container=parsed_args.swift_container
        )
        return zip(*sorted(result.to_dict().items()))


class DeleteDatabaseBackupStrategy(command.Command):
    _description = _("Deletes backup strategy.")

    def get_parser(self, prog_name):
        parser = super(DeleteDatabaseBackupStrategy, self).get_parser(
            prog_name)
        parser.add_argument(
            '--project-id',
            help=_('Project ID in Keystone. Only admin user is allowed to '
                   'delete backup strategy for other projects.')
        )
        parser.add_argument(
            '--instance-id',
            help=_('Database instance ID.')
        )
        return parser

    def take_action(self, parsed_args):
        manager = self.app.client_manager.database.backup_strategies
        manager.delete(instance_id=parsed_args.instance_id,
                       project_id=parsed_args.project_id)
