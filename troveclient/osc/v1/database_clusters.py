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
from osc_lib import exceptions
from osc_lib import utils
import six

from troveclient.i18n import _
from troveclient.v1.shell import _parse_extended_properties
from troveclient.v1.shell import _parse_instance_options
from troveclient.v1.shell import EXT_PROPS_HELP
from troveclient.v1.shell import EXT_PROPS_METAVAR
from troveclient.v1.shell import INSTANCE_HELP
from troveclient.v1.shell import INSTANCE_METAVAR


def set_attributes_for_print_detail(cluster):
    info = cluster._info.copy()
    if hasattr(cluster, 'datastore'):
        info['datastore'] = cluster.datastore['type']
        info['datastore_version'] = cluster.datastore['version']
    if hasattr(cluster, 'task'):
        info['task_description'] = cluster.task['description']
        info['task_name'] = cluster.task['name']
    info.pop('task', None)
    if hasattr(cluster, 'ip'):
        info['ip'] = ', '.join(cluster.ip)
    instances = info.pop('instances', None)
    if instances:
        info['instance_count'] = len(instances)
    info.pop('links', None)
    return info


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
                   ' specified marker. When used with ``--limit``, set '
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


class ShowDatabaseCluster(command.ShowOne):
    _description = _("Shows details of a database cluster")

    def get_parser(self, prog_name):
        parser = super(ShowDatabaseCluster, self).get_parser(prog_name)
        parser.add_argument(
            'cluster',
            metavar='<cluster>',
            help=_('ID or name of the cluster'),
        )
        return parser

    def take_action(self, parsed_args):
        database_clusters = self.app.client_manager.database.clusters
        cluster = utils.find_resource(database_clusters, parsed_args.cluster)
        cluster = set_attributes_for_print_detail(cluster)
        return zip(*sorted(six.iteritems(cluster)))


class DeleteDatabaseCluster(command.Command):

    _description = _("Deletes a cluster.")

    def get_parser(self, prog_name):
        parser = super(DeleteDatabaseCluster, self).get_parser(prog_name)
        parser.add_argument(
            'cluster',
            metavar='<cluster>',
            help=_('ID or name of the cluster.'),
        )
        return parser

    def take_action(self, parsed_args):
        database_clusters = self.app.client_manager.database.clusters
        try:
            cluster = utils.find_resource(database_clusters,
                                          parsed_args.cluster)
            database_clusters.delete(cluster)
        except Exception as e:
            msg = (_("Failed to delete cluster %(cluster)s: %(e)s")
                   % {'cluster': parsed_args.cluster, 'e': e})
            raise exceptions.CommandError(msg)


class CreateDatabaseCluster(command.ShowOne):
    _description = _("Creates a new database cluster.")

    def get_parser(self, prog_name):
        parser = super(CreateDatabaseCluster, self).get_parser(prog_name)
        parser.add_argument(
            'name',
            metavar='<name>',
            type=str,
            help=_('Name of the cluster.'),
        )
        parser.add_argument(
            'datastore',
            metavar='<datastore>',
            help=_('A datastore name or ID.'),
        )
        parser.add_argument(
            'datastore_version',
            metavar='<datastore_version>',
            help=_('A datastore version name or ID.'),
        )
        parser.add_argument(
            '--instance',
            metavar=INSTANCE_METAVAR,
            action='append',
            dest='instances',
            default=[],
            help=INSTANCE_HELP,
        )
        parser.add_argument(
            '--locality',
            metavar='<policy>',
            default=None,
            choices=['affinity', 'anti-affinity'],
            help=_('Locality policy to use when creating cluster. '
                   'Choose one of %(choices)s.'),
        )
        parser.add_argument(
            '--extended-properties',
            dest='extended_properties',
            metavar=EXT_PROPS_METAVAR,
            default=None,
            help=EXT_PROPS_HELP,
        )
        parser.add_argument(
            '--configuration',
            metavar='<configuration>',
            type=str,
            default=None,
            help=_('ID of the configuration group to attach to the cluster.'),
        )
        return parser

    def take_action(self, parsed_args):
        database = self.app.client_manager.database
        instances = _parse_instance_options(database, parsed_args.instances)
        extended_properties = {}
        if parsed_args.extended_properties:
            extended_properties = _parse_extended_properties(
                parsed_args.extended_properties)
        cluster = database.clusters.create(
            parsed_args.name,
            parsed_args.datastore,
            parsed_args.datastore_version,
            instances=instances,
            locality=parsed_args.locality,
            extended_properties=extended_properties,
            configuration=parsed_args.configuration)
        cluster = set_attributes_for_print_detail(cluster)
        return zip(*sorted(six.iteritems(cluster)))


class ResetDatabaseClusterStatus(command.Command):

    _description = _("Set the cluster task to NONE.")

    def get_parser(self, prog_name):
        parser = super(ResetDatabaseClusterStatus, self).get_parser(prog_name)
        parser.add_argument(
            'cluster',
            metavar='<cluster>',
            help=_('ID or name of the cluster.'),
        )
        return parser

    def take_action(self, parsed_args):
        database_clusters = self.app.client_manager.database.clusters
        cluster = utils.find_resource(database_clusters,
                                      parsed_args.cluster)
        database_clusters.reset_status(cluster)


