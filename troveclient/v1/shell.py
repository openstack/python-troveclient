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

INSTANCE_ERROR = ("Instance argument(s) must be of the form --instance "
                  "<opt=value[,opt=value]> - see help for details.")
NIC_ERROR = ("Invalid NIC argument: %s. Must specify either net-id or port-id "
             "but not both. Please refer to help.")
NO_LOG_FOUND_ERROR = "ERROR: No published '%s' log was found for %s."

try:
    import simplejson as json
except ImportError:
    import json

from troveclient import exceptions
from troveclient import utils


def _poll_for_status(poll_fn, obj_id, action, final_ok_states,
                     poll_period=5, show_progress=True):
    """Block while an action is being performed, periodically printing
    progress.
    """
    def print_progress(progress):
        if show_progress:
            msg = ('\rInstance %(action)s... %(progress)s%% complete'
                   % dict(action=action, progress=progress))
        else:
            msg = '\rInstance %(action)s...' % dict(action=action)

        sys.stdout.write(msg)
        sys.stdout.flush()

    print()
    while True:
        obj = poll_fn(obj_id)
        status = obj.status.lower()
        progress = getattr(obj, 'progress', None) or 0
        if status in final_ok_states:
            print_progress(100)
            print("\nFinished")
            break
        elif status == "error":
            print("\nError %(action)s instance" % {'action': action})
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
                "No instance or cluster with a name or ID of '%s' exists."
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


# Flavor related calls
@utils.arg('--datastore_type', metavar='<datastore_type>',
           default=None,
           help='Type of the datastore. For eg: mysql.')
@utils.arg("--datastore_version_id", metavar="<datastore_version_id>",
           default=None, help="ID of the datastore version.")
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

    utils.print_list(_flavors, ['id', 'name', 'ram'],
                     labels={'ram': 'RAM'})


@utils.arg('flavor', metavar='<flavor>', help='ID or name of the flavor.')
@utils.service_type('database')
def do_flavor_show(cs, args):
    """Shows details of a flavor."""
    flavor = _find_flavor(cs, args.flavor)
    _print_object(flavor)


# Instance related calls

@utils.arg('--limit', metavar='<limit>', type=int, default=None,
           help='Limit the number of results displayed.')
@utils.arg('--marker', metavar='<ID>', type=str, default=None,
           help='Begin displaying the results for IDs greater than the '
                'specified marker. When used with --limit, set this to '
                'the last ID displayed in the previous run.')
@utils.arg('--include-clustered', dest='include_clustered',
           action="store_true", default=False,
           help="Include instances that are part of a cluster "
                "(default false).")
@utils.service_type('database')
def do_list(cs, args):
    """Lists all the instances."""
    instances = cs.instances.list(limit=args.limit, marker=args.marker,
                                  include_clustered=args.include_clustered)

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
    utils.print_list(instances, ['id', 'name', 'datastore',
                                 'datastore_version', 'status',
                                 'flavor_id', 'size'])


@utils.arg('--limit', metavar='<limit>', type=int, default=None,
           help='Limit the number of results displayed.')
@utils.arg('--marker', metavar='<ID>', type=str, default=None,
           help='Begin displaying the results for IDs greater than the '
                'specified marker. When used with --limit, set this to '
                'the last ID displayed in the previous run.')
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
           help='ID or name of the instance.')
@utils.service_type('database')
def do_show(cs, args):
    """Shows details of an instance."""
    instance = _find_instance(cs, args.instance)
    _print_instance(instance)


@utils.arg('cluster', metavar='<cluster>', help='ID or name of the cluster.')
@utils.service_type('database')
def do_cluster_show(cs, args):
    """Shows details of a cluster."""
    cluster = _find_cluster(cs, args.cluster)
    info = cluster._info.copy()
    info['datastore'] = cluster.datastore['type']
    info['datastore_version'] = cluster.datastore['version']
    info['task_name'] = cluster.task['name']
    info['task_description'] = cluster.task['description']
    del info['task']
    if hasattr(cluster, 'ip'):
        info['ip'] = ', '.join(cluster.ip)
    del info['instances']
    cluster._info = info
    _print_object(cluster)


@utils.arg('cluster', metavar='<cluster>', help='ID or name of the cluster.')
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


@utils.arg('--instance',
           metavar="<name=name,flavor=flavor_name_or_id,volume=volume>",
           action='append',
           dest='instances',
           default=[],
           help="Add an instance to the cluster. Specify "
                "multiple times to create multiple instances.")
@utils.arg('cluster', metavar='<cluster>', help='ID or name of the cluster.')
@utils.service_type('database')
def do_cluster_grow(cs, args):
    """Adds more instances to a cluster."""
    cluster = _find_cluster(cs, args.cluster)
    instances = []
    for instance_str in args.instances:
        instance_info = {}
        for z in instance_str.split(","):
            for (k, v) in [z.split("=", 1)[:2]]:
                if k == "name":
                    instance_info[k] = v
                elif k == "flavor":
                    flavor_id = _find_flavor(cs, v).id
                    instance_info["flavorRef"] = str(flavor_id)
                elif k == "volume":
                    instance_info["volume"] = {"size": v}
                else:
                    instance_info[k] = v
        if not instance_info.get('flavorRef'):
            raise exceptions.CommandError(
                'flavor is required. '
                'Instance arguments must be of the form '
                '--instance <flavor=flavor_name_or_id,volume=volume,data=data>'
            )
        instances.append(instance_info)
    cs.clusters.grow(cluster, instances=instances)


@utils.arg('cluster', metavar='<cluster>', help='ID or name of the cluster.')
@utils.arg('instances',
           nargs='+',
           metavar='<instance>',
           default=[],
           help="Drop instance(s) from the cluster. Specify "
                "multiple ids to drop multiple instances.")
