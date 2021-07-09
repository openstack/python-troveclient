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

from osc_lib.command import command
from osc_lib import utils as osc_utils
from oslo_utils import uuidutils

from troveclient import exceptions
from troveclient.i18n import _
from troveclient.osc.v1 import base
from troveclient import utils as trove_utils


def get_instances_info(instances):
    instances_info = []

    for instance in instances:
        # To avoid invoking GET request to trove.
        instance_info = instance.to_dict()

        instance_info['flavor_id'] = instance.flavor['id']

        instance_info['size'] = '-'
        if 'volume' in instance_info:
            instance_info['size'] = instance_info['volume']['size']

        instance_info['role'] = ''
        if 'replica_of' in instance_info:
            instance_info['role'] = 'replica'
        if 'replicas' in instance_info:
            instance_info['role'] = 'primary'

        if 'datastore' in instance_info:
            if instance.datastore.get('version'):
                instance_info['datastore_version'] = instance.\
                    datastore['version']
            instance_info['datastore'] = instance.datastore['type']

        if 'access' in instance_info:
            instance_info['public'] = instance_info["access"].get(
                "is_public", False)

        if 'addresses' not in instance_info:
            instance_info['addresses'] = ''

        if 'operating_status' not in instance_info:
            # In case newer version python-troveclient is talking to older
            # version trove.
            instance_info['operating_status'] = ''

        instances_info.append(instance_info)

    return instances_info


def set_attributes_for_print_detail(instance):
    info = instance.to_dict()
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
        info['datastore_version_number'] = instance.datastore.get(
            'version_number')
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
    if hasattr(instance, 'access'):
        info['public'] = instance.access.get("is_public", False)
        info['allowed_cidrs'] = instance.access.get('allowed_cidrs', [])
        info.pop("access", None)

    info.pop('links', None)
    return info


class ListDatabaseInstances(command.Lister):
    _description = _("List database instances")
    columns = ['ID', 'Name', 'Datastore', 'Datastore Version', 'Status',
               'Operating Status', 'Public', 'Addresses', 'Flavor ID',
               'Size', 'Role']
    admin_columns = columns + ["Server ID", "Tenant ID"]

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
        parser.add_argument(
            '--project-id',
            help=_("Include database instances of a specific project "
                   "(admin only)")
        )
        return parser

    def take_action(self, parsed_args):
        extra_params = {}
        if parsed_args.all_projects or parsed_args.project_id:
            db_instances = self.app.client_manager.database.mgmt_instances
            cols = self.admin_columns
            if parsed_args.project_id:
                extra_params['project_id'] = parsed_args.project_id
        else:
            db_instances = self.app.client_manager.database.instances
            cols = self.columns

        instances = db_instances.list(
            limit=parsed_args.limit,
            marker=parsed_args.marker,
            include_clustered=parsed_args.include_clustered,
            **extra_params
        )
        if instances:
            instances_info = get_instances_info(instances)
            instances = [osc_utils.get_dict_properties(info, cols)
                         for info in instances_info]

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
        return zip(*sorted(instance.items()))


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
        parser.add_argument(
            '--force',
            action="store_true",
            default=False,
            help=_('Force delete the instance, will reset the instance status '
                   'before deleting.'),
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances

        # Used for batch deletion
        self.delete_func = (db_instances.force_delete if parsed_args.force
                            else db_instances.delete)
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
            '--flavor',
            metavar='<flavor>',
            type=str,
            help=_("Flavor to create the instance (name or ID). Flavor is not "
                   "required when creating replica instances."),
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
            '--volume-type',
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
            '--availability-zone',
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
            '--datastore-version',
            metavar='<datastore_version>',
            default=None,
            help=_("A datastore version name or ID."),
        )
        parser.add_argument(
            '--datastore-version-number',
            default=None,
            help=_('The version number for the database. The version number '
                   'is needed for the datastore versions with the same name.'),
        )
        parser.add_argument(
            '--nic',
            metavar=('<net-id=<net-uuid>,subnet-id=<subnet-uuid>,'
                     'ip-address=<ip-address>>'),
            dest='nics',
            help=_("Create instance in the given Neutron network. This "
                   "information is used for creating user-facing port for the "
                   "instance. Either network ID or subnet ID (or both) should "
                   "be specified, IP address is optional"),
        )
        parser.add_argument(
            '--configuration',
            metavar='<configuration>',
            default=None,
            help=_("ID of the configuration group to attach to the instance."),
        )
        parser.add_argument(
            '--replica-of',
            metavar='<source_instance>',
            default=None,
            help=_("ID or name of an existing instance to replicate from."),
        )
        parser.add_argument(
            '--replica-count',
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
                 "instance. Repeat for multiple values",
        )
        return parser

    def take_action(self, parsed_args):
        database = self.app.client_manager.database
        db_instances = database.instances

        if not parsed_args.replica_of and not parsed_args.flavor:
            raise exceptions.CommandError(_("Please specify a flavor"))

        if parsed_args.replica_of and parsed_args.flavor:
            print("Warning: Flavor is ignored for creating replica.")

        if not parsed_args.replica_of:
            flavor_id = osc_utils.find_resource(
                database.flavors, parsed_args.flavor).id
        else:
            flavor_id = None

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
            nic_info = {}
            allowed_keys = {
                'net-id': 'network_id',
                'subnet-id': 'subnet_id',
                'ip-address': 'ip_address'
            }
            fields = parsed_args.nics.split(',')
            for field in fields:
                field = field.strip()
                k, v = field.split('=', 1)
                k = k.strip()
                v = v.strip()
                if k not in allowed_keys.keys():
                    raise exceptions.ValidationError(
                        f"{k} is not allowed."
                    )
                if v:
                    nic_info[allowed_keys[k]] = v
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
            flavor_id=flavor_id,
            volume=volume,
            databases=databases,
            users=users,
            restorePoint=restore_point,
            availability_zone=(parsed_args.availability_zone),
            datastore=parsed_args.datastore,
            datastore_version=(parsed_args.datastore_version),
            datastore_version_number=(parsed_args.datastore_version_number),
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
        return zip(*sorted(instance.items()))


