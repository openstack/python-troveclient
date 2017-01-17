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

"""Database v1 Clusters action implementations"""

from osc_lib.command import command
from osc_lib import utils

from troveclient.i18n import _


class ListDatabaseClusters(command.Lister):

    _description = _("List database clusters")
    columns = ['ID', 'Name', 'Datastore', 'Datastore Version',
               'Task Name']

    def get_parser(self, prog_name):
        parser = super(ListDatabaseClusters, self).get_parser(prog_name)
        parser.add_argument(
            '--limit',
            dest='limit',
            metavar='<limit>',
            type=int,
            default=None,
            help=_('Limit the number of results displayed.')
        )
        parser.add_argument(
            '--marker',
            dest='marker',
            metavar='<ID>',
            type=str,
            default=None,
            help=_('Begin displaying the results for IDs greater than the'
                   ' specified marker. When used with :option:`--limit,` set'
                   ' this to the last ID displayed in the previous run.')
        )
        return parser

    def take_action(self, parsed_args):
        database_clusters = self.app.client_manager.database.clusters
        clusters = database_clusters.list(limit=parsed_args.limit,
                                          marker=parsed_args.marker)
        for cluster in clusters:
            setattr(cluster, 'datastore_version',
                    cluster.datastore['version'])
            setattr(cluster, 'datastore', cluster.datastore['type'])
            setattr(cluster, 'task_name', cluster.task['name'])

        clusters = [utils.get_item_properties(c, self.columns)
                    for c in clusters]
        return self.columns, clusters