@utils.service_type('database')
def do_cluster_shrink(cs, args):
    """Drops instances from a cluster."""
    cluster = _find_cluster(cs, args.cluster)
    instances = [{'id': _find_instance(cs, instance).id}
                 for instance in args.instances]
    cs.clusters.shrink(cluster, instances=instances)


@utils.arg('instance', metavar='<instance>',
           help='ID or name  of the instance.')
@utils.service_type('database')
def do_delete(cs, args):
    """Deletes an instance."""
    instance = _find_instance(cs, args.instance)
    cs.instances.delete(instance)


@utils.arg('cluster', metavar='<cluster>', help='ID or name of the cluster.')
@utils.service_type('database')
def do_cluster_delete(cs, args):
    """Deletes a cluster."""
    cluster = _find_cluster(cs, args.cluster)
    cs.clusters.delete(cluster)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
@utils.arg('--name',
           metavar='<name>',
           type=str,
           default=None,
           help='Name of the instance.')
@utils.arg('--configuration',
           metavar='<configuration>',
           type=str,
           default=None,
           help='ID of the configuration reference to attach.')
@utils.arg('--detach-replica-source',
           dest='detach_replica_source',
           action="store_true",
           default=False,
           help='Detach the replica instance from its replication source.')
@utils.arg('--remove_configuration',
           dest='remove_configuration',
           action="store_true",
           default=False,
           help='Drops the current configuration reference.')
@utils.service_type('database')
def do_update(cs, args):
    """Updates an instance: Edits name, configuration, or replica source."""
    instance = _find_instance(cs, args.instance)
    cs.instances.edit(instance, args.configuration, args.name,
                      args.detach_replica_source, args.remove_configuration)


@utils.arg('name',
           metavar='<name>',
           type=str,
           help='Name of the instance.')
@utils.arg('--size',
           metavar='<size>',
           type=int,
           default=None,
           help="Size of the instance disk volume in GB. "
                "Required when volume support is enabled.")
@utils.arg('--volume_type',
           metavar='<volume_type>',
           type=str,
           default=None,
           help="Volume type. Optional when volume support is enabled.")
@utils.arg('flavor',
           metavar='<flavor>',
           help='Flavor ID or name of the instance.')
@utils.arg('--databases', metavar='<databases>',
           help='Optional list of databases.',
           nargs="+", default=[])
@utils.arg('--users', metavar='<users>',
           help='Optional list of users in the form user:password.',
           nargs="+", default=[])
@utils.arg('--backup',
           metavar='<backup>',
           default=None,
           help='A backup ID.')
@utils.arg('--availability_zone',
           metavar='<availability_zone>',
           default=None,
           help='The Zone hint to give to nova.')
@utils.arg('--datastore',
           metavar='<datastore>',
           default=None,
           help='A datastore name or ID.')
@utils.arg('--datastore_version',
           metavar='<datastore_version>',
           default=None,
           help='A datastore version name or ID.')
@utils.arg('--nic',
           metavar="<net-id=net-uuid,v4-fixed-ip=ip-addr,port-id=port-uuid>",
           action='append',
           dest='nics',
           default=[],
           help="Create a NIC on the instance. "
                "Specify option multiple times to create multiple NICs. "
                "net-id: attach NIC to network with this ID "
                "(either port-id or net-id must be specified), "
                "v4-fixed-ip: IPv4 fixed address for NIC (optional), "
                "port-id: attach NIC to port with this ID "
                "(either port-id or net-id must be specified).")
@utils.arg('--configuration',
           metavar='<configuration>',
           default=None,
           help='ID of the configuration group to attach to the instance.')
@utils.arg('--replica_of',
           metavar='<source_instance>',
           default=None,
           help='ID or name of an existing instance to replicate from.')
@utils.arg('--replica_count',
           metavar='<count>',
           type=int,
           default=1,
           help='Number of replicas to create (defaults to 1).')
@utils.service_type('database')
def do_create(cs, args):
    """Creates a new instance."""
    volume = None
    replica_of_instance = None
    flavor_id = _find_flavor(cs, args.flavor).id
    if args.size:
        volume = {"size": args.size,
                  "type": args.volume_type}
    restore_point = None
    if args.backup:
        restore_point = {"backupRef": args.backup}
    if args.replica_of:
        replica_of_instance = _find_instance(cs, args.replica_of)
    databases = [{'name': value} for value in args.databases]
    users = [{'name': n, 'password': p, 'databases': databases} for (n, p) in
             [z.split(':')[:2] for z in args.users]]
    nics = []
    for nic_str in args.nics:
        nic_info = dict([(k, v) for (k, v) in [z.split("=", 1)[:2] for z in
                                               nic_str.split(",")]])
        _validate_nic_info(nic_info, nic_str)
        nics.append(nic_info)

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
                                   replica_of=replica_of_instance,
                                   replica_count=args.replica_count)
    _print_instance(instance)


def _validate_nic_info(nic_info, nic_str):
    # need one or the other, not both, not none (!= ~ XOR)
    if not (bool(nic_info.get('net-id')) != bool(nic_info.get('port-id'))):
        raise exceptions.ValidationError(NIC_ERROR % ("nic='%s'" % nic_str))


def _get_flavors(cs, instance_str):
    flavor_name = _get_instance_property(instance_str, 'flavor', True)
    flavor_id = _find_flavor(cs, flavor_name).id
    return str(flavor_id)


def _get_networks(instance_str):
    nic_args = _dequote(_get_instance_property(instance_str, 'nic',
                                               is_required=False, quoted=True))

    nic_info = {}
    if nic_args:
        net_id = _get_instance_property(nic_args, 'net-id', False)
        port_id = _get_instance_property(nic_args, 'port-id', False)
        fixed_ipv4 = _get_instance_property(nic_args, 'v4-fixed-ip', False)

        if net_id:
            nic_info.update({'net-id': net_id})
        if port_id:
            nic_info.update({'port-id': port_id})
        if fixed_ipv4:
            nic_info.update({'v4-fixed-ip': fixed_ipv4})

        _validate_nic_info(nic_info, nic_args)
        return [nic_info]

    return None


