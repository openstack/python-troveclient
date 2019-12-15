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

"""Database v1 Logs action implementations"""

from osc_lib.command import command
from osc_lib import utils as osc_utils
import six

from troveclient.i18n import _


class ListDatabaseLogs(command.Lister):

    _description = _("Lists the log files available for instance.")
    columns = ['Name', 'Type', 'Status', 'Published', 'Pending',
               'Container', 'Prefix']

    def get_parser(self, prog_name):
        parser = super(ListDatabaseLogs, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            help=_('ID or name of the instance.')
        )
        return parser

    def take_action(self, parsed_args):
        database_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(database_instances,
                                           parsed_args.instance)
        log_list = database_instances.log_list(instance)
        logs = [osc_utils.get_item_properties(l, self.columns)
                for l in log_list]
        return self.columns, logs


class SetDatabaseInstanceLog(command.ShowOne):
    _description = _("Instructs Trove guest to operate logs.")

    def get_parser(self, prog_name):
        parser = super(SetDatabaseInstanceLog, self).get_parser(prog_name)

        parser.add_argument(
            'instance',
            metavar='<instance>',
            type=str,
            help=_('Id or Name of the instance.')
        )
        parser.add_argument(
            'log_name',
            metavar='<log_name>',
            type=str,
            help=_('Name of log to operate.')
        )
        parser.add_argument(
            '--enable',
            action='store_true',
            help="Whether or not to enable log collection.",
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help="Whether or not to disable log collection.",
        )
        parser.add_argument(
            '--publish',
            action='store_true',
            help="Whether or not to publish log files to the backend storage "
                 "for logs(Swift by default).",
        )
        parser.add_argument(
            '--discard',
            action='store_true',
            help="Whether or not to discard the existing logs before publish.",
        )

        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)

        log_info = db_instances.log_action(
            instance, parsed_args.log_name,
            enable=parsed_args.enable,
            disable=parsed_args.disable,
            discard=parsed_args.discard,
            publish=parsed_args.publish
        )
        result = log_info._info

        return zip(*sorted(six.iteritems(result)))


class ShowDatabaseInstanceLog(command.ShowOne):
    _description = _("Show information of given log name for the database "
                     "instance.")

    def get_parser(self, prog_name):
        parser = super(ShowDatabaseInstanceLog, self).get_parser(prog_name)

        parser.add_argument(
            'instance',
            metavar='<instance>',
            type=str,
            help=_('Id or Name of the instance.')
        )
        parser.add_argument(
            'log_name',
            metavar='<log_name>',
            type=str,
            help=_('Name of log to operate.')
        )

        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)

        log_info = db_instances.log_show(instance, parsed_args.log_name)
        result = log_info._info

        return zip(*sorted(six.iteritems(result)))
