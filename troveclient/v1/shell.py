# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# All Rights Reserved.
#
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

from __future__ import print_function

import argparse
import sys
import time

from troveclient.i18n import _

try:
    import simplejson as json
except ImportError:
    import json

from troveclient import exceptions
from troveclient import utils
from troveclient.v1 import modules

INSTANCE_ARG_NAME = _('instance')
INSTANCE_METAVAR = _('"opt=<value>[,opt=<value> ...] "')
INSTANCE_ERROR = _("Instance argument(s) must be of the form --instance "
                   "%s - see help for details.") % INSTANCE_METAVAR
INSTANCE_HELP = _("Add an instance to the cluster.  Specify multiple "
                  "times to create multiple instances.  "
                  "Valid options are: flavor=<flavor_name_or_id>, "
                  "volume=<disk_size_in_GB>, volume_type=<type>, "
                  "nic='<net-id=<net-uuid>, v4-fixed-ip=<ip-addr>, "
                  "port-id=<port-uuid>>' "
                  "(where net-id=network_id, v4-fixed-ip=IPv4r_fixed_address, "
                  "port-id=port_id), availability_zone=<AZ_hint_for_Nova>, "
                  "module=<module_name_or_id>, type=<type_of_cluster_node>, "
                  "related_to=<related_attribute>.")
NIC_ERROR = _("Invalid NIC argument: %s. Must specify either net-id or port-id"
              " but not both. Please refer to help.")
NO_LOG_FOUND_ERROR = _("ERROR: No published '%(log_name)s' log was found for "
                       "%(instance)s.")
LOCALITY_DOMAIN = ['affinity', 'anti-affinity']
EXT_PROPS_METAVAR = INSTANCE_METAVAR
EXT_PROPS_HELP = _("Add extended properties for cluster create. "
                   "Currently only support MongoDB options, other databases "
                   "will be added in the future. "
                   "MongoDB: "
                   "  num_configsvr=<number_of_configsvr>, "
                   "  num_mongos=<number_of_mongos>, "
                   "  configsvr_volume_size=<disk_size_in_GB>, "
                   "  configsvr_volume_type=<volume_type>, "
                   "  mongos_volume_size=<disk_size_in_GB>, "
                   "  mongos_volume_type=<volume_type>.")


def _poll_for_status(poll_fn, obj_id, action, final_ok_states,
                     poll_period=5, show_progress=True):
    """Block while an action is being performed, periodically printing
    progress.
    """
    def print_progress(progress):
        if show_progress:
            msg = (_('\rInstance %(action)s... %(progress)s%% complete')
                   % dict(action=action, progress=progress))
        else:
            msg = _('\rInstance %(action)s...') % dict(action=action)

        sys.stdout.write(msg)
        sys.stdout.flush()

    print()
    while True:
        obj = poll_fn(obj_id)
        status = obj.status.lower()
        progress = getattr(obj, 'progress', None) or 0
        if status in final_ok_states:
            print_progress(100)
            print(_("\nFinished"))
            break
        elif status == "error":
            print(_("\nError %(action)s instance") % {'action': action})
            break
        else:
            print_progress(progress)
            time.sleep(poll_period)


def _print_instance(instance):
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
    utils.print_dict(info)


def _print_cluster(cluster, include_all=False):

    info = cluster._info.copy()
    info['datastore'] = cluster.datastore['type']
    info['datastore_version'] = cluster.datastore['version']
    info['task_name'] = cluster.task['name']
    info['task_description'] = cluster.task['description']
    info.pop('task', None)
    if include_all and hasattr(cluster, 'ip'):
        info['ip'] = ', '.join(cluster.ip)
    instances = info.pop('instances', None)
    if instances:
        info['instance_count'] = len(instances)
    info.pop('links', None)
    utils.print_dict(info)


def _print_object(obj):
    # Get rid of those ugly links
    if obj._info.get('links'):
        del(obj._info['links'])

    # Fallback to str_id for flavors, where necessary
    if hasattr(obj, 'str_id'):
        obj._info['id'] = obj.id
        del(obj._info['str_id'])

    # Get datastore type and version, where necessary
    if hasattr(obj, 'datastore'):
        if 'type' in obj.datastore:
            obj._info['datastore'] = obj.datastore['type']
            obj._info['datastore_version'] = obj.datastore['version']

    utils.print_dict(obj._info)


def _find_instance_or_cluster(cs, instance_or_cluster):
    """Returns an instance or cluster, found by id, along with the type of
    resource, instance or cluster, that was found.
    Raises CommandError if none is found.
    """
    try:
        return _find_instance(cs, instance_or_cluster), 'instance'
    except exceptions.CommandError:
        try:
            return _find_cluster(cs, instance_or_cluster), 'cluster'
        except Exception:
            raise exceptions.CommandError(
                _("No instance or cluster with a name or ID of '%s' exists.")
                % instance_or_cluster)


def _find_instance(cs, instance):
    """Get an instance by ID."""
    return utils.find_resource(cs.instances, instance)


def _find_cluster(cs, cluster):
    """Get a cluster by ID."""
    return utils.find_resource(cs.clusters, cluster)


def _find_flavor(cs, flavor):
    """Get a flavor by ID."""
    return utils.find_resource(cs.flavors, flavor)


def _find_volume_type(cs, volume_type):
    """Get a volume type by ID."""
    return utils.find_resource(cs.volume_types, volume_type)


def _find_backup(cs, backup):
    """Get a backup by ID."""
    return utils.find_resource(cs.backups, backup)


def _find_module(cs, module):
    """Get a module by ID."""
    return utils.find_resource(cs.modules, module)


def _find_datastore(cs, datastore):
    """Get a datastore by ID."""
    return utils.find_resource(cs.datastores, datastore)


def _find_datastore_version(cs, datastore_version):
    """Get a datastore version by ID."""
    return utils.find_resource(cs.datastores, datastore_version)


def _find_configuration(cs, configuration):
    """Get a configuration by ID."""
    return utils.find_resource(cs.configurations, configuration)


# Flavor related calls
@utils.arg('--datastore_type', metavar='<datastore_type>',
           default=None,
           help=_('Type of the datastore. For eg: mysql.'))
@utils.arg("--datastore_version_id", metavar="<datastore_version_id>",
           default=None, help=_("ID of the datastore version."))
@utils.service_type('database')
def do_flavor_list(cs, args):
    """Lists available flavors."""
    if args.datastore_type and args.datastore_version_id:
        flavors = cs.flavors.list_datastore_version_associated_flavors(
            args.datastore_type, args.datastore_version_id)
    elif not args.datastore_type and not args.datastore_version_id:
        flavors = cs.flavors.list()
    else:
        raise exceptions.MissingArgs(['datastore_type',
                                      'datastore_version_id'])

    # Fallback to str_id where necessary.
    _flavors = []
    for f in flavors:
        if not f.id and hasattr(f, 'str_id'):
            f.id = f.str_id
        _flavors.append(f)

    utils.print_list(_flavors, ['id', 'name', 'ram', 'vcpus', 'disk',
                                'ephemeral'],
                     labels={'ram': 'RAM', 'vcpus': 'vCPUs', 'disk': 'Disk'},
                     order_by='ram')


@utils.arg('flavor', metavar='<flavor>', type=str,
           help=_('ID or name of the flavor.'))
@utils.service_type('database')
def do_flavor_show(cs, args):
    """Shows details of a flavor."""
    flavor = _find_flavor(cs, args.flavor)
    _print_object(flavor)


# Volume type related calls
@utils.arg('--datastore_type', metavar='<datastore_type>',
           default=None,
           help='Type of the datastore. For eg: mysql.')
@utils.arg("--datastore_version_id", metavar="<datastore_version_id>",
           default=None, help="ID of the datastore version.")
@utils.service_type('database')
def do_volume_type_list(cs, args):
    """Lists available volume types."""
    if args.datastore_type and args.datastore_version_id:
        volume_types = cs.volume_types.\
            list_datastore_version_associated_volume_types(
                args.datastore_type, args.datastore_version_id
            )
    elif not args.datastore_type and not args.datastore_version_id:
        volume_types = cs.volume_types.list()
    else:
        raise exceptions.MissingArgs(['datastore_type',
                                      'datastore_version_id'])

    utils.print_list(volume_types, ['id', 'name', 'is_public', 'description'])


@utils.arg('volume_type', metavar='<volume_type>',
           help='ID or name of the volume type.')
@utils.service_type('database')
def do_volume_type_show(cs, args):
    """Shows details of a volume type."""
    volume_type = _find_volume_type(cs, args.volume_type)
    _print_object(volume_type)


# Instance related calls

@utils.arg('--limit', metavar='<limit>', type=int, default=None,
           help=_('Limit the number of results displayed.'))
@utils.arg('--marker', metavar='<ID>', type=str, default=None,
           help=_('Begin displaying the results for IDs greater than the '
                  'specified marker. When used with --limit, set this to '
                  'the last ID displayed in the previous run.'))
@utils.arg('--include_clustered', '--include-clustered',
           dest='include_clustered',
           action="store_true", default=False,
           help=_("Include instances that are part of a cluster "
                  "(default %(default)s).  --include-clustered may be "
                  "deprecated in the future, retaining just "
                  "--include_clustered."))
@utils.service_type('database')
def do_list(cs, args):
    """Lists all the instances."""
    instances = cs.instances.list(limit=args.limit, marker=args.marker,
                                  include_clustered=args.include_clustered)
    _print_instances(instances)


def _print_instances(instances, is_admin=False):
    for instance in instances:
        setattr(instance, 'flavor_id', instance.flavor['id'])
        if hasattr(instance, 'volume'):
            setattr(instance, 'size', instance.volume['size'])
        else:
            setattr(instance, 'size', '-')
        if not hasattr(instance, 'region'):
            setattr(instance, 'region', '')
        if hasattr(instance, 'datastore'):
            if instance.datastore.get('version'):
                setattr(instance, 'datastore_version',
                        instance.datastore['version'])
            setattr(instance, 'datastore', instance.datastore['type'])
    fields = ['id', 'name', 'datastore',
              'datastore_version', 'status',
              'flavor_id', 'size', 'region']
    if is_admin:
        fields.append('tenant_id')
    utils.print_list(instances, fields)


@utils.arg('--limit', metavar='<limit>', type=int, default=None,
           help=_('Limit the number of results displayed.'))
@utils.arg('--marker', metavar='<ID>', type=str, default=None,
           help=_('Begin displaying the results for IDs greater than the '
                  'specified marker. When used with --limit, set this to '
                  'the last ID displayed in the previous run.'))