def _dequote(value):
    def _strip_quotes(value, quote_char):
        if value:
            return value.strip(quote_char)
        return value

    return _strip_quotes(_strip_quotes(value, "'"), '"')


def _get_volumes(instance_str):
    volume_size = _get_instance_property(instance_str, 'volume', True)
    volume_type = _get_instance_property(instance_str, 'volume_type', False)

    volume_info = {"size": volume_size}
    if volume_type:
        volume_info.update({"type": volume_type})

    return volume_info


def _get_availability_zones(instance_str):
    return _get_instance_property(instance_str, 'availability_zone', False)


def _get_instance_property(instance_str, property_name, is_required=True,
                           quoted=False):
    if property_name in instance_str:
        try:
            left = instance_str.split('%s=' % property_name)[1]

            # Handle complex (quoted) properties. Strip the quotes.
            quote = left[0]
            if quote in ["'", '"']:
                left = left[1:]
            else:
                if quoted:
                    # Fail if quotes are required.
                    raise exceptions.ValidationError(
                        "Invalid '%s' parameter. The value must be quoted."
                        % property_name)
                quote = ''

            property_value = left.split('%s,' % quote)[0]
            return str(property_value).strip()
        except IndexError:
            raise exceptions.ValidationError("Invalid '%s' parameter. %s."
                                             % (property_name, INSTANCE_ERROR))

    if is_required:
        raise exceptions.MissingArgs([property_name])

    return None


@utils.arg('name',
           metavar='<name>',
           type=str,
           help='Name of the cluster.')
@utils.arg('datastore',
           metavar='<datastore>',
           help='A datastore name or ID.')
@utils.arg('datastore_version',
           metavar='<datastore_version>',
           help='A datastore version name or ID.')
@utils.arg('--instance',
           metavar='"<opt=value,opt=value,...>"',
           help="Create an instance for the cluster.  Specify multiple "
                "times to create multiple instances.  "
                "Valid options are: flavor=flavor_name_or_id, "
                "volume=disk_size_in_GB, volume_type=type, "
                "nic='net-id=net-uuid,v4-fixed-ip=ip-addr,port-id=port-uuid' "
                "(where net-id=network_id, v4-fixed-ip=IPv4r_fixed_address, "
                "port-id=port_id), availability_zone=AZ_hint_for_Nova.",
           action='append',
           dest='instances',
           default=[])
@utils.service_type('database')
def do_cluster_create(cs, args):
    """Creates a new cluster."""
    instances = []
    for instance_str in args.instances:
        instance_info = {}

        instance_info["flavorRef"] = _get_flavors(cs, instance_str)
        instance_info["volume"] = _get_volumes(instance_str)

        nics = _get_networks(instance_str)
        if nics:
            instance_info["nics"] = nics

        availability_zones = _get_availability_zones(instance_str)
        if availability_zones:
            instance_info["availability_zone"] = availability_zones

        instances.append(instance_info)

    if len(instances) == 0:
        raise exceptions.MissingArgs(['instance'])

    cluster = cs.clusters.create(args.name,
                                 args.datastore,
                                 args.datastore_version,
                                 instances=instances)
    cluster._info['task_name'] = cluster.task['name']
    cluster._info['task_description'] = cluster.task['description']
    del cluster._info['task']
    cluster._info['datastore'] = cluster.datastore['type']
    cluster._info['datastore_version'] = cluster.datastore['version']
    del cluster._info['instances']
    _print_object(cluster)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
@utils.arg('flavor',
           metavar='<flavor>',
           help='New flavor of the instance.')
@utils.service_type('database')
def do_resize_instance(cs, args):
    """Resizes an instance with a new flavor."""
    instance = _find_instance(cs, args.instance)
    flavor_id = _find_flavor(cs, args.flavor).id
    cs.instances.resize_instance(instance, flavor_id)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
@utils.arg('size',
           metavar='<size>',
           type=int,
           default=None,
           help='New size of the instance disk volume in GB.')
@utils.service_type('database')
def do_resize_volume(cs, args):
    """Resizes the volume size of an instance."""
    instance = _find_instance(cs, args.instance)
    cs.instances.resize_volume(instance, args.size)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
@utils.service_type('database')
def do_restart(cs, args):
    """Restarts an instance."""
    instance = _find_instance(cs, args.instance)
    cs.instances.restart(instance)

# Replication related commands


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
def do_detach_replica(cs, args):
    """Detaches a replica instance from its replication source."""
    instance = _find_instance(cs, args.instance)
    cs.instances.edit(instance, detach_replica_source=True)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
def do_promote_to_replica_source(cs, args):
    """Promotes a replica to be the new replica source of its set."""
    instance = _find_instance(cs, args.instance)
    cs.instances.promote_to_replica_source(instance)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
def do_eject_replica_source(cs, args):
    """Ejects a replica source from its set."""
    instance = _find_instance(cs, args.instance)
    cs.instances.eject_replica_source(instance)

# Backup related commands


@utils.arg('backup', metavar='<backup>', help='ID of the backup.')
@utils.service_type('database')
def do_backup_show(cs, args):
    """Shows details of a backup."""
    backup = _find_backup(cs, args.backup)
    _print_object(backup)


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('--limit', metavar='<limit>',
           default=None,
           help='Return up to N number of the most recent backups.')
@utils.arg('--marker', metavar='<ID>', type=str, default=None,
           help='Begin displaying the results for IDs greater than the '
                'specified marker. When used with --limit, set this to '
                'the last ID displayed in the previous run.')
