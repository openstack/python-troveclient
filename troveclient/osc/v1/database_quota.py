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

from osc_lib.command import command
from osc_lib import utils as osc_utils
import six

from troveclient.i18n import _


class ShowDatabaseQuota(command.Lister):

    _description = _("Show quotas for a tenant.")
    columns = ['Resource', 'In Use', 'Reserved', 'Limit']

    def get_parser(self, prog_name):
        parser = super(ShowDatabaseQuota, self).get_parser(prog_name)
        parser.add_argument(
            'tenant_id',
            metavar='<tenant_id>',
            help=_('Id of tenant for which to show quotas.'),
        )
        return parser

    def take_action(self, parsed_args):
        db_quota = self.app.client_manager.database.quota
        quota = [osc_utils.get_item_properties(q, self.columns)
                 for q in db_quota.show(parsed_args.tenant_id)]
        return self.columns, quota


class UpdateDatabaseQuota(command.ShowOne):

    _description = _("Update quotas for a tenant.")

    def get_parser(self, prog_name):
        parser = super(UpdateDatabaseQuota, self).get_parser(prog_name)
        parser.add_argument(
            'tenant_id',
            metavar='<tenant_id>',
            help=_('Id of tenant for which to update quotas.'),
        )
        parser.add_argument(
            'resource',
            metavar='<resource>',
            help=_('Id of resource to change.'),
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
        update_params = {
            parsed_args.resource: parsed_args.limit
        }
        updated_quota = db_quota.update(parsed_args.tenant_id,
                                        update_params)
        return zip(*sorted(six.iteritems(updated_quota)))