@utils.service_type('database')
def do_cluster_list(cs, args):
    """Lists all the clusters."""
    clusters = cs.clusters.list(limit=args.limit, marker=args.marker)

    for cluster in clusters:
        setattr(cluster, 'datastore_version',
                cluster.datastore['version'])
        setattr(cluster, 'datastore', cluster.datastore['type'])
        setattr(cluster, 'task_name', cluster.task['name'])
    utils.print_list(clusters, ['id', 'name', 'datastore',
                                'datastore_version', 'task_name'])


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.service_type('database')
def do_show(cs, args):
    """Shows details of an instance."""
    instance = _find_instance(cs, args.instance)
    _print_instance(instance)


@utils.arg('cluster', metavar='<cluster>',
           help=_('ID or name of the cluster.'))
@utils.service_type('database')
def do_cluster_show(cs, args):
    """Shows details of a cluster."""
    cluster = _find_cluster(cs, args.cluster)
    _print_cluster(cluster, include_all=True)


@utils.arg('cluster', metavar='<cluster>',
           help=_('ID or name of the cluster.'))
@utils.service_type('database')
def do_cluster_instances(cs, args):
    """Lists all instances of a cluster."""
    cluster = _find_cluster(cs, args.cluster)
    instances = cluster._info['instances']
    for instance in instances:
        instance['flavor_id'] = instance['flavor']['id']
        if instance.get('volume'):
            instance['size'] = instance['volume']['size']
    utils.print_list(
        instances, ['id', 'name', 'flavor_id', 'size', 'status'],
        obj_is_dict=True)


@utils.arg('--' + INSTANCE_ARG_NAME, metavar=INSTANCE_METAVAR,
           action='append', dest='instances', default=[],
           help=INSTANCE_HELP)
@utils.arg('cluster', metavar='<cluster>',
           help=_('ID or name of the cluster.'))
@utils.service_type('database')
def do_cluster_grow(cs, args):
    """Adds more instances to a cluster."""
    cluster = _find_cluster(cs, args.cluster)
    instances = _parse_instance_options(cs, args.instances, for_grow=True)
    cs.clusters.grow(cluster, instances=instances)


@utils.arg('cluster', metavar='<cluster>',
           help=_('ID or name of the cluster.'))
@utils.arg('instances', metavar='<instance>', nargs='+', default=[],
           help=_("Drop instance(s) from the cluster. Specify "
                  "multiple ids to drop multiple instances."))
@utils.service_type('database')
def do_cluster_shrink(cs, args):
    """Drops instances from a cluster."""
    cluster = _find_cluster(cs, args.cluster)
    instances = [{'id': _find_instance(cs, instance).id}
                 for instance in args.instances]
    cs.clusters.shrink(cluster, instances=instances)


@utils.arg('instance', metavar='<instance>', nargs='+',
           help=_('ID or name of the instance(s).'))
@utils.service_type('database')
def do_delete(cs, args):
    """Delete specified instance(s)."""
    utils.do_action_on_many(
        lambda s: cs.instances.delete(_find_instance(cs, s)),
        args.instance,
        _("Request to delete instance %s has been accepted."),
        _("Unable to delete the specified instance(s)."))


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.service_type('database')
def do_force_delete(cs, args):
    """Force delete an instance."""
    instance = _find_instance(cs, args.instance)
    msg = _("Request to force delete instance %s "
            "has been accepted.") % instance.id
    cs.instances.reset_status(instance)
    utils.do_action_with_msg(cs.instances.delete(instance), msg)


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.service_type('database')
def do_reset_status(cs, args):
    """Set the task status of an instance to NONE if the instance is in BUILD
    or ERROR state. Resetting task status of an instance in BUILD state will
    allow the instance to be deleted.
    """
    instance = _find_instance(cs, args.instance)
    cs.instances.reset_status(instance=instance)


@utils.arg('cluster', metavar='<cluster>', nargs='+',
           help=_('ID or name of the cluster(s).'))
@utils.service_type('database')
def do_cluster_delete(cs, args):
    """Delete specified cluster(s)."""
    utils.do_action_on_many(
        lambda s: cs.clusters.delete(_find_cluster(cs, s)),
        args.cluster,
        _("Request to delete cluster %s has been accepted."),
        _("Unable to delete the specified cluster(s)."))


@utils.arg('cluster', metavar='<cluster>',
           help=_('ID or name of the cluster.'))
@utils.service_type('database')
def do_cluster_force_delete(cs, args):
    """Force delete a cluster"""
    cluster = _find_cluster(cs, args.cluster)
    msg = _("Request to force delete cluster %s "
            "has been accepted.") % cluster.id
    cs.clusters.reset_status(cluster)
    utils.do_action_with_msg(cs.clusters.delete(cluster), msg)


@utils.arg('cluster', metavar='<cluster>',
           help=_('ID or name of the cluster.'))
@utils.service_type('database')
def do_cluster_reset_status(cs, args):
    """Set the cluster task to NONE."""
    cluster = _find_cluster(cs, args.cluster)
    cs.clusters.reset_status(cluster)


@utils.arg('cluster', metavar='<cluster>',
           help=_('ID or name of the cluster.'))
@utils.arg('datastore_version',
           metavar='<datastore_version>',
           help=_('A datastore version name or ID.'))
@utils.service_type('database')
def do_cluster_upgrade(cs, args):
    """Upgrades a cluster to a new datastore version."""
    cluster = _find_cluster(cs, args.cluster)
    cs.clusters.upgrade(cluster, args.datastore_version)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help=_('ID or name of the instance.'))
@utils.arg('--name',
           metavar='<name>',
           type=str,
           default=None,
           help=_('Name of the instance.'))
@utils.arg('--configuration',
           metavar='<configuration>',
           type=str,
           default=None,
           help=_('ID of the configuration reference to attach.'))
@utils.arg('--detach_replica_source', '--detach-replica-source',
           dest='detach_replica_source',
           action="store_true",
           default=False,
           help=_('Detach the replica instance from its replication source. '
                  '--detach-replica-source may be deprecated in the future '
                  'in favor of just --detach_replica_source'))
@utils.arg('--remove_configuration',
           dest='remove_configuration',
           action="store_true",
           default=False,
           help=_('Drops the current configuration reference.'))
@utils.service_type('database')
def do_update(cs, args):
    """Updates an instance: Edits name, configuration, or replica source."""
    instance = _find_instance(cs, args.instance)
    cs.instances.edit(instance, args.configuration, args.name,
                      args.detach_replica_source, args.remove_configuration)


@utils.arg('name',
           metavar='<name>',
           type=str,
           help=_('Name of the instance.'))
@utils.arg('--size',
           metavar='<size>',
           type=int,
           default=None,
           help=_("Size of the instance disk volume in GB. "
                  "Required when volume support is enabled."))
@utils.arg('--volume_type',
           metavar='<volume_type>',
           type=str,
           default=None,
           help=_("Volume type. Optional when volume support is enabled."))
@utils.arg('flavor',
           metavar='<flavor>',
           type=str,
           help=_('A flavor name or ID.'))
@utils.arg('--databases', metavar='<database>',
           help=_('Optional list of databases.'),
           nargs="+", default=[])
@utils.arg('--users', metavar='<user:password>',
           help=_('Optional list of users.'),
           nargs="+", default=[])
@utils.arg('--backup',
           metavar='<backup>',
           default=None,
           help=_('A backup name or ID.'))
@utils.arg('--availability_zone',
           metavar='<availability_zone>',
           default=None,
           help=_('The Zone hint to give to Nova.'))
@utils.arg('--datastore',
           metavar='<datastore>',
           default=None,
           help=_('A datastore name or ID.'))
@utils.arg('--datastore_version',
           metavar='<datastore_version>',
           default=None,
           help=_('A datastore version name or ID.'))
@utils.arg('--nic',
           metavar="<net-id=<net-uuid>,v4-fixed-ip=<ip-addr>,"
                   "port-id=<port-uuid>>",
           action='append',
           dest='nics',
           default=[],
           help=_("Create a NIC on the instance. "
                  "Specify option multiple times to create multiple NICs. "
                  "net-id: attach NIC to network with this ID "
                  "(either port-id or net-id must be specified), "
                  "v4-fixed-ip: IPv4 fixed address for NIC (optional), "
                  "port-id: attach NIC to port with this ID "
                  "(either port-id or net-id must be specified)."))
@utils.arg('--configuration',
           metavar='<configuration>',
           default=None,
           help=_('ID of the configuration group to attach to the instance.'))
@utils.arg('--replica_of',
           metavar='<source_instance>',
           default=None,
           help=_('ID or name of an existing instance to replicate from.'))
@utils.arg('--replica_count',
           metavar='<count>',
           type=int,
           default=None,
           help=_('Number of replicas to create (defaults to 1 if replica_of '
                  'specified).'))
@utils.arg('--module', metavar='<module>',
           type=str, dest='modules', action='append', default=[],
           help=_('ID or name of the module to apply.  Specify multiple '
                  'times to apply multiple modules.'))
@utils.arg('--locality',
           metavar='<policy>',
           default=None,
           choices=LOCALITY_DOMAIN,
           help=_('Locality policy to use when creating replicas. Choose '
                  'one of %(choices)s.'))
@utils.arg('--region', metavar='<region>',
           type=str,
           default=None,
           help=argparse.SUPPRESS)
#           help=_('Name of region in which to create the instance.'))
@utils.service_type('database')
def do_create(cs, args):
    """Creates a new instance."""
    flavor_id = _find_flavor(cs, args.flavor).id
    volume = None
    if args.size is not None and args.size <= 0:
        raise exceptions.ValidationError(
            _("Volume size '%s' must be an integer and greater than 0.")
            % args.size)
    elif args.size:
        volume = {"size": args.size,
                  "type": args.volume_type}
    restore_point = None
    if args.backup:
        restore_point = {"backupRef": _find_backup(cs, args.backup).id}
    replica_of = None
    replica_count = args.replica_count
    if args.replica_of:
        replica_of = _find_instance(cs, args.replica_of)
        replica_count = replica_count or 1
    locality = None
    if args.locality:
        locality = args.locality
        if replica_of:
            raise exceptions.ValidationError(
                _('Cannot specify locality when adding replicas to existing '
                  'master.'))
    databases = [{'name': value} for value in args.databases]
    users = [{'name': n, 'password': p, 'databases': databases} for (n, p) in
             [z.split(':')[:2] for z in args.users]]
    nics = []
    for nic_str in args.nics:
        nic_info = dict([(k, v) for (k, v) in [z.split("=", 1)[:2] for z in
                                               nic_str.split(",")]])
        _validate_nic_info(nic_info, nic_str)
        nics.append(nic_info)
    modules = []
    for module in args.modules:
        modules.append(_find_module(cs, module).id)

    instance = cs.instances.create(args.name,
                                   flavor_id,
                                   volume=volume,
                                   databases=databases,
                                   users=users,
                                   restorePoint=restore_point,
                                   availability_zone=args.availability_zone,
                                   datastore=args.datastore,
                                   datastore_version=args.datastore_version,
                                   nics=nics,
                                   configuration=args.configuration,
                                   replica_of=replica_of,
                                   replica_count=replica_count,
                                   modules=modules,
                                   locality=locality,
                                   region_name=args.region)
    _print_instance(instance)