@utils.service_type('database')
def do_backup_list_instance(cs, args):
    """Lists available backups for an instance."""
    instance = _find_instance(cs, args.instance)
    wrapper = cs.instances.backups(instance, limit=args.limit,
                                   marker=args.marker)
    backups = wrapper.items
    while wrapper.next and not args.limit:
        wrapper = cs.instances.backups(instance, marker=wrapper.next)
        backups += wrapper.items
    utils.print_list(backups, ['id', 'name', 'status',
                               'parent_id', 'updated'],
                     order_by='updated')


@utils.arg('--limit', metavar='<limit>',
           default=None,
           help='Return up to N number of the most recent backups.')
@utils.arg('--marker', metavar='<ID>', type=str, default=None,
           help='Begin displaying the results for IDs greater than the '
                'specified marker. When used with --limit, set this to '
                'the last ID displayed in the previous run.')
@utils.arg('--datastore', metavar='<datastore>',
           default=None,
           help='Name or ID of the datastore to list backups for.')
@utils.service_type('database')
def do_backup_list(cs, args):
    """Lists available backups."""
    wrapper = cs.backups.list(limit=args.limit, datastore=args.datastore,
                              marker=args.marker)
    backups = wrapper.items
    while wrapper.next and not args.limit:
        wrapper = cs.backups.list(marker=wrapper.next)
        backups += wrapper.items
    utils.print_list(backups, ['id', 'instance_id', 'name',
                               'status', 'parent_id', 'updated'],
                     order_by='updated')


@utils.arg('backup', metavar='<backup>', help='ID or name of the backup.')
@utils.service_type('database')
def do_backup_delete(cs, args):
    """Deletes a backup."""
    backup = _find_backup(cs, args.backup)
    cs.backups.delete(backup)


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of the backup.')
@utils.arg('--description', metavar='<description>',
           default=None,
           help='An optional description for the backup.')
@utils.arg('--parent', metavar='<parent>', default=None,
           help='Optional ID of the parent backup to perform an'
           ' incremental backup from.')
@utils.service_type('database')
def do_backup_create(cs, args):
    """Creates a backup of an instance."""
    instance = _find_instance(cs, args.instance)
    backup = cs.backups.create(args.name, instance,
                               description=args.description,
                               parent_id=args.parent)
    _print_object(backup)


@utils.arg('name', metavar='<name>', help='Name of the backup.')
@utils.arg('backup', metavar='<backup>',
           help='Backup ID of the source backup.',
           default=None)
@utils.arg('--region', metavar='<region>', help='Region where the source '
                                                'backup resides.',
           default=None)
@utils.arg('--description', metavar='<description>',
           default=None,
           help='An optional description for the backup.')
@utils.service_type('database')
def do_backup_copy(cs, args):
    """Creates a backup from another backup."""
    if args.backup:
        backup_ref = {"id": args.backup,
                      "region": args.region}
    else:
        backup_ref = None
    backup = cs.backups.create(args.name, instance=None,
                               description=args.description,
                               parent_id=None, backup=backup_ref,)
    _print_object(backup)


# Database related actions

@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of the database.')
@utils.arg('--character_set', metavar='<character_set>',
           default=None,
           help='Optional character set for database.')
@utils.arg('--collate', metavar='<collate>', default=None,
           help='Optional collation type for database.')
@utils.service_type('database')
def do_database_create(cs, args):
    """Creates a database on an instance."""
    instance = _find_instance(cs, args.instance)
    database_dict = {'name': args.name}
    if args.collate:
        database_dict['collate'] = args.collate
    if args.character_set:
        database_dict['character_set'] = args.character_set
    cs.databases.create(instance,
                        [database_dict])


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.service_type('database')
def do_database_list(cs, args):
    """Lists available databases on an instance."""
    instance = _find_instance(cs, args.instance)
    wrapper = cs.databases.list(instance)
    databases = wrapper.items
    while (wrapper.next):
        wrapper = cs.databases.list(instance, marker=wrapper.next)
        databases += wrapper.items

    utils.print_list(databases, ['name'])


@utils.arg('instance', metavar='<instance>',
           help='ID or name  of the instance.')
@utils.arg('database', metavar='<database>', help='Name of the database.')
@utils.service_type('database')
def do_database_delete(cs, args):
    """Deletes a database from an instance."""
    instance = _find_instance(cs, args.instance)
    cs.databases.delete(instance, args.database)


# User related actions

@utils.arg('instance', metavar='<instance>',
           help='ID or name  of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user.')
@utils.arg('password', metavar='<password>', help='Password of user.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user.')
@utils.arg('--databases', metavar='<databases>',
           help='Optional list of databases.',
           nargs="+", default=[])
@utils.service_type('database')
def do_user_create(cs, args):
    """Creates a user on an instance."""
    instance = _find_instance(cs, args.instance)
    databases = [{'name': value} for value in args.databases]
    user = {'name': args.name, 'password': args.password,
            'databases': databases}
    if args.host:
        user['host'] = args.host
    cs.users.create(instance, [user])


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.service_type('database')
def do_user_list(cs, args):
    """Lists the users for an instance."""
    instance = _find_instance(cs, args.instance)
    wrapper = cs.users.list(instance)
    users = wrapper.items
    while (wrapper.next):
        wrapper = cs.users.list(instance, marker=wrapper.next)
        users += wrapper.items
    for user in users:
        db_names = [db['name'] for db in user.databases]
        user.databases = ', '.join(db_names)
    utils.print_list(users, ['name', 'host', 'databases'])


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user.')
@utils.service_type('database')
def do_user_delete(cs, args):
    """Deletes a user from an instance."""
    instance = _find_instance(cs, args.instance)
    cs.users.delete(instance, args.name, hostname=args.host)


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user.')
@utils.service_type('database')
def do_user_show(cs, args):
    """Shows details of a user of an instance."""
    instance = _find_instance(cs, args.instance)
    user = cs.users.get(instance, args.name, hostname=args.host)
    _print_object(user)


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user.')
@utils.service_type('database')
def do_user_show_access(cs, args):
    """Shows access details of a user of an instance."""
    instance = _find_instance(cs, args.instance)
    access = cs.users.list_access(instance, args.name, hostname=args.host)
    utils.print_list(access, ['name'])


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user.')
@utils.arg('--new_name', metavar='<new_name>', default=None,
           help='Optional new name of user.')
