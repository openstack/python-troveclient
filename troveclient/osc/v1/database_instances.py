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

import argparse
import six

from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils as osc_utils
from oslo_utils import uuidutils

from troveclient.i18n import _
from troveclient.osc.v1 import base
from troveclient import utils as trove_utils


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


def set_attributes_for_print_detail(instance):
    info = instance._info.copy()
    info['flavor'] = instance.flavor['id']
    if hasattr(instance, 'volume'):
        info['volume'] = instance.volume['size']
        if 'used' in instance.volume:
            info['volume_used'] = instance.volume['used']
    if hasattr(instance, 'ip'):
        info['ip'] = ', '.join(instance.ip)
    if hasattr(instance, 'datastore'):
        info['datastore'] = instance.datastore['type']
        info['datastore_version'] = instance.datastore['version']
    if hasattr(instance, 'configuration'):
        info['configuration'] = instance.configuration['id']
    if hasattr(instance, 'replica_of'):
        info['replica_of'] = instance.replica_of['id']
    if hasattr(instance, 'replicas'):
        replicas = [replica['id'] for replica in instance.replicas]
        info['replicas'] = ', '.join(replicas)
    if hasattr(instance, 'networks'):
        info['networks'] = instance.networks['name']
        info['networks_id'] = instance.networks['id']
    if hasattr(instance, 'fault'):
        info.pop('fault', None)
        info['fault'] = instance.fault['message']
        info['fault_date'] = instance.fault['created']
        if 'details' in instance.fault and instance.fault['details']:
            info['fault_details'] = instance.fault['details']
    info.pop('links', None)
    return info


class ListDatabaseInstances(command.Lister):
    _description = _("List database instances")
    columns = ['ID', 'Name', 'Datastore', 'Datastore Version', 'Status',
               'Flavor ID', 'Size', 'Region']
    admin_columns = [
        'ID', 'Name', 'Tenant ID', 'Datastore', 'Datastore Version', 'Status',
        'Flavor ID', 'Size'
    ]

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
                   'specified marker. When used with ``--limit``, set '
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
        parser.add_argument(
            '--all-projects',
            dest='all_projects',
            action="store_true",
            default=False,
            help=_("Include database instances of all projects (admin only)")
        )
        return parser

    def take_action(self, parsed_args):
        if parsed_args.all_projects:
            db_instances = self.app.client_manager.database.mgmt_instances
            cols = self.admin_columns
        else:
            db_instances = self.app.client_manager.database.instances
            cols = self.columns

        instances = db_instances.list(
            limit=parsed_args.limit,
            marker=parsed_args.marker,
            include_clustered=parsed_args.include_clustered
        )
        if instances:
            instances = set_attributes_for_print(instances)
            instances = [osc_utils.get_item_properties(i, cols)
                         for i in instances]

        return cols, instances