def _validate_nic_info(nic_info, nic_str):
    # need one or the other, not both, not none (!= ~ XOR)
    if not (bool(nic_info.get('net-id')) != bool(nic_info.get('port-id'))):
        raise exceptions.ValidationError(NIC_ERROR % (_("nic='%s'") % nic_str))


def _get_flavor(cs, opts_str):
    flavor_name, opts_str = _strip_option(opts_str, 'flavor', True)
    flavor_id = _find_flavor(cs, flavor_name).id
    return str(flavor_id), opts_str


def _get_networks(opts_str):
    nic_args_list, opts_str = _strip_option(opts_str, 'nic', is_required=False,
                                            quotes_required=True,
                                            allow_multiple=True)
    nic_info_list = []
    for nic_args in nic_args_list:
        orig_nic_args = nic_args = _unquote(nic_args)
        nic_info = {}
        net_id, nic_args = _strip_option(nic_args, 'net-id', False)
        port_id, nic_args = _strip_option(nic_args, 'port-id', False)
        fixed_ipv4, nic_args = _strip_option(nic_args, 'v4-fixed-ip', False)
        if nic_args:
            raise exceptions.ValidationError(
                _("Unknown args '%s' in 'nic' option") % nic_args)
        if net_id:
            nic_info.update({'net-id': net_id})
        if port_id:
            nic_info.update({'port-id': port_id})
        if fixed_ipv4:
            nic_info.update({'v4-fixed-ip': fixed_ipv4})

        _validate_nic_info(nic_info, orig_nic_args)
        nic_info_list.append(nic_info)

    return nic_info_list, opts_str


def _unquote(value):
    def _strip_quotes(value, quote_char):
        if value:
            return value.strip(quote_char)
        return value

    return _strip_quotes(_strip_quotes(value, "'"), '"')


def _get_volume(opts_str):
    volume_size, opts_str = _strip_option(opts_str, 'volume', is_required=True)
    volume_type, opts_str = _strip_option(opts_str, 'volume_type',
                                          is_required=False)

    volume_info = {"size": volume_size}
    if volume_type:
        volume_info.update({"type": volume_type})

    return volume_info, opts_str


def _get_availability_zone(opts_str):
    return _strip_option(opts_str, 'availability_zone', is_required=False)


def _get_region(cs, opts_str):
    return _strip_option(opts_str, 'region', is_required=False)


def _get_modules(cs, opts_str):
    modules, opts_str = _strip_option(
        opts_str, 'module', is_required=False, allow_multiple=True)
    module_list = []
    for module in modules:
        module_info = {'id': _find_module(cs, module).id}
        module_list.append(module_info)
    return module_list, opts_str


def _strip_option(opts_str, opt_name, is_required=True,
                  quotes_required=False, allow_multiple=False):
    opt_value = [] if allow_multiple else None
    opts_str = opts_str.strip().strip(",")
    if opt_name in opts_str:
        try:
            split_str = '%s=' % opt_name
            parts = opts_str.split(split_str)
            before = parts[0]
            after = parts[1]
            if len(parts) > 2:
                if allow_multiple:
                    after = split_str.join(parts[1:])
                    value, after = _strip_option(
                        after, opt_name, is_required=is_required,
                        quotes_required=quotes_required,
                        allow_multiple=allow_multiple)
                    opt_value.extend(value)
                else:
                    raise exceptions.ValidationError((
                        _("Option '%s' found more than once in argument "
                          "--instance ") % opt_name) + INSTANCE_METAVAR)

            # Handle complex (quoted) properties. Strip the quotes.
            quote = after[0]
            if quote in ["'", '"']:
                after = after[1:]
            else:
                if quotes_required:
                    raise exceptions.ValidationError(
                        _("Invalid '%s' option. The value must be quoted. "
                          "(Or perhaps you're missing quotes around the "
                          "entire argument string)")
                        % opt_name)
                quote = ''

            split_str = '%s,' % quote
            parts = after.split(split_str)
            value = str(parts[0]).strip()
            if allow_multiple:
                opt_value.append(value)
                opt_value = list(set(opt_value))
            else:
                opt_value = value
            opts_str = before + split_str.join(parts[1:])
        except IndexError:
            raise exceptions.ValidationError(
                _("Invalid '%(name)s' parameter. %(error)s.")
                % {'name': opt_name,
                   'error': INSTANCE_ERROR})

    if is_required and not opt_value:
        raise exceptions.MissingArgs([opt_name],
                                     message=(_("Missing option '%s' for "
                                                "argument --instance ") +
                                              INSTANCE_METAVAR))

    return opt_value, opts_str.strip().strip(",")


def _parse_instance_options(cs, instance_options, for_grow=False):
    instances = []
    for instance_opts in instance_options:
        instance_info = {}

        flavor, instance_opts = _get_flavor(cs, instance_opts)
        instance_info["flavorRef"] = flavor
        volume, instance_opts = _get_volume(instance_opts)
        instance_info["volume"] = volume

        nics, instance_opts = _get_networks(instance_opts)
        if nics:
            instance_info["nics"] = nics

        availability_zone, instance_opts = _get_availability_zone(
            instance_opts)
        if availability_zone:
            instance_info["availability_zone"] = availability_zone

        modules, instance_opts = _get_modules(cs, instance_opts)
        if modules:
            instance_info["modules"] = modules

        instance_type, instance_opts = _strip_option(
            instance_opts, 'type', is_required=False, allow_multiple=True)
        if instance_type:
            instance_info["type"] = instance_type

        if for_grow:
            related_to, instance_opts = _strip_option(
                instance_opts, 'related_to', is_required=False)
            if instance_type:
                instance_info["related_to"] = related_to

            name, instance_opts = _strip_option(
                instance_opts, 'name', is_required=False)
            if name:
                instance_info["name"] = name

        region, instance_opts = _get_region(cs, instance_opts)
        if region:
            instance_info["region"] = region

        if instance_opts:
            raise exceptions.ValidationError(
                _("Unknown option(s) '%s' specified for instance")
                % instance_opts)

        instances.append(instance_info)
    if len(instances) == 0:
        raise exceptions.MissingArgs([INSTANCE_ARG_NAME])
    return instances


def _parse_extended_properties(extended_properties):
    return dict([(k, v) for (k, v) in [kv.strip().split("=")
                for kv in extended_properties.split(",")]])


@utils.arg('name',
           metavar='<name>',
           type=str,
           help=_('Name of the cluster.'))
@utils.arg('datastore',
           metavar='<datastore>',
           help=_('A datastore name or ID.'))
@utils.arg('datastore_version',
           metavar='<datastore_version>',
           help=_('A datastore version name or ID.'))
@utils.arg('--' + INSTANCE_ARG_NAME, metavar=INSTANCE_METAVAR,
           action='append', dest='instances', default=[],
           help=INSTANCE_HELP)
@utils.arg('--locality',
           metavar='<policy>',
           default=None,
           choices=LOCALITY_DOMAIN,
           help=_('Locality policy to use when creating cluster. Choose '
                  'one of %(choices)s.'))
@utils.arg('--extended_properties',
           metavar=EXT_PROPS_METAVAR,
           default=None,
           help=EXT_PROPS_HELP)
@utils.arg('--configuration',
           metavar='<configuration>',
           type=str,
           default=None,
           help=_('ID of the configuration group to attach to the cluster.'))
@utils.service_type('database')
def do_cluster_create(cs, args):
    """Creates a new cluster."""
    instances = _parse_instance_options(cs, args.instances)
    extended_properties = {}
    if args.extended_properties:
        extended_properties = _parse_extended_properties(
            args.extended_properties)
    cluster = cs.clusters.create(args.name,
                                 args.datastore,
                                 args.datastore_version,
                                 instances=instances,
                                 locality=args.locality,
                                 extended_properties=extended_properties,
                                 configuration=args.configuration)
    _print_cluster(cluster)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help=_('ID or name of the instance.'))
@utils.arg('flavor',
           metavar='<flavor>',
           type=str,
           help=_('New flavor of the instance.'))
@utils.service_type('database')
def do_resize_instance(cs, args):
    """Resizes an instance with a new flavor."""
    instance = _find_instance(cs, args.instance)
    flavor_id = _find_flavor(cs, args.flavor).id
    cs.instances.resize_instance(instance, flavor_id)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help=_('ID or name of the instance.'))
@utils.arg('datastore_version',
           metavar='<datastore_version>',
           help=_('A datastore version name or ID.'))
@utils.service_type('database')
def do_upgrade(cs, args):
    """Upgrades an instance to a new datastore version."""
    instance = _find_instance(cs, args.instance)
    cs.instances.upgrade(instance, args.datastore_version)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help=_('ID or name of the instance.'))
@utils.arg('size',
           metavar='<size>',
           type=int,
           default=None,
           help=_('New size of the instance disk volume in GB.'))
@utils.service_type('database')
def do_resize_volume(cs, args):
    """Resizes the volume size of an instance."""
    instance = _find_instance(cs, args.instance)
    cs.instances.resize_volume(instance, args.size)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help=_('ID or name of the instance.'))
@utils.service_type('database')
def do_restart(cs, args):
    """Restarts an instance."""
    instance = _find_instance(cs, args.instance)
    cs.instances.restart(instance)

# Replication related commands


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help=_('ID or name of the instance.'))
def do_detach_replica(cs, args):
    """Detaches a replica instance from its replication source."""
    instance = _find_instance(cs, args.instance)
    cs.instances.edit(instance, detach_replica_source=True)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help=_('ID or name of the instance.'))