@utils.arg('--new_password', metavar='<new_password>', default=None,
           help='Optional new password of user.')
@utils.arg('--new_host', metavar='<new_host>', default=None,
           help='Optional new host of user.')
@utils.service_type('database')
def do_user_update_attributes(cs, args):
    """Updates a user's attributes on an instance.
    At least one optional argument must be provided.
    """
    instance = _find_instance(cs, args.instance)
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
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user.')
@utils.arg('databases', metavar='<databases>',
           help='List of databases.',
           nargs="+", default=[])
@utils.service_type('database')
def do_user_grant_access(cs, args):
    """Grants access to a database(s) for a user."""
    instance = _find_instance(cs, args.instance)
    cs.users.grant(instance, args.name,
                   args.databases, hostname=args.host)


@utils.arg('instance', metavar='<instance>',
           help='ID or name of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user.')
@utils.arg('database', metavar='<database>', help='A single database.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user.')
@utils.service_type('database')
def do_user_revoke_access(cs, args):
    """Revokes access to a database for a user."""
    instance = _find_instance(cs, args.instance)
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
           help='ID or name of the instance or cluster.')
@utils.arg('--root_password',
           metavar='<root_password>',
           default=None,
           help='Root password to set.')
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
           help='ID or name of the instance.')
@utils.service_type('database')
def do_root_disable(cs, args):
    """Disables root for an instance."""
    instance = _find_instance(cs, args.instance)
    cs.root.disable_instance_root(instance)


@utils.arg('instance_or_cluster', metavar='<instance_or_cluster>',
           help='ID or name of the instance or cluster.')
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
    wrapper = cs.security_groups.list()
    sec_grps = wrapper.items
    while (wrapper.next):
        wrapper = cs.security_groups.list()
        sec_grps += wrapper.items

    utils.print_list(sec_grps, ['id', 'name', 'instance_id'])


@utils.arg('security_group', metavar='<security_group>',
           help='Security group ID.')
@utils.service_type('database')
def do_secgroup_show(cs, args):
    """Shows details of a security group."""
    sec_grp = cs.security_groups.get(args.security_group)
    del sec_grp._info['rules']
    _print_object(sec_grp)


@utils.arg('security_group', metavar='<security_group>',
           help='Security group ID.')
@utils.arg('cidr', metavar='<cidr>', help='CIDR address.')
@utils.service_type('database')
def do_secgroup_add_rule(cs, args):
    """Creates a security group rule."""
    rules = cs.security_group_rules.create(
        args.security_group, args.cidr)

    utils.print_list(rules, [
        'id', 'security_group_id', 'protocol',
        'from_port', 'to_port', 'cidr', 'created'], obj_is_dict=True)


@utils.arg('security_group', metavar='<security_group>',
           help='Security group ID.')
@utils.service_type('database')
def do_secgroup_list_rules(cs, args):
    """Lists all rules for a security group."""
    sec_grp = cs.security_groups.get(args.security_group)
    rules = sec_grp._info['rules']
    utils.print_list(
        rules, ['id', 'protocol', 'from_port', 'to_port', 'cidr'],
        obj_is_dict=True)


@utils.arg('security_group_rule', metavar='<security_group_rule>',
           help='Name of security group rule.')
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
           help='ID of the datastore.')
@utils.service_type('database')
def do_datastore_show(cs, args):
    """Shows details of a datastore."""
    datastore = cs.datastores.get(args.datastore)
    if hasattr(datastore, 'default_version'):
        datastore._info['default_version'] = getattr(datastore,
                                                     'default_version')
    _print_object(datastore)


@utils.arg('datastore', metavar='<datastore>',
           help='ID or name of the datastore.')
@utils.service_type('database')
def do_datastore_version_list(cs, args):
    """Lists available versions for a datastore."""
    datastore_versions = cs.datastore_versions.list(args.datastore)
    utils.print_list(datastore_versions, ['id', 'name'])


@utils.arg('--datastore', metavar='<datastore>',
           default=None,
           help='ID or name of the datastore. Optional if the ID of the'
                ' datastore_version is provided.')
@utils.arg('datastore_version', metavar='<datastore_version>',
           help='ID or name of the datastore version.')
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
        raise exceptions.NoUniqueMatch('The datastore name or id is required'
                                       ' to retrieve a datastore version'
                                       ' by name.')
    _print_object(datastore_version)


# configuration group related functions

@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
@utils.arg('configuration',
           metavar='<configuration>',
           type=str,
           help='ID of the configuration group to attach to the instance.')
@utils.service_type('database')
def do_configuration_attach(cs, args):
    """Attaches a configuration group to an instance."""
    instance = _find_instance(cs, args.instance)
    cs.instances.modify(instance, args.configuration)


@utils.arg('name', metavar='<name>', help='Name of the configuration group.')
@utils.arg('values', metavar='<values>',
           help='Dictionary of the values to set.')
@utils.arg('--datastore', metavar='<datastore>',
           help='Datastore assigned to the configuration group. Required if '
                'default datastore is not configured.')
@utils.arg('--datastore_version', metavar='<datastore_version>',
           help='Datastore version ID assigned to the configuration group.')
