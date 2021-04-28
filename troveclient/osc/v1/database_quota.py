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

"""Database v1 Quota action implementations"""

from osc_lib import utils as osc_utils
from osc_lib.command import command

from troveclient.i18n import _
from troveclient import utils


class ShowDatabaseQuota(command.Lister):
    _description = _("Show quotas for a project.")
    columns = ['Resource', 'In Use', 'Reserved', 'Limit']

    def get_parser(self, prog_name):
        parser = super(ShowDatabaseQuota, self).get_parser(prog_name)
        parser.add_argument(
            'project',
            help=_('Id or name of the project.'),
        )
        return parser

    def take_action(self, parsed_args):
        db_quota = self.app.client_manager.database.quota
        project_id = utils.get_project_id(
            self.app.client_manager.identity,
            parsed_args.project
        )
        quota = [osc_utils.get_item_properties(q, self.columns)
                 for q in db_quota.show(project_id)]
        return self.columns, quota


class UpdateDatabaseQuota(command.ShowOne):
    _description = _("Update quotas for a project.")

    def get_parser(self, prog_name):
        parser = super(UpdateDatabaseQuota, self).get_parser(prog_name)
        parser.add_argument(
            'project',
            help=_('Id or name of the project.'),
        )
        parser.add_argument(
            'resource',
            metavar='<resource>',
            help=_('Resource name.'),
        )
        parser.add_argument(
            'limit',
            metavar='<limit>',
            type=int,
            help=_('New limit to set for the named resource.'),
        )
        return parser

    def take_action(self, parsed_args):
        db_quota = self.app.client_manager.database.quota
        project_id = utils.get_project_id(
            self.app.client_manager.identity,
            parsed_args.project
        )
        update_params = {
            parsed_args.resource: parsed_args.limit
        }
        updated_quota = db_quota.update(project_id, update_params)
        return zip(*sorted(updated_quota.items()))