def do_promote_to_replica_source(cs, args):
    """Promotes a replica to be the new replica source of its set."""
    instance = _find_instance(cs, args.instance)
    cs.instances.promote_to_replica_source(instance)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help=_('ID or name of the instance.'))
def do_eject_replica_source(cs, args):
    """Ejects a replica source from its set."""
    instance = _find_instance(cs, args.instance)
    cs.instances.eject_replica_source(instance)

# Backup related commands


@utils.arg('backup', metavar='<backup>', help=_('ID or name of the backup.'))
@utils.service_type('database')
def do_backup_show(cs, args):
    """Shows details of a backup."""
    backup = _find_backup(cs, args.backup)
    _print_object(backup)


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.arg('--limit', metavar='<limit>',
           default=None,
           help=_('Return up to N number of the most recent backups.'))
@utils.arg('--marker', metavar='<ID>', type=str, default=None,
           help=_('Begin displaying the results for IDs greater than the '
                  'specified marker. When used with --limit, set this to '
                  'the last ID displayed in the previous run.'))
@utils.service_type('database')
def do_backup_list_instance(cs, args):
    """Lists available backups for an instance."""
    instance = _find_instance(cs, args.instance)
    items = cs.instances.backups(instance, limit=args.limit,
                                 marker=args.marker)
    backups = items
    while items.next and not args.limit:
        items = cs.instances.backups(instance, marker=items.next)
        backups += items
    utils.print_list(backups, ['id', 'name', 'status',
                               'parent_id', 'updated'],
                     order_by='updated')


@utils.arg('--limit', metavar='<limit>',
           default=None,
           help=_('Return up to N number of the most recent backups.'))
@utils.arg('--marker', metavar='<ID>', type=str, default=None,
           help=_('Begin displaying the results for IDs greater than the '
                  'specified marker. When used with --limit, set this to '
                  'the last ID displayed in the previous run.'))
@utils.arg('--datastore', metavar='<datastore>',
           default=None,
           help=_('ID or name of the datastore (to filter backups by).'))
@utils.service_type('database')
def do_backup_list(cs, args):
    """Lists available backups."""
    items = cs.backups.list(limit=args.limit, datastore=args.datastore,
                            marker=args.marker)
    backups = items
    while items.next and not args.limit:
        items = cs.backups.list(marker=items.next)
        backups += items
    utils.print_list(backups, ['id', 'instance_id', 'name',
                               'status', 'parent_id', 'updated'],
                     order_by='updated')


@utils.arg('backup', metavar='<backup>', help=_('ID or name of the backup.'))
@utils.service_type('database')
def do_backup_delete(cs, args):
    """Deletes a backup."""
    backup = _find_backup(cs, args.backup)
    cs.backups.delete(backup)


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.arg('name', metavar='<name>', help=_('Name of the backup.'))
@utils.arg('--description', metavar='<description>',
           default=None,
           help=_('An optional description for the backup.'))
@utils.arg('--parent', metavar='<parent>', default=None,
           help=_('Optional ID of the parent backup to perform an'
                  ' incremental backup from.'))
@utils.arg('--incremental', action='store_true', default=False,
           help=_('Create an incremental backup based on the last'
                  ' full or incremental backup. It will create a'
                  ' full backup if no existing backup found.'))
@utils.service_type('database')
def do_backup_create(cs, args):
    """Creates a backup of an instance."""
    instance = _find_instance(cs, args.instance)
    backup = cs.backups.create(args.name, instance,
                               description=args.description,
                               parent_id=args.parent,
                               incremental=args.incremental)
    _print_object(backup)


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.arg('pattern', metavar='<pattern>',
           help=_('Cron style pattern describing schedule occurrence.'))
@utils.arg('name', metavar='<name>', help=_('Name of the backup.'))
@utils.arg('--description', metavar='<description>',
           default=None,
           help=_('An optional description for the backup.'))
@utils.arg('--incremental', action="store_true", default=False,
           help=_('Flag to select incremental backup based on most recent'
                  ' backup.'))
@utils.service_type('database')
def do_schedule_create(cs, args):
    """Schedules backups for an instance."""
    instance = _find_instance(cs, args.instance)
    backup = cs.backups.schedule_create(instance, args.pattern, args.name,
                                        description=args.description,
                                        incremental=args.incremental)
    _print_object(backup)


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.service_type('database')
def do_schedule_list(cs, args):
    """Lists scheduled backups for an instance."""
    instance = _find_instance(cs, args.instance)
    schedules = cs.backups.schedule_list(instance)
    utils.print_list(schedules, ['id', 'name', 'pattern',
                                 'next_execution_time'],
                     order_by='next_execution_time')


@utils.arg('id', metavar='<schedule id>', help=_('Id of the schedule.'))
@utils.service_type('database')
def do_schedule_show(cs, args):
    """Shows details of a schedule."""
    _print_object(cs.backups.schedule_show(args.id))


@utils.arg('id', metavar='<schedule id>', help=_('Id of the schedule.'))
@utils.service_type('database')
def do_schedule_delete(cs, args):
    """Deletes a schedule."""
    cs.backups.schedule_delete(args.id)


@utils.arg('id', metavar='<schedule id>', help=_('Id of the schedule.'))
@utils.arg('--limit', metavar='<limit>',
           default=None, type=int,
           help=_('Return up to N number of the most recent executions.'))
@utils.arg('--marker', metavar='<ID>', type=str, default=None,
           help=_('Begin displaying the results for IDs greater than the '
                  'specified marker. When used with --limit, set this to '
                  'the last ID displayed in the previous run.'))
@utils.service_type('database')
def do_execution_list(cs, args):
    """Lists executions of a scheduled backup of an instance."""
    executions = cs.backups.execution_list(args.id, marker=args.marker,
                                           limit=args.limit)

    utils.print_list(executions, ['id', 'created_at', 'state', 'output'],
                     labels={'created_at': 'Execution Time'},
                     order_by='created_at')


@utils.arg('execution', metavar='<execution>',
           help=_('Id of the execution to delete.'))
@utils.service_type('database')
def do_execution_delete(cs, args):
    """Deletes an execution."""
    cs.backups.execution_delete(args.execution)


# Database related actions

@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.arg('name', metavar='<name>', help=_('Name of the database.'))
@utils.arg('--character_set', metavar='<character_set>',
           default=None,
           help=_('Optional character set for database.'))
@utils.arg('--collate', metavar='<collate>', default=None,
           help=_('Optional collation type for database.'))
@utils.service_type('database')
def do_database_create(cs, args):
    """Creates a database on an instance."""
    instance, _ = _find_instance_or_cluster(cs, args.instance)
    database_dict = {'name': args.name}
    if args.collate:
        database_dict['collate'] = args.collate
    if args.character_set:
        database_dict['character_set'] = args.character_set
    cs.databases.create(instance,
                        [database_dict])


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.service_type('database')
def do_database_list(cs, args):
    """Lists available databases on an instance."""
    instance, _ = _find_instance_or_cluster(cs, args.instance)
    items = cs.databases.list(instance)
    databases = items
    while (items.next):
        items = cs.databases.list(instance, marker=items.next)
        databases += items

    utils.print_list(databases, ['name'])


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.arg('database', metavar='<database>', help=_('Name of the database.'))
@utils.service_type('database')
def do_database_delete(cs, args):
    """Deletes a database from an instance."""
    instance, _ = _find_instance_or_cluster(cs, args.instance)
    cs.databases.delete(instance, args.database)


# User related actions

@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.arg('name', metavar='<name>', help=_('Name of user.'))
@utils.arg('password', metavar='<password>', help=_('Password of user.'))
@utils.arg('--host', metavar='<host>', default=None,
           help=_('Optional host of user.'))
@utils.arg('--databases', metavar='<databases>',
           help=_('Optional list of databases.'),
           nargs="+", default=[])
@utils.service_type('database')
def do_user_create(cs, args):
    """Creates a user on an instance."""
    instance, _ = _find_instance_or_cluster(cs, args.instance)
    databases = [{'name': value} for value in args.databases]
    user = {'name': args.name, 'password': args.password,
            'databases': databases}
    if args.host:
        user['host'] = args.host
    cs.users.create(instance, [user])


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.service_type('database')
def do_user_list(cs, args):
    """Lists the users for an instance."""
    instance, _ = _find_instance_or_cluster(cs, args.instance)
    items = cs.users.list(instance)
    users = items
    while (items.next):
        items = cs.users.list(instance, marker=items.next)
        users += items
    for user in users:
        db_names = [db['name'] for db in user.databases]
        user.databases = ', '.join(db_names)
    utils.print_list(users, ['name', 'host', 'databases'])


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.arg('name', metavar='<name>', help=_('Name of user.'))
@utils.arg('--host', metavar='<host>', default=None,
           help=_('Optional host of user.'))
@utils.service_type('database')
def do_user_delete(cs, args):
    """Deletes a user from an instance."""
    instance, _ = _find_instance_or_cluster(cs, args.instance)
    cs.users.delete(instance, args.name, hostname=args.host)


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.arg('name', metavar='<name>', help=_('Name of user.'))
@utils.arg('--host', metavar='<host>', default=None,
           help=_('Optional host of user.'))
@utils.service_type('database')
def do_user_show(cs, args):
    """Shows details of a user of an instance."""
    instance, _ = _find_instance_or_cluster(cs, args.instance)
    user = cs.users.get(instance, args.name, hostname=args.host)
    _print_object(user)


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.arg('name', metavar='<name>', help=_('Name of user.'))
@utils.arg('--host', metavar='<host>', default=None,
           help=_('Optional host of user.'))
@utils.service_type('database')
def do_user_show_access(cs, args):
    """Shows access details of a user of an instance."""
    instance, _ = _find_instance_or_cluster(cs, args.instance)
    access = cs.users.list_access(instance, args.name, hostname=args.host)
    utils.print_list(access, ['name'])


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.arg('name', metavar='<name>', help=_('Name of user.'))
@utils.arg('--host', metavar='<host>', default=None,
           help=_('Optional host of user.'))
@utils.arg('--new_name', metavar='<new_name>', default=None,
           help=_('Optional new name of user.'))
@utils.arg('--new_password', metavar='<new_password>', default=None,
           help=_('Optional new password of user.'))
@utils.arg('--new_host', metavar='<new_host>', default=None,
           help=_('Optional new host of user.'))