@utils.arg('--description', metavar='<description>',
           default=None,
           help='An optional description for the configuration group.')
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
           help='ID or name of the instance.')
@utils.service_type('database')
def do_configuration_default(cs, args):
    """Shows the default configuration of an instance."""
    instance = _find_instance(cs, args.instance)
    configs = cs.instances.configuration(instance)
    utils.print_dict(configs._info['configuration'])


@utils.arg('configuration_group', metavar='<configuration_group>',
           help='ID of the configuration group.')
@utils.service_type('database')
def do_configuration_delete(cs, args):
    """Deletes a configuration group."""
    cs.configurations.delete(args.configuration_group)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='ID or name of the instance.')
@utils.service_type('database')
def do_configuration_detach(cs, args):
    """Detaches a configuration group from an instance."""
    instance = _find_instance(cs, args.instance)
    cs.instances.modify(instance)


@utils.arg('--datastore', metavar='<datastore>',
           default=None,
           help='ID or name of the datastore to list configuration '
                'parameters for. Optional if the ID of the'
                ' datastore_version is provided.')
@utils.arg('datastore_version',
           metavar='<datastore_version>',
           help='Datastore version name or ID assigned to the '
                'configuration group.')
@utils.arg('parameter', metavar='<parameter>',
           help='Name of the configuration parameter.')
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
    _print_object(param)


@utils.arg('--datastore', metavar='<datastore>',
           default=None,
           help='ID or name of the datastore to list configuration '
                'parameters for. Optional if the ID of the'
                ' datastore_version is provided.')
@utils.arg('datastore_version',
           metavar='<datastore_version>',
           help='Datastore version name or ID assigned to the '
                'configuration group.')
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
        raise exceptions.NoUniqueMatch('The datastore name or id is required'
                                       ' to retrieve the parameters for the'
                                       ' configuration group by name.')
    utils.print_list(params, ['name', 'type', 'min_size', 'max_size',
                              'restart_required'])


@utils.arg('configuration_group', metavar='<configuration_group>',
           help='ID of the configuration group.')
@utils.arg('values', metavar='<values>',
           help='Dictionary of the values to set.')
@utils.service_type('database')
def do_configuration_patch(cs, args):
    """Patches a configuration group."""
    cs.configurations.edit(args.configuration_group,
                           args.values)


@utils.arg('configuration_group', metavar='<configuration_group>',
           help='ID of the configuration group.')
@utils.service_type('database')
def do_configuration_instances(cs, args):
    """Lists all instances associated with a configuration group."""
    params = cs.configurations.instances(args.configuration_group)
    utils.print_list(params, ['id', 'name'])


@utils.service_type('database')
def do_configuration_list(cs, args):
    """Lists all configuration groups."""
    config_grps = cs.configurations.list()
    utils.print_list(config_grps, [
        'id', 'name', 'description',
        'datastore_name', 'datastore_version_name'])


@utils.arg('configuration_group', metavar='<configuration_group>',
           help='ID of the configuration group.')
@utils.service_type('database')
def do_configuration_show(cs, args):
    """Shows details of a configuration group."""
    config_grp = cs.configurations.get(args.configuration_group)
    config_grp._info['values'] = json.dumps(config_grp.values)

    del config_grp._info['datastore_version_id']
    _print_object(config_grp)


@utils.arg('configuration_group', metavar='<configuration_group>',
           help='ID of the configuration group.')
@utils.arg('values', metavar='<values>',
           help='Dictionary of the values to set.')
@utils.arg('--name', metavar='<name>', default=None,
           help='Name of the configuration group.')
@utils.arg('--description', metavar='<description>',
           default=None,
           help='An optional description for the configuration group.')
@utils.service_type('database')
def do_configuration_update(cs, args):
    """Updates a configuration group."""
    cs.configurations.update(args.configuration_group,
                             args.values,
                             args.name,
                             args.description)


@utils.arg('instance_id', metavar='<instance_id>', help='UUID for instance.')
@utils.service_type('database')
def do_metadata_list(cs, args):
    """Shows all metadata for instance <id>."""
    result = cs.metadata.list(args.instance_id)
    _print_object(result)


@utils.arg('instance_id', metavar='<instance_id>', help='UUID for instance.')
@utils.arg('key', metavar='<key>', help='Key to display.')
@utils.service_type('database')
def do_metadata_show(cs, args):
    """Shows metadata entry for key <key> and instance <id>."""
    result = cs.metadata.show(args.instance_id, args.key)
    _print_object(result)


@utils.arg('instance_id', metavar='<instance_id>', help='UUID for instance.')
@utils.arg('key', metavar='<key>', help='Key to replace.')
@utils.arg('value', metavar='<value>',
           help='New value to assign to <key>.')
@utils.service_type('database')
def do_metadata_edit(cs, args):
    """Replaces metadata value with a new one, this is non-destructive."""
    cs.metadata.edit(args.instance_id, args.key, args.value)


@utils.arg('instance_id', metavar='<instance_id>', help='UUID for instance.')
@utils.arg('key', metavar='<key>', help='Key to update.')
@utils.arg('newkey', metavar='<newkey>', help='New key.')
@utils.arg('value', metavar='<value>', help='Value to assign to <newkey>.')
@utils.service_type('database')
def do_metadata_update(cs, args):
    """Updates metadata, this is destructive."""
    cs.metadata.update(args.instance_id, args.key, args.newkey, args.value)


@utils.arg('instance_id', metavar='<instance_id>', help='UUID for instance.')
@utils.arg('key', metavar='<key>', help='Key for assignment.')
@utils.arg('value', metavar='<value>', help='Value to assign to <key>.')
@utils.service_type('database')
def do_metadata_create(cs, args):
    """Creates metadata in the database for instance <id>."""
    result = cs.metadata.create(args.instance_id, args.key, args.value)
    _print_object(result)


