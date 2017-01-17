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

"""Database v1 Datastores action implementations"""

from osc_lib.command import command
from osc_lib import utils

from troveclient.i18n import _


class ListDatastores(command.Lister):

    _description = _("List available datastores")
    columns = ['ID', 'Name']

    def take_action(self, parsed_args):
        datastore_client = self.app.client_manager.database.datastores
        datastores = datastore_client.list()
        ds = [utils.get_item_properties(d, self.columns) for d in datastores]
        return self.columns, ds