@utils.service_type('database')
def do_user_update_attributes(cs, args):
    """Updates a user's attributes on an instance.
    At least one optional argument must be provided.
    """
    instance, _ = _find_instance_or_cluster(cs, args.instance)
    new_attrs = {}
    if args.new_name:
        new_attrs['name'] = args.new_name
    if args.new_password:
        new_attrs['password'] = args.new_password
    if args.new_host:
        new_attrs['host'] = args.new_host
    cs.users.update_attributes(instance, args.name,
                               newuserattr=new_attrs, hostname=args.host)


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.arg('name', metavar='<name>', help=_('Name of user.'))
@utils.arg('--host', metavar='<host>', default=None,
           help=_('Optional host of user.'))
@utils.arg('databases', metavar='<databases>',
           help=_('List of databases.'),
           nargs="+", default=[])
@utils.service_type('database')
def do_user_grant_access(cs, args):
    """Grants access to a database(s) for a user."""
    instance, _ = _find_instance_or_cluster(cs, args.instance)
    cs.users.grant(instance, args.name,
                   args.databases, hostname=args.host)


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.arg('name', metavar='<name>', help=_('Name of user.'))
@utils.arg('database', metavar='<database>', help=_('A single database.'))
@utils.arg('--host', metavar='<host>', default=None,
           help=_('Optional host of user.'))
@utils.service_type('database')
def do_user_revoke_access(cs, args):
    """Revokes access to a database for a user."""
    instance, _ = _find_instance_or_cluster(cs, args.instance)
    cs.users.revoke(instance, args.name,
                    args.database, hostname=args.host)


# Limits related commands

@utils.service_type('database')
def do_limit_list(cs, args):
    """Lists the limits for a tenant."""
    limits = cs.limits.list()
    # Pop the first one, its absolute limits
    absolute = limits.pop(0)
    _print_object(absolute)
    utils.print_list(limits, ['value', 'verb', 'remaining', 'unit'])


# Root related commands

@utils.arg('instance_or_cluster', metavar='<instance_or_cluster>',
           help=_('ID or name of the instance or cluster.'))
@utils.arg('--root_password',
           metavar='<root_password>',
           default=None,
           help=_('Root password to set.'))
@utils.service_type('database')
def do_root_enable(cs, args):
    """Enables root for an instance and resets if already exists."""
    instance_or_cluster, resource_type = _find_instance_or_cluster(
        cs, args.instance_or_cluster)
    if resource_type == 'instance':
        root = cs.root.create_instance_root(instance_or_cluster,
                                            args.root_password)
    else:
        root = cs.root.create_cluster_root(instance_or_cluster,
                                           args.root_password)
    utils.print_dict({'name': root[0], 'password': root[1]})


@utils.arg('instance', metavar='<instance>',
           help=_('ID or name of the instance.'))
@utils.service_type('database')
def do_root_disable(cs, args):
    """Disables root for an instance."""
    instance = _find_instance(cs, args.instance)
    cs.root.disable_instance_root(instance)


@utils.arg('instance_or_cluster', metavar='<instance_or_cluster>',
           help=_('ID or name of the instance or cluster.'))
@utils.service_type('database')
def do_root_show(cs, args):
    """Gets status if root was ever enabled for an instance or cluster."""
    instance_or_cluster, resource_type = _find_instance_or_cluster(
        cs, args.instance_or_cluster)
    if resource_type == 'instance':
        root = cs.root.is_instance_root_enabled(instance_or_cluster)
    else:
        root = cs.root.is_cluster_root_enabled(instance_or_cluster)
    utils.print_dict({'is_root_enabled': root.rootEnabled})


# security group related functions

@utils.service_type('database')
def do_secgroup_list(cs, args):
    """Lists all security groups."""
    items = cs.security_groups.list()
    sec_grps = items
    while (items.next):
        items = cs.security_groups.list()
        sec_grps += items

    utils.print_list(sec_grps, ['id', 'name', 'instance_id'])


@utils.arg('security_group', metavar='<security_group>',
           help=_('Security group ID.'))
@utils.service_type('database')
def do_secgroup_show(cs, args):
    """Shows details of a security group."""
    sec_grp = cs.security_groups.get(args.security_group)
    del sec_grp._info['rules']
    _print_object(sec_grp)


@utils.arg('security_group', metavar='<security_group>',
           help=_('Security group ID.'))
@utils.arg('cidr', metavar='<cidr>', help=_('CIDR address.'))
@utils.service_type('database')
def do_secgroup_add_rule(cs, args):
    """Creates a security group rule."""
    rules = cs.security_group_rules.create(
        args.security_group, args.cidr)

    utils.print_list(rules, [
        'id', 'security_group_id', 'protocol',
        'from_port', 'to_port', 'cidr', 'created'], obj_is_dict=True)


@utils.arg('security_group', metavar='<security_group>',
           help=_('Security group ID.'))
@utils.service_type('database')
def do_secgroup_list_rules(cs, args):
    """Lists all rules for a security group."""
    sec_grp = cs.security_groups.get(args.security_group)
    rules = sec_grp._info['rules']
    utils.print_list(
        rules, ['id', 'protocol', 'from_port', 'to_port', 'cidr'],
        obj_is_dict=True)


@utils.arg('security_group_rule', metavar='<security_group_rule>',
           help=_('ID of security group rule.'))
@utils.service_type('database')
def do_secgroup_delete_rule(cs, args):
    """Deletes a security group rule."""
    cs.security_group_rules.delete(args.security_group_rule)


@utils.service_type('database')
def do_datastore_list(cs, args):
    """Lists available datastores."""
    datastores = cs.datastores.list()
    utils.print_list(datastores, ['id', 'name'])


@utils.arg('datastore', metavar='<datastore>',
           help=_('ID of the datastore.'))
@utils.service_type('database')
def do_datastore_show(cs, args):
    """Shows details of a datastore."""
    datastore = cs.datastores.get(args.datastore)

    info = datastore._info.copy()
    versions = info.get('versions', [])
    versions_str = "\n".join(
        [ver['name'] + " (" + ver['id'] + ")" for ver in versions])
    info['versions (id)'] = versions_str
    info.pop('versions', None)
    info.pop('links', None)
    if hasattr(datastore, 'default_version'):
        def_ver_id = getattr(datastore, 'default_version')
        info['default_version'] = [
            ver['name'] for ver in versions if ver['id'] == def_ver_id][0]
    utils.print_dict(info)


@utils.arg('datastore', metavar='<datastore>',
           help=_('ID or name of the datastore.'))
@utils.service_type('database')
def do_datastore_version_list(cs, args):
    """Lists available versions for a datastore."""
    datastore_versions = cs.datastore_versions.list(args.datastore)
    utils.print_list(datastore_versions, ['id', 'name'])


@utils.arg('--datastore', metavar='<datastore>',
           default=None,
           help=_('ID or name of the datastore. Optional if the ID of the'
                  ' datastore_version is provided.'))
@utils.arg('datastore_version', metavar='<datastore_version>',
           help=_('ID or name of the datastore version.'))
@utils.service_type('database')
def do_datastore_version_show(cs, args):
    """Shows details of a datastore version."""
    if args.datastore:
        datastore_version = cs.datastore_versions.get(args.datastore,
                                                      args.datastore_version)
    elif utils.is_uuid_like(args.datastore_version):
        datastore_version = cs.datastore_versions.get_by_uuid(
            args.datastore_version)
    else:
        raise exceptions.NoUniqueMatch(_('The datastore name or id is required'
                                         ' to retrieve a datastore version'
                                         ' by name.'))
    _print_object(datastore_version)


# configuration group related functions

@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help=_('ID or name of the instance.'))
@utils.arg('configuration',
           metavar='<configuration>',
           type=str,
           help=_('ID or name of the configuration group to attach to the'
                  ' instance.'))
@utils.service_type('database')
def do_configuration_attach(cs, args):
    """Attaches a configuration group to an instance."""
    instance = _find_instance(cs, args.instance)
    configuration = _find_configuration(cs, args.configuration)
    cs.instances.modify(instance, configuration)


@utils.arg('name', metavar='<name>',
           help=_('Name of the configuration group.'))
@utils.arg('values', metavar='<values>',
           help=_('Dictionary of the values to set.'))
@utils.arg('--datastore', metavar='<datastore>',
           help=_('Datastore assigned to the configuration group. Required if '
                  'default datastore is not configured.'))
@utils.arg('--datastore_version', metavar='<datastore_version>',
           help=_('Datastore version ID assigned to the configuration group.'))
@utils.arg('--description', metavar='<description>',
           default=None,
           help=_('An optional description for the configuration group.'))
@utils.service_type('database')
def do_configuration_create(cs, args):
    """Creates a configuration group."""
    config_grp = cs.configurations.create(
        args.name,
        args.values,
        description=args.description,
        datastore=args.datastore,
        datastore_version=args.datastore_version)
    config_grp._info['values'] = json.dumps(config_grp.values)
    _print_object(config_grp)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help=_('ID or name of the instance.'))
@utils.service_type('database')
def do_configuration_default(cs, args):
    """Shows the default configuration of an instance."""
    instance = _find_instance(cs, args.instance)
    configs = cs.instances.configuration(instance)
    utils.print_dict(configs._info['configuration'])


@utils.arg('configuration_group', metavar='<configuration_group>',
           help=_('ID or name of the configuration group.'))
@utils.service_type('database')
def do_configuration_delete(cs, args):
    """Deletes a configuration group."""
    configuration = _find_configuration(cs, args.configuration_group)
    cs.configurations.delete(configuration)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help=_('ID or name of the instance.'))
@utils.service_type('database')
def do_configuration_detach(cs, args):
    """Detaches a configuration group from an instance."""
    instance = _find_instance(cs, args.instance)
    cs.instances.modify(instance)


@utils.arg('--datastore', metavar='<datastore>',
           default=None,
           help=_('ID or name of the datastore to list configuration '
                  'parameters for. Optional if the ID of the'
                  ' datastore_version is provided.'))
@utils.arg('datastore_version',
           metavar='<datastore_version>',
           help=_('Datastore version name or ID assigned to the '
                  'configuration group.'))
@utils.arg('parameter', metavar='<parameter>',
           help=_('Name of the configuration parameter.'))
@utils.service_type('database')
def do_configuration_parameter_show(cs, args):
    """Shows details of a configuration parameter."""
    if args.datastore:
        param = cs.configuration_parameters.get_parameter(
            args.datastore,
            args.datastore_version,
            args.parameter)
    elif utils.is_uuid_like(args.datastore_version):
        param = cs.configuration_parameters.get_parameter_by_version(
            args.datastore_version,
            args.parameter)
    else:
        raise exceptions.NoUniqueMatch(_('The datastore name or id is'
                                         ' required to retrieve the'
                                         ' parameter for the configuration'
                                         ' group by name.'))
    _print_object(param)