@utils.arg('instance_id', metavar='<instance_id>', help='UUID for instance.')
@utils.arg('key', metavar='<key>', help='Metadata key to delete.')
@utils.service_type('database')
def do_metadata_delete(cs, args):
    """Deletes metadata for instance <id>."""
    cs.metadata.delete(args.instance_id, args.key)


@utils.arg('--datastore', metavar='<datastore>',
           help='Name or ID of datastore to list modules for.')
@utils.service_type('database')
def do_module_list(cs, args):
    """Lists the modules available."""
    datastore = None
    if args.datastore:
        datastore = _find_datastore(cs, args.datastore)
    module_list = cs.modules.list(datastore=datastore)
    utils.print_list(
        module_list,
        ['id', 'tenant', 'name', 'type', 'datastore',
         'datastore_version', 'auto_apply', 'visible'],
        labels={'datastore_version': 'Version'})


@utils.arg('module', metavar='<module>',
           help='ID or name of the module.')
@utils.service_type('database')
def do_module_show(cs, args):
    """Shows details of a module."""
    module = _find_module(cs, args.module)
    _print_object(module)


@utils.arg('name', metavar='<name>', type=str, help='Name of the module.')
@utils.arg('type', metavar='<type>', type=str,
           help='Type of the module. The type must be supported by a '
                'corresponding module plugin on the datastore it is '
                'applied to.')
@utils.arg('file', metavar='<filename>', type=argparse.FileType('rb', 0),
           help='File containing data contents for the module.')
@utils.arg('--description', metavar='<description>', type=str,
           help='Description of the module.')
@utils.arg('--datastore', metavar='<datastore>',
           help='Name or ID of datastore this module can be applied to. '
                'If not specified, module can be applied to all datastores.')
@utils.arg('--datastore_version', metavar='<version>',
           help='Name or ID of datastore version this module can be applied '
                'to. If not specified, module can be applied to all versions.')
@utils.arg('--auto_apply', action='store_true', default=False,
           help='Automatically apply this module when creating an instance '
                'or cluster.')
@utils.arg('--all_tenants', action='store_true', default=False,
           help='Module is valid for all tenants (Admin only).')
# This option is to suppress the module from module-list for non-admin
@utils.arg('--hidden', action='store_true', default=False,
           help=argparse.SUPPRESS)
@utils.arg('--live_update', action='store_true', default=False,
           help='Allow module to be updated even if it is already applied '
                'to a current instance or cluster. Automatically attempt to '
                'reapply this module if the contents change.')
@utils.service_type('database')
def do_module_create(cs, args):
    """Create a module."""

    contents = args.file.read()
    if not contents:
        raise exceptions.ValidationError(
            "The file '%s' must contain some data" % args.file)

    module = cs.modules.create(
        args.name, args.type, contents, description=args.description,
        all_tenants=args.all_tenants, datastore=args.datastore,
        datastore_version=args.datastore_version,
        auto_apply=args.auto_apply, visible=not args.hidden,
        live_update=args.live_update)
    _print_object(module)


@utils.arg('module', metavar='<module>', type=str,
           help='Name or ID of the module.')
@utils.arg('--name', metavar='<name>', type=str, default=None,
           help='Name of the module.')
@utils.arg('--type', metavar='<type>', type=str, default=None,
           help='Type of the module. The type must be supported by a '
                'corresponding module plugin on the datastore it is '
                'applied to.')
@utils.arg('--file', metavar='<filename>', type=argparse.FileType('rb', 0),
           default=None,
           help='File containing data contents for the module.')
@utils.arg('--description', metavar='<description>', type=str, default=None,
           help='Description of the module.')
@utils.arg('--datastore', metavar='<datastore>',
           help='Name or ID of datastore this module can be applied to. '
                'If not specified, module can be applied to all datastores.')
@utils.arg('--all_datastores', dest='datastore', action='store_const',
           const=None,
           help='Module is valid for all datastores.')
@utils.arg('--datastore_version', metavar='<version>',
           help='Name or ID of datastore version this module can be applied '
                'to. If not specified, module can be applied to all versions.')
@utils.arg('--all_datastore_versions', dest='datastore_version',
           action='store_const', const=None,
           help='Module is valid for all datastore version.')
@utils.arg('--auto_apply', action='store_true', default=None,
           help='Automatically apply this module when creating an instance '
                'or cluster.')
@utils.arg('--no_auto_apply', dest='auto_apply', action='store_false',
           default=None,
           help='Do not automatically apply this module when creating an '
                'instance or cluster.')
@utils.arg('--all_tenants', action='store_true', default=None,
           help='Module is valid for all tenants (Admin only).')
@utils.arg('--no_all_tenants', dest='all_tenants', action='store_false',
           default=None,
           help='Module is valid for current tenant only (Admin only).')
# This option is to suppress the module from module-list for non-admin
@utils.arg('--hidden', action='store_true', default=None,
           help=argparse.SUPPRESS)
# This option is to allow the module to be seen from module-list for non-admin
@utils.arg('--no_hidden', dest='hidden', action='store_false', default=None,
           help=argparse.SUPPRESS)
@utils.arg('--live_update', action='store_true', default=None,
           help='Allow module to be updated or deleted even if it is already '
                'applied to a current instance or cluster. Automatically '
                'attempt to reapply this module if the contents change.')
@utils.arg('--no_live_update', dest='live_update', action='store_false',
           default=None,
           help='Restricts a module from being updated or deleted if it is '
                'already applied to a current instance or cluster.')