class ResetDatabaseInstanceStatus(command.Command):
    _description = _("Set instance service status to ERROR and clear the "
                     "current task status. Mark any running backup operations "
                     "as FAILED.")

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
            'flavor',
            type=str,
            help=_('ID or name of the new flavor.')
        )
        return parser

    def take_action(self, parsed_args):
        instance_mgr = self.app.client_manager.database.instances
        flavor_mgr = self.app.client_manager.database.flavors

        instance_id = parsed_args.instance
        if not uuidutils.is_uuid_like(instance_id):
            instance = osc_utils.find_resource(instance_mgr, instance_id)
            instance_id = instance.id

        flavor = osc_utils.find_resource(flavor_mgr, parsed_args.flavor)

        instance_mgr.resize_instance(instance_id, flavor.id)


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
            help=_('ID or name of the datastore version.'),
        )
        return parser

    def take_action(self, parsed_args):
        db_instances = self.app.client_manager.database.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)
        db_instances.upgrade(instance, parsed_args.datastore_version)


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
        parser = (
            super(ForceDeleteDatabaseInstance, self).get_parser(prog_name))
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
            '--detach-replica-source',
            '--detach_replica_source',
            dest='detach_replica_source',
            action="store_true",
            default=False,
            help=_('Detach the replica instance from its replication source. '
                   '--detach-replica-source may be deprecated in the future '
                   'in favor of just --detach_replica_source'),
        )
        parser.add_argument(
            '--remove-configuration',
            '--remove_configuration',
            dest='remove_configuration',
            action="store_true",
            default=False,
            help=_('Drops the current configuration reference.'),
        )
        public_group = parser.add_mutually_exclusive_group()
        public_group.add_argument(
            '--is-public',
            dest='public',
            default=None,
            action='store_true',
            help="Make the database instance accessible to public.",
        )
        public_group.add_argument(
            '--is-private',
            dest='public',
            default=None,
            action='store_false',
            help="Make the database instance inaccessible to public.",
        )
        parser.add_argument(
            '--allowed-cidr',
            action='append',
            dest='allowed_cidrs',
            help="The IP CIDRs that are allowed to access the database "
                 "instance. Repeat for multiple values",
        )
        return parser

    def take_action(self, parsed_args):
        instance_mgr = self.app.client_manager.database.instances
        instance_id = parsed_args.instance

        if not uuidutils.is_uuid_like(instance_id):
            instance_id = osc_utils.find_resource(instance_mgr, instance_id)

        instance_mgr.update(instance_id, parsed_args.configuration,
                            parsed_args.name,
                            parsed_args.detach_replica_source,
                            parsed_args.remove_configuration,
                            is_public=parsed_args.public,
                            allowed_cidrs=parsed_args.allowed_cidrs)


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
        db_instances.update(instance, detach_replica_source=True)


class RebootDatabaseInstance(command.Command):
    _description = _("Reboots an instance(the Nova server).")

    def get_parser(self, prog_name):
        parser = super(RebootDatabaseInstance, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            type=str,
            help=_('ID or name of the instance.'))

        return parser

    def take_action(self, parsed_args):
        instance_id = parsed_args.instance

        if not uuidutils.is_uuid_like(instance_id):
            instance_mgr = self.app.client_manager.database.instances
            instance_id = osc_utils.find_resource(instance_mgr, instance_id)

        mgmt_instance_mgr = self.app.client_manager.database.mgmt_instances
        mgmt_instance_mgr.reboot(instance_id)


class RebuildDatabaseInstance(command.Command):
    _description = _("Rebuilds an instance(the Nova server).")

    def get_parser(self, prog_name):
        parser = super(RebuildDatabaseInstance, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            type=str,
            help=_('ID or name of the instance.'))
        parser.add_argument(
            'image',
            metavar='<image-id>',
            help=_('ID of the new guest image.'))

        return parser

    def take_action(self, parsed_args):
        instance_id = parsed_args.instance

        if not uuidutils.is_uuid_like(instance_id):
            instance_mgr = self.app.client_manager.database.instances
            instance_id = osc_utils.find_resource(instance_mgr, instance_id)

        mgmt_instance_mgr = self.app.client_manager.database.mgmt_instances
        mgmt_instance_mgr.rebuild(instance_id, parsed_args.image)