class ShowDatabaseInstance(command.ShowOne):
    _description = _("Show instance details")

    def get_parser(self, prog_name):
        parser = super(ShowDatabaseInstance, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            help=_('Instance (name or ID)'),
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(db_instances, parsed_args.instance)
        instance = set_attributes_for_print_detail(instance)
        return zip(*sorted(six.iteritems(instance)))


class DeleteDatabaseInstance(base.TroveDeleter):
    _description = _("Deletes an instance.")

    def get_parser(self, prog_name):
        parser = super(DeleteDatabaseInstance, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            nargs='+',
            metavar='instance',
            help='Id or name of instance(s).'
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances

        # Used for batch deletion
        self.delete_func = db_instances.delete
        self.resource = 'database instance'

        ids = []
        for instance_id in parsed_args.instance:
            if not uuidutils.is_uuid_like(instance_id):
                try:
                    instance_id = trove_utils.get_resource_id_by_name(
                        db_instances, instance_id
                    )
                except Exception as e:
                    msg = ("Failed to get database instance %s, error: %s" %
                           (instance_id, str(e)))
                    raise exceptions.CommandError(msg)

            ids.append(instance_id)

        self.delete_resources(ids)


class CreateDatabaseInstance(command.ShowOne):

    _description = _("Creates a new database instance.")

    def get_parser(self, prog_name):
        parser = super(CreateDatabaseInstance, self).get_parser(prog_name)
        parser.add_argument(
            'name',
            metavar='<name>',
            help=_("Name of the instance."),
        )
        parser.add_argument(
            'flavor',
            metavar='<flavor>',
            type=str,
            help=_("A flavor name or ID."),
        )
        parser.add_argument(
            '--size',
            metavar='<size>',
            type=int,
            default=None,
            help=_("Size of the instance disk volume in GB. "
                   "Required when volume support is enabled."),
        )
        parser.add_argument(
            '--volume_type',
            metavar='<volume_type>',
            type=str,
            default=None,
            help=_("Volume type. Optional when volume support is enabled."),
        )
        parser.add_argument(
            '--databases',
            metavar='<database>',
            nargs="+",
            default=[],
            help=_("Optional list of databases."),
        )
        parser.add_argument(
            '--users',
            metavar='<user:password>',
            nargs="+",
            default=[],
            help=_("Optional list of users."),
        )
        parser.add_argument(
            '--backup',
            metavar='<backup>',
            default=None,
            help=_("A backup name or ID."),
        )
        parser.add_argument(
            '--availability_zone',
            metavar='<availability_zone>',
            default=None,
            help=_("The Zone hint to give to Nova."),
        )
        parser.add_argument(
            '--datastore',
            metavar='<datastore>',
            default=None,
            help=_("A datastore name or ID."),
        )
        parser.add_argument(
            '--datastore_version',
            metavar='<datastore_version>',
            default=None,
            help=_("A datastore version name or ID."),
        )
        parser.add_argument(
            '--nic',
            metavar='<net-id=<net-uuid>>',
            dest='nics',
            help=_("Create instance in the given Neutron network."),
        )
        parser.add_argument(
            '--configuration',
            metavar='<configuration>',
            default=None,
            help=_("ID of the configuration group to attach to the instance."),
        )
        parser.add_argument(
            '--replica_of',
            metavar='<source_instance>',
            default=None,
            help=_("ID or name of an existing instance to replicate from."),
        )
        parser.add_argument(
            '--replica_count',
            metavar='<count>',
            type=int,
            default=None,
            help=_("Number of replicas to create (defaults to 1 if "
                   "replica_of specified)."),
        )
        parser.add_argument(
            '--module',
            metavar='<module>',
            type=str,
            dest='modules',
            action='append',
            default=[],
            help=_("ID or name of the module to apply.  Specify multiple "
                   "times to apply multiple modules."),
        )
        parser.add_argument(
            '--locality',
            metavar='<policy>',
            default=None,
            choices=['affinity', 'anti-affinity'],
            help=_("Locality policy to use when creating replicas. Choose "
                   "one of %(choices)s."),
        )
        parser.add_argument(
            '--region',
            metavar='<region>',
            type=str,
            default=None,
            help=argparse.SUPPRESS,
        )
        parser.add_argument(
            '--is-public',
            action='store_true',
            help="Whether or not to make the instance public.",
        )
        parser.add_argument(
            '--allowed-cidr',
            action='append',
            dest='allowed_cidrs',
            help="The IP CIDRs that are allowed to access the database "
                 "instance.",
        )
        return parser

    def take_action(self, parsed_args):
        database = self.app.client_manager.database
        db_instances = database.instances
        flavor_id = osc_utils.find_resource(database.flavors,
                                            parsed_args.flavor).id
        volume = None
        if parsed_args.size is not None and parsed_args.size <= 0:
            raise exceptions.ValidationError(
                _("Volume size '%s' must be an integer and greater than 0.")
                % parsed_args.size)
        elif parsed_args.size:
            volume = {"size": parsed_args.size,
                      "type": parsed_args.volume_type}
        restore_point = None
        if parsed_args.backup:
            restore_point = {"backupRef": osc_utils.find_resource(
                database.backups, parsed_args.backup).id}
        replica_of = None
        replica_count = parsed_args.replica_count
        if parsed_args.replica_of:
            replica_of = osc_utils.find_resource(
                db_instances, parsed_args.replica_of)
            replica_count = replica_count or 1
        locality = None
        if parsed_args.locality:
            locality = parsed_args.locality
            if replica_of:
                raise exceptions.ValidationError(
                    _('Cannot specify locality when adding replicas '
                      'to existing master.'))
        databases = [{'name': value} for value in parsed_args.databases]
        users = [{'name': n, 'password': p, 'databases': databases} for (n, p)
                 in
                 [z.split(':')[:2] for z in parsed_args.users]]

        nics = []
        if parsed_args.nics:
            nic_info = dict(
                [(k, v) for (k, v) in [parsed_args.nics.split("=", 1)[:2]]]
            )
            if not nic_info.get('net-id'):
                raise exceptions.ValidationError(
                    "net-id is not set in %s" % parsed_args.nics
                )
            nics.append(nic_info)

        modules = []
        for module in parsed_args.modules:
            modules.append(osc_utils.find_resource(database.modules,
                                                   module).id)

        access = {'is_public': False}
        if parsed_args.is_public:
            access['is_public'] = True
        if parsed_args.allowed_cidrs:
            access['allowed_cidrs'] = parsed_args.allowed_cidrs

        instance = db_instances.create(
            parsed_args.name,
            flavor_id,
            volume=volume,
            databases=databases,
            users=users,
            restorePoint=restore_point,
            availability_zone=(parsed_args.availability_zone),
            datastore=parsed_args.datastore,
            datastore_version=(parsed_args.datastore_version),
            nics=nics,
            configuration=parsed_args.configuration,
            replica_of=replica_of,
            replica_count=replica_count,
            modules=modules,
            locality=locality,
            region_name=parsed_args.region,
            access=access
        )
        instance = set_attributes_for_print_detail(instance)
        return zip(*sorted(six.iteritems(instance)))


class ResetDatabaseInstanceStatus(command.Command):

    _description = _("Set the task status of an instance to NONE if the "
                     "instance is in BUILD or ERROR state. Resetting task "
                     "status of an instance in BUILD state will allow "
                     "the instance to be deleted.")

    def get_parser(self, prog_name):
        parser = super(ResetDatabaseInstanceStatus, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            help=_('ID or name of the instance'),
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)
        db_instances.reset_status(instance)


class ResizeDatabaseInstanceFlavor(command.Command):

    _description = _("Resize an instance with a new flavor")

    def get_parser(self, prog_name):
        parser = super(ResizeDatabaseInstanceFlavor, self).get_parser(
            prog_name
        )
        parser.add_argument(
            'instance',
            metavar='<instance>',
            type=str,
            help=_('ID or name of the instance')
        )
        parser.add_argument(
            'flavor_id',
            metavar='<flavor_id>',
            type=str,
            help=_('New flavor of the instance')
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        db_flavor = self.app.client_manager.database.flavors
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)
        flavor = osc_utils.find_resource(db_flavor,
                                         parsed_args.flavor_id)
        db_instances.resize_instance(instance, flavor)


class UpgradeDatabaseInstance(command.Command):

    _description = _("Upgrades an instance to a new datastore version.")

    def get_parser(self, prog_name):
        parser = super(UpgradeDatabaseInstance, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            type=str,
            help=_('ID or name of the instance.'),
        )
        parser.add_argument(
            'datastore_version',
            metavar='<datastore_version>',
            help=_('ID or name of the instance.'),
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)
        db_instances.upgrade(instance, parsed_args.datastore_version)


class EnableDatabaseInstanceLog(command.ShowOne):

    _description = _("Instructs Trove guest to start collecting log details.")

    def get_parser(self, prog_name):
        parser = super(EnableDatabaseInstanceLog, self).get_parser(prog_name)
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
            help=_('Name of log to publish.')
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)
        log_info = db_instances.log_enable(instance, parsed_args.log_name)
        result = log_info._info
        return zip(*sorted(six.iteritems(result)))


class ResizeDatabaseInstanceVolume(command.Command):

    _description = _("Resizes the volume size of an instance.")

    def get_parser(self, prog_name):
        parser = super(ResizeDatabaseInstanceVolume, self).get_parser(
            prog_name
        )
        parser.add_argument(
            'instance',
            metavar='<instance>',
            type=str,
            help=_('ID or name of the instance.')
        )
        parser.add_argument(
            'size',
            metavar='<size>',
            type=int,
            default=None,
            help=_('New size of the instance disk volume in GB.')
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)
        db_instances.resize_volume(instance, parsed_args.size)


class ForceDeleteDatabaseInstance(command.Command):

    _description = _("Force delete an instance.")

    def get_parser(self, prog_name):
        parser = (super(ForceDeleteDatabaseInstance, self)
                  .get_parser(prog_name))
        parser.add_argument(
            'instance',
            metavar='<instance>',
            help=_('ID or name of the instance'),
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)
        db_instances.reset_status(instance)
        try:
            db_instances.delete(instance)
        except Exception as e:
            msg = (_("Failed to delete instance %(instance)s: %(e)s")
                   % {'instance': parsed_args.instance, 'e': e})
            raise exceptions.CommandError(msg)


class PromoteDatabaseInstanceToReplicaSource(command.Command):

    _description = _(
        "Promotes a replica to be the new replica source of its set.")

    def get_parser(self, prog_name):
        parser = super(PromoteDatabaseInstanceToReplicaSource,
                       self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            type=str,
            help=_('ID or name of the instance.'),
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)
        db_instances.promote_to_replica_source(instance)


class RestartDatabaseInstance(command.Command):

    _description = _("Restarts an instance.")

    def get_parser(self, prog_name):
        parser = super(RestartDatabaseInstance, self).get_parser(
            prog_name
        )
        parser.add_argument(
            'instance',
            metavar='<instance>',
            type=str,
            help=_('ID or name of the instance.')
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)
        db_instances.restart(instance)


class EjectDatabaseInstanceReplicaSource(command.Command):

    _description = _("Ejects a replica source from its set.")

    def get_parser(self, prog_name):
        parser = super(EjectDatabaseInstanceReplicaSource, self).get_parser(
            prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            type=str,
            help=_('ID or name of the instance.'),
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)
        db_instances.eject_replica_source(instance)


class UpdateDatabaseInstance(command.Command):

    _description = _("Updates an instance: Edits name, "
                     "configuration, or replica source.")

    def get_parser(self, prog_name):
        parser = super(UpdateDatabaseInstance, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            type=str,
            help=_('ID or name of the instance.'),
        )
        parser.add_argument(
            '--name',
            metavar='<name>',
            type=str,
            default=None,
            help=_('ID or name of the instance.'),
        )
        parser.add_argument(
            '--configuration',
            metavar='<configuration>',
            type=str,
            default=None,
            help=_('ID of the configuration reference to attach.'),
        )
        parser.add_argument(
            '--detach_replica_source',
            '--detach-replica-source',
            dest='detach_replica_source',
            action="store_true",
            default=False,
            help=_('Detach the replica instance from its replication source. '
                   '--detach-replica-source may be deprecated in the future '
                   'in favor of just --detach_replica_source'),
        )
        parser.add_argument(
            '--remove_configuration',
            dest='remove_configuration',
            action="store_true",
            default=False,
            help=_('Drops the current configuration reference.'),
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)
        db_instances.edit(instance, parsed_args.configuration,
                          parsed_args.name,
                          parsed_args.detach_replica_source,
                          parsed_args.remove_configuration)


class DetachDatabaseInstanceReplica(command.Command):

    _description = _("Detaches a replica instance "
                     "from its replication source.")

    def get_parser(self, prog_name):
        parser = super(DetachDatabaseInstanceReplica, self).get_parser(
            prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            type=str,
            help=_('ID or name of the instance.'),
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)
        db_instances.edit(instance, detach_replica_source=True)