@utils.service_type('database')
def do_module_update(cs, args):
    """Create a module."""
    module = _find_module(cs, args.module)
    contents = args.file.read() if args.file else None
    visible = not args.hidden if args.hidden is not None else None
    datastore_args = {}
    if args.datastore:
        datastore_args['datastore'] = args.datastore
    if args.datastore_version:
        datastore_args['datastore_version'] = args.datastore_version
    updated_module = cs.modules.update(
        module, name=args.name, module_type=args.type, contents=contents,
        description=args.description, all_tenants=args.all_tenants,
        auto_apply=args.auto_apply, visible=visible,
        live_update=args.live_update, **datastore_args)
    _print_object(updated_module)


@utils.arg('module', metavar='<module>',
           help='ID or name of the module.')
@utils.service_type('database')
def do_module_delete(cs, args):
    """Delete a module."""
    module = _find_module(cs, args.module)
    cs.modules.delete(module)


@utils.arg('instance', metavar='<instance>',
           help='Id or Name of the instance.')
@utils.service_type('database')
def do_log_list(cs, args):
    """Lists the log files available for instance."""
    instance = _find_instance(cs, args.instance)
    log_list = cs.instances.log_list(instance)
    utils.print_list(log_list,
                     ['name', 'type', 'status', 'published', 'pending',
                      'container', 'prefix'])


@utils.arg('instance', metavar='<instance>',
           help='Id or Name of the instance.')
@utils.arg('log_name', metavar='<log_name>', help='Name of log to show.')
@utils.service_type('database')
def do_log_show(cs, args):
    """Instructs Trove guest to show details of log."""
    try:
        instance = _find_instance(cs, args.instance)
        log_info = cs.instances.log_show(instance, args.log_name)
        _print_object(log_info)
    except exceptions.GuestLogNotFoundError:
        print(NO_LOG_FOUND_ERROR % (args.log_name, instance))
    except Exception as ex:
        error_msg = ex.message.split('\n')
        print(error_msg[0])


@utils.arg('instance', metavar='<instance>',
           help='Id or Name of the instance.')
@utils.arg('log_name', metavar='<log_name>', help='Name of log to publish.')
@utils.service_type('database')
def do_log_enable(cs, args):
    """Instructs Trove guest to start collecting log details."""
    try:
        instance = _find_instance(cs, args.instance)
        log_info = cs.instances.log_enable(instance, args.log_name)
        _print_object(log_info)
    except exceptions.GuestLogNotFoundError:
        print(NO_LOG_FOUND_ERROR % (args.log_name, instance))
    except Exception as ex:
        error_msg = ex.message.split('\n')
        print(error_msg[0])


@utils.arg('instance', metavar='<instance>',
           help='Id or Name of the instance.')
@utils.arg('log_name', metavar='<log_name>', help='Name of log to publish.')
@utils.arg('--discard', action='store_true', default=False,
           help='Discard published contents of specified log.')
@utils.service_type('database')
def do_log_disable(cs, args):
    """Instructs Trove guest to stop collecting log details."""
    try:
        instance = _find_instance(cs, args.instance)
        log_info = cs.instances.log_disable(instance, args.log_name,
                                            discard=args.discard)
        _print_object(log_info)
    except exceptions.GuestLogNotFoundError:
        print(NO_LOG_FOUND_ERROR % (args.log_name, instance))
    except Exception as ex:
        error_msg = ex.message.split('\n')
        print(error_msg[0])


@utils.arg('instance', metavar='<instance>',
           help='Id or Name of the instance.')
@utils.arg('log_name', metavar='<log_name>', help='Name of log to publish.')
@utils.arg('--disable', action='store_true', default=False,
           help='Stop collection of specified log.')
@utils.arg('--discard', action='store_true', default=False,
           help='Discard published contents of specified log.')
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
        print(NO_LOG_FOUND_ERROR % (args.log_name, instance))
    except Exception as ex:
        error_msg = ex.message.split('\n')
        print(error_msg[0])


@utils.arg('instance', metavar='<instance>',
           help='Id or Name of the instance.')
@utils.arg('log_name', metavar='<log_name>', help='Name of log to publish.')
@utils.service_type('database')
def do_log_discard(cs, args):
    """Instructs Trove guest to discard the container of the published log."""
    try:
        instance = _find_instance(cs, args.instance)
        log_info = cs.instances.log_discard(instance, args.log_name)
        _print_object(log_info)
    except exceptions.GuestLogNotFoundError:
        print(NO_LOG_FOUND_ERROR % (args.log_name, instance))
    except Exception as ex:
        error_msg = ex.message.split('\n')
        print(error_msg[0])


@utils.arg('instance', metavar='<instance>',
           help='Id or Name of the instance.')
@utils.arg('log_name', metavar='<log_name>', help='Name of log to publish.')
@utils.arg('--publish', action='store_true', default=False,
           help='Publish latest entries from guest before display.')
@utils.arg('--lines', metavar='<lines>', default=50, type=int,
           help='Publish latest entries from guest before display.')
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
        print(NO_LOG_FOUND_ERROR % (args.log_name, instance))
    except Exception as ex:
        error_msg = ex.message.split('\n')
        print(error_msg[0])


@utils.arg('instance', metavar='<instance>',
           help='Id or Name of the instance.')
@utils.arg('log_name', metavar='<log_name>', help='Name of log to publish.')
@utils.arg('--publish', action='store_true', default=False,
           help='Publish latest entries from guest before display.')
@utils.arg('--file', metavar='<file>', default=None,
           help='Path of file to save log to for instance.')
@utils.service_type('database')
def do_log_save(cs, args):
    """Save log file for instance."""
    try:
        instance = _find_instance(cs, args.instance)
        filename = cs.instances.log_save(instance, args.log_name,
                                         args.publish, args.file)
        print('Log "%s" written to %s' % (args.log_name, filename))
    except exceptions.GuestLogNotFoundError:
        print(NO_LOG_FOUND_ERROR % (args.log_name, instance))
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
