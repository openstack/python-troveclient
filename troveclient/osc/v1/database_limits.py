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

"""Database v1 Limits action implementations"""

from osc_lib.command import command
from osc_lib import utils as osc_utils

from troveclient.i18n import _
from troveclient import utils


class ListDatabaseLimits(command.Lister):

    _description = _("List database limits")
    columns = ['Value', 'Verb', 'Remaining', 'Unit']

    def take_action(self, parsed_args):
        database_limits = self.app.client_manager.database.limits
        limits = database_limits.list()
        # Pop the first one, its absolute limits
        utils.print_dict(limits.pop(0)._info)
        limits = [osc_utils.get_item_properties(i, self.columns)
                  for i in limits]
        return self.columns, limits