@utils.arg('--datastore', metavar='<datastore>',
           default=None,
           help=_('ID or name of the datastore to list configuration '
                  'parameters for. Optional if the ID of the'
                  ' datastore_version is provided.'))
@utils.arg('datastore_version',
           metavar='<datastore_version>',
           help=_('Datastore version name or ID assigned to the '
                  'configuration group.'))
@utils.service_type('database')
def do_configuration_parameter_list(cs, args):
    """Lists available parameters for a configuration group."""
    if args.datastore:
        params = cs.configuration_parameters.parameters(
            args.datastore,
            args.datastore_version)
    elif utils.is_uuid_like(args.datastore_version):
        params = cs.configuration_parameters.parameters_by_version(
            args.datastore_version)
    else:
        raise exceptions.NoUniqueMatch(_('The datastore name or id is required'
                                         ' to retrieve the parameters for the'
                                         ' configuration group by name.'))
    for param in params:
        setattr(param, 'min', getattr(param, 'min', '-'))
        setattr(param, 'max', getattr(param, 'max', '-'))
    utils.print_list(
        params, ['name', 'type', 'min', 'max', 'restart_required'],
        labels={'min': 'Min Size', 'max': 'Max Size'})


@utils.arg('configuration_group', metavar='<configuration_group>',
           help=_('ID or name of the configuration group.'))
@utils.arg('values', metavar='<values>',
           help=_('Dictionary of the values to set.'))
@utils.service_type('database')
def do_configuration_patch(cs, args):
    """Patches a configuration group."""
    configuration = _find_configuration(cs, args.configuration_group)
    cs.configurations.edit(configuration, args.values)


@utils.arg('configuration_group', metavar='<configuration_group>',
           help=_('ID or name of the configuration group.'))
@utils.arg('--limit', metavar='<limit>', type=int, default=None,
           help=_('Limit the number of results displayed.'))
@utils.arg('--marker', metavar='<ID>', type=str, default=None,
           help=_('Begin displaying the results for IDs greater than the '
                  'specified marker. When used with --limit, set this to '
                  'the last ID displayed in the previous run.'))
@utils.service_type('database')
def do_configuration_instances(cs, args):
    """Lists all instances associated with a configuration group."""
    configuration = _find_configuration(cs, args.configuration_group)
    params = cs.configurations.instances(configuration,
                                         limit=args.limit,
                                         marker=args.marker)
    utils.print_list(params, ['id', 'name'])


@utils.arg('--limit', metavar='<limit>', type=int, default=None,
           help=_('Limit the number of results displayed.'))
@utils.arg('--marker', metavar='<ID>', type=str, default=None,
           help=_('Begin displaying the results for IDs greater than the '
                  'specified marker. When used with --limit, set this to '
                  'the last ID displayed in the previous run.'))
@utils.service_type('database')
def do_configuration_list(cs, args):
    """Lists all configuration groups."""
    config_grps = cs.configurations.list(limit=args.limit, marker=args.marker)
    utils.print_list(config_grps, [
        'id', 'name', 'description',
        'datastore_name', 'datastore_version_name'])


@utils.arg('configuration_group', metavar='<configuration_group>',
           help=_('ID or name of the configuration group.'))
@utils.service_type('database')
def do_configuration_show(cs, args):
    """Shows details of a configuration group."""
    configuration = _find_configuration(cs, args.configuration_group)
    config_grp = cs.configurations.get(configuration)
    config_grp._info['values'] = json.dumps(config_grp.values)

    del config_grp._info['datastore_version_id']
    _print_object(config_grp)


@utils.arg('configuration_group', metavar='<configuration_group>',
           help=_('ID or name of the configuration group.'))
@utils.arg('values', metavar='<values>',
           help=_('Dictionary of the values to set.'))
@utils.arg('--name', metavar='<name>', default=None,
           help=_('Name of the configuration group.'))
@utils.arg('--description', metavar='<description>',
           default=None,
           help=_('An optional description for the configuration group.'))
@utils.service_type('database')
def do_configuration_update(cs, args):
    """Updates a configuration group."""
    configuration = _find_configuration(cs, args.configuration_group)
    cs.configurations.update(configuration,
                             args.values,
                             args.name,
                             args.description)


@utils.arg('instance_id', metavar='<instance_id>',
           help=_('UUID for instance.'))
@utils.service_type('database')
def do_metadata_list(cs, args):
    """Shows all metadata for instance <id>."""
    result = cs.metadata.list(args.instance_id)
    _print_object(result)


@utils.arg('instance_id', metavar='<instance_id>',
           help=_('UUID for instance.'))
@utils.arg('key', metavar='<key>', help=_('Key to display.'))
@utils.service_type('database')
def do_metadata_show(cs, args):
    """Shows metadata entry for key <key> and instance <id>."""
    result = cs.metadata.show(args.instance_id, args.key)
    _print_object(result)


@utils.arg('instance_id', metavar='<instance_id>',
           help=_('UUID for instance.'))
@utils.arg('key', metavar='<key>', help=_('Key to replace.'))
@utils.arg('value', metavar='<value>',
           help=_('New value to assign to <key>.'))
@utils.service_type('database')
def do_metadata_edit(cs, args):
    """Replaces metadata value with a new one, this is non-destructive."""
    cs.metadata.edit(args.instance_id, args.key, args.value)


@utils.arg('instance_id', metavar='<instance_id>',
           help=_('UUID for instance.'))
@utils.arg('key', metavar='<key>', help=_('Key to update.'))
@utils.arg('newkey', metavar='<newkey>', help=_('New key.'))
@utils.arg('value', metavar='<value>', help=_('Value to assign to <newkey>.'))
@utils.service_type('database')
def do_metadata_update(cs, args):
    """Updates metadata, this is destructive."""
    cs.metadata.update(args.instance_id, args.key, args.newkey, args.value)


@utils.arg('instance_id', metavar='<instance_id>',
           help=_('UUID for instance.'))
@utils.arg('key', metavar='<key>', help=_('Key for assignment.'))
@utils.arg('value', metavar='<value>', help=_('Value to assign to <key>.'))
@utils.service_type('database')
def do_metadata_create(cs, args):
    """Creates metadata in the database for instance <id>."""
    result = cs.metadata.create(args.instance_id, args.key, args.value)
    _print_object(result)


@utils.arg('instance_id', metavar='<instance_id>',
           help=_('UUID for instance.'))
@utils.arg('key', metavar='<key>', help=_('Metadata key to delete.'))
@utils.service_type('database')
def do_metadata_delete(cs, args):
    """Deletes metadata for instance <id>."""
    cs.metadata.delete(args.instance_id, args.key)


@utils.arg('--datastore', metavar='<datastore>',
           help=_("Name or ID of datastore to list modules for. Use '%s' "
                  "to list modules that apply to all datastores.")
           % modules.Module.ALL_KEYWORD)
@utils.service_type('database')
def do_module_list(cs, args):
    """Lists the modules available."""
    datastore = None
    if args.datastore:
        if args.datastore.lower() == modules.Module.ALL_KEYWORD:
            datastore = args.datastore.lower()
        else:
            datastore = _find_datastore(cs, args.datastore)
    module_list = cs.modules.list(datastore=datastore)
    field_list = ['id', 'name', 'type', 'datastore',
                  'datastore_version', 'auto_apply',
                  'priority_apply', 'apply_order', 'is_admin',
                  'tenant', 'visible']
    if not utils.is_admin(cs):
        field_list = field_list[:-2]
    utils.print_list(
        module_list, field_list,
        labels={'datastore_version': 'Version',
                'priority_apply': 'Priority',
                'apply_order': 'Order',
                'is_admin': 'Admin'})


@utils.arg('module', metavar='<module>',
           help=_('ID or name of the module.'))
@utils.service_type('database')
def do_module_show(cs, args):
    """Shows details of a module."""
    module = _find_module(cs, args.module)
    _print_object(module)


@utils.arg('name', metavar='<name>', type=str, help=_('Name of the module.'))
@utils.arg('type', metavar='<type>', type=str,
           help=_('Type of the module. The type must be supported by a '
                  'corresponding module plugin on the datastore it is '
                  'applied to.'))
@utils.arg('file', metavar='<filename>',
           type=argparse.FileType(mode='rb', bufsize=0),
           help=_('File containing data contents for the module.'))
@utils.arg('--description', metavar='<description>', type=str,
           help=_('Description of the module.'))
@utils.arg('--datastore', metavar='<datastore>',
           help=_('Name or ID of datastore this module can be applied to. '
                  'If not specified, module can be applied to all '
                  'datastores.'))
@utils.arg('--datastore_version', metavar='<version>',
           help=_('Name or ID of datastore version this module can be applied '
                  'to. If not specified, module can be applied to all '
                  'versions.'))
@utils.arg('--auto_apply', action='store_true', default=False,
           help=_('Automatically apply this module when creating an instance '
                  'or cluster. Admin only.'))
@utils.arg('--all_tenants', action='store_true', default=False,
           help=_('Module is valid for all tenants. Admin only.'))
@utils.arg('--hidden', action='store_true', default=False,
           help=_('Hide this module from non-Admin. Useful in creating '
                  'auto-apply modules without cluttering up module lists. '
                  'Admin only.'))
@utils.arg('--live_update', action='store_true', default=False,
           help=_('Allow module to be updated even if it is already applied '
                  'to a current instance or cluster.'))
@utils.arg('--priority_apply', action='store_true', default=False,
           help=_('Sets a priority for applying the module. All priority '
                  'modules will be applied before non-priority ones. '
                  'Admin only.'))
@utils.arg('--apply_order', type=int, default=5, choices=range(0, 10),
           help=_('Sets an order for applying the module. Modules with a '
                  'lower value will be applied before modules with a higher '
                  'value. Modules having the same value may be '
                  'applied in any order (default %(default)s).'))
@utils.arg('--full_access', action='store_true', default=None,
           help=_("Marks a module as 'non-admin', unless an admin-only "
                  "option was specified. Admin only."))
@utils.service_type('database')
def do_module_create(cs, args):
    """Create a module."""

    contents = args.file.read()
    if not contents:
        raise exceptions.ValidationError(
            _("The file '%s' must contain some data") % args.file)

    module = cs.modules.create(
        args.name, args.type, contents, description=args.description,
        all_tenants=args.all_tenants, datastore=args.datastore,
        datastore_version=args.datastore_version,
        auto_apply=args.auto_apply, visible=not args.hidden,
        live_update=args.live_update, priority_apply=args.priority_apply,
        apply_order=args.apply_order, full_access=args.full_access)
    _print_object(module)


