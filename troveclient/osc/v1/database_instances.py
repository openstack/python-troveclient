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

"""Database v1 Instances action implementations"""

from osc_lib.command import command
from osc_lib import utils as osc_utils

from troveclient.i18n import _


def set_attributes_for_print(instances):
    for instance in instances:
        setattr(instance, 'flavor_id', instance.flavor['id'])
        if hasattr(instance, 'volume'):
            setattr(instance, 'size', instance.volume['size'])
        else:
            setattr(instance, 'size', '-')
        if hasattr(instance, 'datastore'):
            if instance.datastore.get('version'):
                setattr(instance, 'datastore_version',
                        instance.datastore['version'])
            setattr(instance, 'datastore', instance.datastore['type'])
        return instances


class ListDatabaseInstances(command.Lister):

    _description = _("List database instances")
    columns = ['ID', 'Name', 'Datastore', 'Datastore Version', 'Status',
               'Flavor ID', 'Size', 'Region']

    def get_parser(self, prog_name):
        parser = super(ListDatabaseInstances, self).get_parser(prog_name)
        parser.add_argument(
            '--limit',
            dest='limit',
            metavar='<limit>',
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
                   'specified marker. When used with :option:`--limit,` set'
                   'this to the last ID displayed in the previous run.')
        )
        parser.add_argument(
            '--include_clustered', '--include-clustered',
            dest='include_clustered',
            action="store_true",
            default=False,
            help=_("Include instances that are part of a cluster "
                   "(default %(default)s).  --include-clustered may be "
                   "deprecated in the future, retaining just "
                   "--include_clustered.")
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instances = db_instances.list(limit=parsed_args.limit,
                                      marker=parsed_args.marker,
                                      include_clustered=(parsed_args.
                                                         include_clustered))
        if instances:
            instances = set_attributes_for_print(instances)
            instances = [osc_utils.get_item_properties(i, self.columns)
                         for i in instances]
        return self.columns, instances