class ListDatabaseClusterInstances(command.Lister):

    _description = _("Lists all instances of a cluster.")
    columns = ['ID', 'Name', 'Flavor ID', 'Size', 'Status']

    def get_parser(self, prog_name):
        parser = (super(ListDatabaseClusterInstances, self)
                  .get_parser(prog_name))
        parser.add_argument(
            'cluster',
            metavar='<cluster>',
            help=_('ID or name of the cluster.'))
        return parser

    def take_action(self, parsed_args):
        database_clusters = self.app.client_manager.database.clusters
        cluster = utils.find_resource(database_clusters, parsed_args.cluster)
        instances = cluster._info['instances']
        for instance in instances:
            instance['flavor_id'] = instance['flavor']['id']
            if instance.get('volume'):
                instance['size'] = instance['volume']['size']

        instances = [utils.get_dict_properties(inst, self.columns)
                     for inst in instances]
        return self.columns, instances


class UpgradeDatabaseCluster(command.Command):

    _description = _("Upgrades a cluster to a new datastore version.")

    def get_parser(self, prog_name):
        parser = super(UpgradeDatabaseCluster, self).get_parser(prog_name)
        parser.add_argument(
            'cluster',
            metavar='<cluster>',
            help=_('ID or name of the cluster.'),
        )
        parser.add_argument(
            'datastore_version',
            metavar='<datastore_version>',
            help=_('A datastore version name or ID.'),
        )
        return parser

    def take_action(self, parsed_args):
        database_clusters = self.app.client_manager.database.clusters
        cluster = utils.find_resource(database_clusters,
                                      parsed_args.cluster)
        database_clusters.upgrade(cluster, parsed_args.datastore_version)


class ForceDeleteDatabaseCluster(command.Command):

    _description = _("Force delete a cluster.")

    def get_parser(self, prog_name):
        parser = super(ForceDeleteDatabaseCluster, self).get_parser(prog_name)
        parser.add_argument(
            'cluster',
            metavar='<cluster>',
            help=_('ID or name of the cluster.'),
        )
        return parser

    def take_action(self, parsed_args):
        database_clusters = self.app.client_manager.database.clusters
        cluster = utils.find_resource(database_clusters,
                                      parsed_args.cluster)
        database_clusters.reset_status(cluster)
        try:
            database_clusters.delete(cluster)
        except Exception as e:
            msg = (_("Failed to delete cluster %(cluster)s: %(e)s")
                   % {'cluster': parsed_args.cluster, 'e': e})
            raise exceptions.CommandError(msg)


class GrowDatabaseCluster(command.Command):

    _description = _("Adds more instances to a cluster.")

    def get_parser(self, prog_name):
        parser = super(GrowDatabaseCluster, self).get_parser(prog_name)
        parser.add_argument(
            '--instance',
            metavar=INSTANCE_METAVAR,
            action='append',
            dest='instances',
            default=[],
            help=INSTANCE_HELP
        )
        parser.add_argument(
            'cluster',
            metavar='<cluster>',
            help=_('ID or name of the cluster.')
        )
        return parser

    def take_action(self, parsed_args):
        database_client_manager = self.app.client_manager.database

        db_clusters = database_client_manager.clusters
        cluster = utils.find_resource(db_clusters,
                                      parsed_args.cluster)

        instances = _parse_instance_options(database_client_manager,
                                            parsed_args.instances,
                                            for_grow=True)
        db_clusters.grow(cluster, instances=instances)


class ShrinkDatabaseCluster(command.Command):

    _description = _("Drops instances from a cluster.")

    def get_parser(self, prog_name):
        parser = super(ShrinkDatabaseCluster, self).get_parser(prog_name)
        parser.add_argument(
            'cluster',
            metavar='<cluster>',
            help=_('ID or name of the cluster.')
        )
        parser.add_argument(
            'instances',
            metavar='<instance>',
            nargs='+',
            default=[],
            help=_("Drop instance(s) from the cluster. Specify "
                   "multiple ids to drop multiple instances.")
        )
        return parser

    def take_action(self, parsed_args):
        database_client_manager = self.app.client_manager.database

        db_clusters = database_client_manager.clusters
        cluster = utils.find_resource(db_clusters,
                                      parsed_args.cluster)

        db_instances = database_client_manager.instances
        instances = [
            {'id': utils.find_resource(db_instances,
                                       instance).id}
            for instance in parsed_args.instances
        ]
        db_clusters.shrink(cluster, instances)


class ListDatabaseClusterModules(command.Lister):

    _description = _("Lists all modules for each instance of a cluster.")
    columns = ['instance_name', 'Module Name', 'Module Type', 'md5',
               'created', 'updated']

    def get_parser(self, prog_name):
        parser = (super(ListDatabaseClusterModules, self)
                  .get_parser(prog_name))
        parser.add_argument(
            'cluster',
            metavar='<cluster>',
            help=_('ID or name of the cluster.'))
        return parser

    def take_action(self, parsed_args):
        database_clusters = self.app.client_manager.database.clusters
        database_instances = self.app.client_manager.database.instances
        cluster = utils.find_resource(database_clusters, parsed_args.cluster)
        instances = cluster._info['instances']
        modules = []
        for instance in instances:
            new_list = database_instances.modules(instance['id'])
            for item in new_list:
                item.instance_id = instance['id']
                item.instance_name = instance['name']
                item.module_name = item.name
                item.module_type = item.type
            modules += new_list
        modules = [utils.get_item_properties(module, self.columns)
                   for module in modules]
        return self.columns, modules