@utils.arg('module', metavar='<module>', type=str,
           help=_('Name or ID of the module.'))
@utils.arg('--name', metavar='<name>', type=str, default=None,
           help=_('Name of the module.'))
@utils.arg('--type', metavar='<type>', type=str, default=None,
           help=_('Type of the module. The type must be supported by a '
                  'corresponding module driver plugin on the datastore it is '
                  'applied to.'))
@utils.arg('--file', metavar='<filename>', type=argparse.FileType('rb', 0),
           default=None,
           help=_('File containing data contents for the module.'))
@utils.arg('--description', metavar='<description>', type=str, default=None,
           help=_('Description of the module.'))
@utils.arg('--datastore', metavar='<datastore>',
           default=None,
           help=_('Name or ID of datastore this module can be applied to. '
                  'If not specified, module can be applied to all '
                  'datastores.'))
@utils.arg('--all_datastores', default=None, action='store_const', const=True,
           help=_('Module is valid for all datastores.'))
@utils.arg('--datastore_version', metavar='<version>',
           default=None,
           help=_('Name or ID of datastore version this module can be applied '
                  'to. If not specified, module can be applied to all '
                  'versions.'))
@utils.arg('--all_datastore_versions', default=None,
           action='store_const', const=True,
           help=_('Module is valid for all datastore versions.'))
@utils.arg('--auto_apply', action='store_true', default=None,
           help=_('Automatically apply this module when creating an instance '
                  'or cluster. Admin only.'))
@utils.arg('--no_auto_apply', dest='auto_apply', action='store_false',
           default=None,
           help=_('Do not automatically apply this module when creating an '
                  'instance or cluster. Admin only.'))
@utils.arg('--all_tenants', action='store_true', default=None,
           help=_('Module is valid for all tenants. Admin only.'))
@utils.arg('--no_all_tenants', dest='all_tenants', action='store_false',
           default=None,
           help=_('Module is valid for current tenant only. Admin only.'))
@utils.arg('--hidden', action='store_true', default=None,
           help=_('Hide this module from non-admin users. Useful in creating '
                  'auto-apply modules without cluttering up module lists. '
                  'Admin only.'))
@utils.arg('--no_hidden', dest='hidden', action='store_false', default=None,
           help=_('Allow all users to see this module. Admin only.'))
@utils.arg('--live_update', action='store_true', default=None,
           help=_('Allow module to be updated or deleted even if it is '
                  'already applied to a current instance or cluster.'))
@utils.arg('--no_live_update', dest='live_update', action='store_false',
           default=None,
           help=_('Restricts a module from being updated or deleted if it is '
                  'already applied to a current instance or cluster.'))
@utils.arg('--priority_apply', action='store_true', default=None,
           help=_('Sets a priority for applying the module. All priority '
                  'modules will be applied before non-priority ones. '
                  'Admin only.'))
@utils.arg('--no_priority_apply', dest='priority_apply', action='store_false',
           default=None,
           help=_('Removes apply priority from the module. Admin only.'))
@utils.arg('--apply_order', type=int, default=None, choices=range(0, 10),
           help=_('Sets an order for applying the module. Modules with a '
                  'lower value will be applied before modules with a higher '
                  'value. Modules having the same value may be '
                  'applied in any order (default %(default)s).'))
@utils.arg('--full_access', action='store_true', default=None,
           help=_("Marks a module as 'non-admin', unless an admin-only "
                  "option was specified. Admin only."))
@utils.arg('--no_full_access', dest='full_access', action='store_false',
           default=None,
           help=_('Restricts modification access for non-admin. Admin only.'))
@utils.service_type('database')
def do_module_update(cs, args):
    """Update a module."""
    module = _find_module(cs, args.module)
    contents = args.file.read() if args.file else None
    visible = not args.hidden if args.hidden is not None else None
    datastore_args = {'datastore': args.datastore,
                      'datastore_version': args.datastore_version}
    updated_module = cs.modules.update(
        module, name=args.name, module_type=args.type, contents=contents,
        description=args.description, all_tenants=args.all_tenants,
        auto_apply=args.auto_apply, visible=visible,
        live_update=args.live_update, all_datastores=args.all_datastores,
        all_datastore_versions=args.all_datastore_versions,
        priority_apply=args.priority_apply,
        apply_order=args.apply_order, full_access=args.full_access,
        **datastore_args)
    _print_object(updated_module)


@utils.arg('module', metavar='<module>', type=str,
           help=_('Name or ID of the module.'))
@utils.arg('--md5', metavar='<md5>', type=str,
           default=None,
           help=_('Reapply the module only to instances applied '
                  'with the specific md5.'))
@utils.arg('--include_clustered', action='store_true', default=False,
           help=_('Include instances that are part of a cluster '
                  '(default %(default)s).'))
@utils.arg('--batch_size', metavar='<batch_size>', type=int,
           default=None,
           help=_('Number of instances to reapply the module to before '
                  'sleeping.'))
@utils.arg('--delay', metavar='<delay>', type=int,
           default=None,
           help=_('Time to sleep in seconds between applying batches.'))
@utils.arg('--force', action='store_true', default=False,
           help=_('Force reapply even on modules already having the '
                  'current MD5'))
@utils.service_type('database')
def do_module_reapply(cs, args):
    """Reapply a module."""
    module = _find_module(cs, args.module)
    cs.modules.reapply(module, args.md5, args.include_clustered,
                       args.batch_size, args.delay, args.force)


@utils.arg('module', metavar='<module>',
           help=_('ID or name of the module.'))
@utils.service_type('database')
def do_module_delete(cs, args):
    """Delete a module."""
    module = _find_module(cs, args.module)
    cs.modules.delete(module)


@utils.arg('instance', metavar='<instance>', type=str,
           help=_('ID or name of the instance.'))
@utils.service_type('database')
def do_module_list_instance(cs, args):
    """Lists the modules that have been applied to an instance."""
    instance = _find_instance(cs, args.instance)
    module_list = cs.instances.modules(instance)
    utils.print_list(
        module_list, ['id', 'name', 'type', 'md5', 'created', 'updated'])


@utils.arg('module', metavar='<module>', type=str,
           help=_('ID or name of the module.'))
@utils.arg('--include_clustered', action="store_true", default=False,
           help=_("Include instances that are part of a cluster "
                  "(default %(default)s)."))
@utils.arg('--limit', metavar='<limit>', default=None,
           help=_('Return up to N number of the most recent results.'))
@utils.arg('--marker', metavar='<ID>', type=str, default=None,
           help=_('Begin displaying the results for IDs greater than the '
                  'specified marker. When used with --limit, set this to '
                  'the last ID displayed in the previous run.'))
@utils.service_type('database')
def do_module_instances(cs, args):
    """Lists the instances that have a particular module applied."""
    module = _find_module(cs, args.module)
    items = cs.modules.instances(
        module, limit=args.limit, marker=args.marker,
        include_clustered=args.include_clustered)
    instance_list = items
    while not args.limit and items.next:
        items = cs.modules.instances(module, marker=items.next)
        instance_list += items
    _print_instances(instance_list, utils.is_admin(cs))


@utils.arg('module', metavar='<module>', type=str,
           help=_('ID or name of the module.'))
@utils.arg('--include_clustered', action="store_true", default=False,
           help=_("Include instances that are part of a cluster "
                  "(default %(default)s)."))
@utils.service_type('database')
def do_module_instance_count(cs, args):
    """Lists a count of the instances for each module md5."""
    module = _find_module(cs, args.module)
    count_list = cs.modules.instances(
        module, include_clustered=args.include_clustered,
        count_only=True)
    field_list = ['module_name', 'min_updated_date', 'max_updated_date',
                  'module_md5', 'current', 'instance_count']
    utils.print_list(count_list, field_list,
                     labels={'module_md5': 'Module MD5',
                             'instance_count': 'Count',
                             'module_id': 'Module ID'})


@utils.arg('cluster', metavar='<cluster>',
           help=_('ID or name of the cluster.'))
@utils.service_type('database')
def do_cluster_modules(cs, args):
    """Lists all modules for each instance of a cluster."""
    cluster = _find_cluster(cs, args.cluster)
    instances = cluster._info['instances']
    module_list = []
    for instance in instances:
        new_list = cs.instances.modules(instance['id'])
        for item in new_list:
            item.instance_id = instance['id']
            item.instance_name = instance['name']
        module_list += new_list
    utils.print_list(
        module_list,
        ['instance_name', 'name', 'type', 'md5', 'created', 'updated'],
        labels={'name': 'Module Name', 'type': 'Module Type'})


@utils.arg('instance', metavar='<instance>', type=str,
           help=_('ID or name of the instance.'))
@utils.arg('modules', metavar='<module>', type=str, nargs='+', default=[],
           help=_('ID or name of the module.'))
@utils.service_type('database')
def do_module_apply(cs, args):
    """Apply modules to an instance."""
    instance = _find_instance(cs, args.instance)
    modules = []
    for module in args.modules:
        modules.append(_find_module(cs, module))

    result_list = cs.instances.module_apply(instance, modules)
    utils.print_list(
        result_list,
        ['name', 'type', 'datastore',
         'datastore_version', 'status', 'message'],
        labels={'datastore_version': 'Version'})


@utils.arg('instance', metavar='<instance>', type=str,
           help=_('ID or name of the instance.'))
@utils.arg('module', metavar='<module>', type=str,
           help=_('ID or name of the module.'))
@utils.service_type('database')
def do_module_remove(cs, args):
    """Remove a module from an instance."""
    instance = _find_instance(cs, args.instance)
    module = _find_module(cs, args.module)
    cs.instances.module_remove(instance, module)


@utils.arg('instance', metavar='<instance>', type=str,
           help=_('ID or name of the instance.'))
@utils.service_type('database')
def do_module_query(cs, args):
    """Query the status of the modules on an instance."""
    instance = _find_instance(cs, args.instance)
    result_list = cs.instances.module_query(instance)
    utils.print_list(
        result_list,
        ['name', 'type', 'datastore',
         'datastore_version', 'status', 'message', 'created', 'updated'],
        labels={'datastore_version': 'Version'})


@utils.arg('instance', metavar='<instance>', type=str,
           help=_('ID or name of the instance.'))
