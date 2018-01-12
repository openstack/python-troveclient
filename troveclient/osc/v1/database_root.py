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

"""Database v1 Root action implementations"""

from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils as osc_utils
import six

from troveclient.i18n import _


def find_instance_or_cluster(database_client_manager,
                             instance_or_cluster):
    """Returns an instance or cluster, found by ID or name,
    along with the type of resource, instance or cluster.
    Raises CommandError if none is found.
    """
    db_instances = database_client_manager.instances

    try:
        return (osc_utils.find_resource(db_instances,
                                        instance_or_cluster),
                'instance')
    except exceptions.CommandError:
        db_clusters = database_client_manager.clusters
        try:
            return (osc_utils.find_resource(db_clusters,
                                            instance_or_cluster),
                    'cluster')
        except exceptions.CommandError:
            raise exceptions.CommandError(
                _("No instance or cluster with a name or ID of '%s' exists.")
                % instance_or_cluster)


class EnableDatabaseRoot(command.ShowOne):

    _description = _("Enables root for an instance and resets "
                     "if already exists.")

    def get_parser(self, prog_name):
        parser = super(EnableDatabaseRoot, self).get_parser(prog_name)
        parser.add_argument(
            'instance_or_cluster',
            metavar='<instance_or_cluster>',
            help=_('ID or name of the instance or cluster.'),
        )
        parser.add_argument(
            '--root_password',
            metavar='<root_password>',
            default=None,
            help=_('Root password to set.'))

        return parser

    def take_action(self, parsed_args):
        database_client_manager = self.app.client_manager.database
        instance_or_cluster, resource_type = find_instance_or_cluster(
            database_client_manager,
            parsed_args.instance_or_cluster)

        db_root = database_client_manager.root
        if resource_type == 'instance':
            root = db_root.create_instance_root(instance_or_cluster,
                                                parsed_args.root_password)
        else:
            root = db_root.create_cluster_root(instance_or_cluster,
                                               parsed_args.root_password)

        result = {'name': root[0],
                  'password': root[1]}
        return zip(*sorted(six.iteritems(result)))


class DisableDatabaseRoot(command.Command):

    _description = _("Disables root for an instance.")

    def get_parser(self, prog_name):
        parser = super(DisableDatabaseRoot, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            help=_('ID or name of the instance.'),
        )

        return parser

    def take_action(self, parsed_args):
        database_client_manager = self.app.client_manager.database

        db_instances = database_client_manager.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)

        db_root = database_client_manager.root
        db_root.disable_instance_root(instance)


class ShowDatabaseRoot(command.ShowOne):

    _description = _("Gets status if root was ever enabled for "
                     "an instance or cluster.")

    def get_parser(self, prog_name):
        parser = super(ShowDatabaseRoot, self).get_parser(prog_name)
        parser.add_argument(
            'instance_or_cluster',
            metavar='<instance_or_cluster>',
            help=_('ID or name of the instance or cluster.'),
        )

        return parser

    def take_action(self, parsed_args):
        database_client_manager = self.app.client_manager.database
        instance_or_cluster, resource_type = find_instance_or_cluster(
            database_client_manager,
            parsed_args.instance_or_cluster)

        db_root = database_client_manager.root
        if resource_type == 'instance':
            root = db_root.is_instance_root_enabled(instance_or_cluster)
        else:
            root = db_root.is_cluster_root_enabled(instance_or_cluster)

        result = {'is_root_enabled': root.rootEnabled}
        return zip(*sorted(six.iteritems(result)))