@utils.arg('--directory', metavar='<directory>', type=str,
           help=_('Directory to write module content files in. It will '
                  'be created if it does not exist. Defaults to the '
                  'current directory.'))
@utils.arg('--prefix', metavar='<filename_prefix>', type=str,
           help=_('Prefix to prepend to generated filename for each module.'))
@utils.service_type('database')
def do_module_retrieve(cs, args):
    """Retrieve module contents from an instance."""
    instance = _find_instance(cs, args.instance)
    saved_modules = cs.instances.module_retrieve(
        instance, args.directory, args.prefix)
    for module_name, filename in saved_modules.items():
        print(_("Module contents for '%(module)s' written to '%(file)s'") %
              {'module': module_name,
               'file': filename})


@utils.arg('instance', metavar='<instance>',
           help=_('Id or Name of the instance.'))
@utils.service_type('database')
def do_log_list(cs, args):
    """Lists the log files available for instance."""
    instance = _find_instance(cs, args.instance)
    log_list = cs.instances.log_list(instance)
    utils.print_list(log_list,
                     ['name', 'type', 'status', 'published', 'pending',
                      'container', 'prefix'])


@utils.arg('instance', metavar='<instance>',
           help=_('Id or Name of the instance.'))
@utils.arg('log_name', metavar='<log_name>', help=_('Name of log to show.'))
@utils.service_type('database')
def do_log_show(cs, args):
    """Instructs Trove guest to show details of log."""
    try:
        instance = _find_instance(cs, args.instance)
        log_info = cs.instances.log_show(instance, args.log_name)
        _print_object(log_info)
    except exceptions.GuestLogNotFoundError:
        print(NO_LOG_FOUND_ERROR % {'log_name': args.log_name,
                                    'instance': instance})
    except Exception as ex:
        error_msg = ex.message.split('\n')
        print(error_msg[0])


@utils.arg('instance', metavar='<instance>',
           help=_('Id or Name of the instance.'))
@utils.arg('log_name', metavar='<log_name>',
           help=_('Name of log to publish.'))
@utils.service_type('database')
def do_log_enable(cs, args):
    """Instructs Trove guest to start collecting log details."""
    try:
        instance = _find_instance(cs, args.instance)
        log_info = cs.instances.log_enable(instance, args.log_name)
        _print_object(log_info)
    except exceptions.GuestLogNotFoundError:
        print(NO_LOG_FOUND_ERROR % {'log_name': args.log_name,
                                    'instance': instance})
    except Exception as ex:
        error_msg = ex.message.split('\n')
        print(error_msg[0])


@utils.arg('instance', metavar='<instance>',
           help=_('Id or Name of the instance.'))
@utils.arg('log_name', metavar='<log_name>', help=_('Name of log to publish.'))
@utils.arg('--discard', action='store_true', default=False,
           help=_('Discard published contents of specified log.'))
@utils.service_type('database')
def do_log_disable(cs, args):
    """Instructs Trove guest to stop collecting log details."""
    try:
        instance = _find_instance(cs, args.instance)
        log_info = cs.instances.log_disable(instance, args.log_name,
                                            discard=args.discard)
        _print_object(log_info)
    except exceptions.GuestLogNotFoundError:
        print(NO_LOG_FOUND_ERROR % {'log_name': args.log_name,
                                    'instance': instance})
    except Exception as ex:
        error_msg = ex.message.split('\n')
        print(error_msg[0])


@utils.arg('instance', metavar='<instance>',
           help=_('Id or Name of the instance.'))
@utils.arg('log_name', metavar='<log_name>', help=_('Name of log to publish.'))
@utils.arg('--disable', action='store_true', default=False,
           help=_('Stop collection of specified log.'))
@utils.arg('--discard', action='store_true', default=False,
           help=_('Discard published contents of specified log.'))
@utils.service_type('database')
def do_log_publish(cs, args):
    """Instructs Trove guest to publish latest log entries on instance."""
    try:
        instance = _find_instance(cs, args.instance)
        log_info = cs.instances.log_publish(
            instance, args.log_name, disable=args.disable,
            discard=args.discard)
        _print_object(log_info)
    except exceptions.GuestLogNotFoundError:
        print(NO_LOG_FOUND_ERROR % {'log_name': args.log_name,
                                    'instance': instance})
    except Exception as ex:
        error_msg = ex.message.split('\n')
        print(error_msg[0])


@utils.arg('instance', metavar='<instance>',
           help=_('Id or Name of the instance.'))
@utils.arg('log_name', metavar='<log_name>', help=_('Name of log to publish.'))
@utils.service_type('database')
def do_log_discard(cs, args):
    """Instructs Trove guest to discard the container of the published log."""
    try:
        instance = _find_instance(cs, args.instance)
        log_info = cs.instances.log_discard(instance, args.log_name)
        _print_object(log_info)
    except exceptions.GuestLogNotFoundError:
        print(NO_LOG_FOUND_ERROR % {'log_name': args.log_name,
                                    'instance': instance})
    except Exception as ex:
        error_msg = ex.message.split('\n')
        print(error_msg[0])


@utils.arg('instance', metavar='<instance>',
           help=_('Id or Name of the instance.'))
@utils.arg('log_name', metavar='<log_name>', help=_('Name of log to publish.'))
@utils.arg('--publish', action='store_true', default=False,
           help=_('Publish latest entries from guest before display.'))
@utils.arg('--lines', metavar='<lines>', default=50, type=int,
           help=_('Publish latest entries from guest before display.'))
@utils.service_type('database')
def do_log_tail(cs, args):
    """Display log entries for instance."""
    try:
        instance = _find_instance(cs, args.instance)
        log_gen = cs.instances.log_generator(instance, args.log_name,
                                             args.publish, args.lines)
        for log_part in log_gen():
            print(log_part, end="")
    except exceptions.GuestLogNotFoundError:
        print(NO_LOG_FOUND_ERROR % {'log_name': args.log_name,
                                    'instance': instance})
    except Exception as ex:
        error_msg = ex.message.split('\n')
        print(error_msg[0])


@utils.arg('instance', metavar='<instance>',
           help=_('Id or Name of the instance.'))
@utils.arg('log_name', metavar='<log_name>', help=_('Name of log to publish.'))
@utils.arg('--publish', action='store_true', default=False,
           help=_('Publish latest entries from guest before display.'))
@utils.arg('--file', metavar='<file>', default=None,
           help=_('Path of file to save log to for instance.'))
@utils.service_type('database')
def do_log_save(cs, args):
    """Save log file for instance."""
    try:
        instance = _find_instance(cs, args.instance)
        filename = cs.instances.log_save(instance, args.log_name,
                                         args.publish, args.file)
        print(_('Log "%(log_name)s" written to %(file_name)s')
              % {'log_name': args.log_name,
                 'file_name': filename})
    except exceptions.GuestLogNotFoundError:
        print(NO_LOG_FOUND_ERROR % {'log_name': args.log_name,
                                    'instance': instance})
    except Exception as ex:
        error_msg = ex.message.split('\n')
        print(error_msg[0])


# @utils.arg('datastore_version',
#            metavar='<datastore_version>',
#            help='Datastore version name or UUID assigned to the '
#                 'configuration group.')
# @utils.arg('name', metavar='<name>',
#            help='Name of the datastore configuration parameter.')
# @utils.arg('restart_required', metavar='<restart_required>',
#            help='Flags the instance to require a restart if this '
#                 'configuration parameter is new or changed.')
# @utils.arg('data_type', metavar='<data_type>',
#            help='Data type of the datastore configuration parameter.')
# @utils.arg('--max_size', metavar='<max_size>',
#            help='Maximum size of the datastore configuration parameter.')
# @utils.arg('--min_size', metavar='<min_size>',
#            help='Minimum size of the datastore configuration parameter.')
# @utils.service_type('database')
# def do_configuration_parameter_create(cs, args):
#     """Create datastore configuration parameter"""
#     cs.mgmt_config_params.create(
#         args.datastore_version,
#         args.name,
#         args.restart_required,
#         args.data_type,
#         args.max_size,
#         args.min_size,
#     )


# @utils.arg('datastore_version',
#            metavar='<datastore_version>',
#            help='Datastore version name or UUID assigned to the '
#                 'configuration group.')
# @utils.arg('name', metavar='<name>',
#            help='Name of the datastore configuration parameter.')
# @utils.arg('restart_required', metavar='<restart_required>',
#            help='Sets the datastore configuration parameter if it '
#                 'requires a restart or not.')
# @utils.arg('data_type', metavar='<data_type>',
#            help='Data type of the datastore configuration parameter.')
# @utils.arg('--max_size', metavar='<max_size>',
#            help='Maximum size of the datastore configuration parameter.')
# @utils.arg('--min_size', metavar='<min_size>',
#            help='Minimum size of the datastore configuration parameter.')
# @utils.service_type('database')
# def do_configuration_parameter_modify(cs, args):
#     """Modify datastore configuration parameter"""
#     cs.mgmt_config_params.modify(
#         args.datastore_version,
#         args.name,
#         args.restart_required,
#         args.data_type,
#         args.max_size,
#         args.min_size,
#     )


# @utils.arg('datastore_version',
#            metavar='<datastore_version>',
#            help='Datastore version name or UUID assigned to the '
#                 'configuration group.')
# @utils.arg('name', metavar='<name>',
#            help='UUID of the datastore configuration parameter.')
# @utils.service_type('database')
# def do_configuration_parameter_delete(cs, args):
#     """Modify datastore configuration parameter"""
#     cs.mgmt_config_params.delete(
#         args.datastore_version,
#         args.name,
#     )

@utils.arg('tenant_id', metavar='<tenant_id>',
           help=_('Id of tenant for which to show quotas.'))
@utils.service_type('database')
def do_quota_show(cs, args):
    """Show quotas for a tenant."""
    utils.print_list(cs.quota.show(args.tenant_id),
                     ['resource', 'in_use', 'reserved', 'limit'])


@utils.arg('tenant_id', metavar='<tenant_id>',
           help=_('Id of tenant for which to update quotas.'))
@utils.arg('resource', metavar='<resource>',
           help=_('Id of resource to change.'))
@utils.arg('limit', metavar='<limit>', type=int,
           help=_('New limit to set for the named resource.'))
@utils.service_type('database')
def do_quota_update(cs, args):
    """Update quotas for a tenant."""
    utils.print_dict(cs.quota.update(args.tenant_id,
                                     {args.resource: args.limit}))
