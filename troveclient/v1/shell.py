# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import sys
import time

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
    # Get rid of those ugly links
    if instance._info.get('links'):
        del(instance._info['links'])
    utils.print_dict(instance._info)


def _find_instance(cs, instance):
    """Get a instance by ID."""
    return utils.find_resource(cs.instances, instance)


def _find_flavor(cs, flavor):
    """Get a flavor by ID."""
    return utils.find_resource(cs.flavors, flavor)


def _find_backup(cs, backup):
    """Gets a backup by ID."""
    return utils.find_resource(cs.backups, backup)


# Flavor related calls

@utils.service_type('database')
def do_flavor_list(cs, args):
    """Lists available flavors."""
    flavors = cs.flavors.list()
    utils.print_list(flavors, ['id', 'name', 'ram'])


@utils.arg('flavor', metavar='<flavor>', help='ID of the flavor.')
@utils.service_type('database')
def do_flavor_show(cs, args):
    """Show details of a flavor."""
    flavor = _find_flavor(cs, args.flavor)
    _print_instance(flavor)


# Instance related calls

@utils.service_type('database')
def do_list(cs, args):
    """List all the instances."""
    instances = cs.instances.list()

    for instance in instances:
        setattr(instance, 'flavor_id', instance.flavor['id'])
        if hasattr(instance, 'volume'):
            setattr(instance, 'size', instance.volume['size'])
        if hasattr(instance, 'datastore'):
            setattr(instance, 'datastore', instance.datastore['type'])
    utils.print_list(instances, ['id', 'name', 'datastore', 'status',
                                 'flavor_id', 'size'])


@utils.arg('instance', metavar='<instance>', help='ID of the instance.')
@utils.service_type('database')
def do_show(cs, args):
    """Show details of an instance."""
    instance = _find_instance(cs, args.instance)
    instance._info['flavor'] = instance.flavor['id']
    if hasattr(instance, 'volume'):
        instance._info['volume'] = instance.volume['size']
        if 'used' in instance.volume:
            instance._info['volume_used'] = instance.volume['used']
    if hasattr(instance, 'ip'):
        instance._info['ip'] = ', '.join(instance.ip)
    if hasattr(instance, 'datastore'):
        instance._info['datastore'] = instance.datastore['type']
        instance._info['datastore_version'] = instance.datastore['version']
    _print_instance(instance)


@utils.arg('instance', metavar='<instance>', help='ID of the instance.')
@utils.service_type('database')
def do_delete(cs, args):
    """Deletes an instance."""
    cs.instances.delete(args.instance)


@utils.arg('name',
           metavar='<name>',
           type=str,
           help='Name of the instance')
@utils.arg('--size',
           metavar='<size>',
           type=int,
           default=None,
           help='Size of the instance disk in GB')
@utils.arg('flavor_id',
           metavar='<flavor_id>',
           help='Flavor of the instance')
@utils.arg('--databases', metavar='<databases>',
           help='Optional list of databases.',
           nargs="+", default=[])
@utils.arg('--users', metavar='<users>',
           help='Optional list of users in the form user:password.',
           nargs="+", default=[])
@utils.arg('--backup',
           metavar='<backup>',
           default=None,
           help='A backup UUID')
@utils.arg('--availability_zone',
           metavar='<availability_zone>',
           default=None,
           help='The Zone hint to give to nova')
@utils.arg('--datastore',
           metavar='<datastore>',
           default=None,
           help='A datastore name or UUID')
@utils.arg('--datastore_version',
           metavar='<datastore_version>',
           default=None,
           help='A datastore version name or UUID')
@utils.service_type('database')
def do_create(cs, args):
    """Creates a new instance."""
    volume = None
    if args.size:
        volume = {"size": args.size}
    restore_point = None
    if args.backup:
        restore_point = {"backupRef": args.backup}
    databases = [{'name': value} for value in args.databases]
    users = [{'name': n, 'password': p} for (n, p) in
             [z.split(':')[:2] for z in args.users]]
    instance = cs.instances.create(args.name,
                                   args.flavor_id,
                                   volume=volume,
                                   databases=databases,
                                   users=users,
                                   restorePoint=restore_point,
                                   availability_zone=args.availability_zone,
                                   datastore=args.datastore,
                                   datastore_version=args.datastore_version)
    instance._info['flavor'] = instance.flavor['id']
    if hasattr(instance, 'volume'):
        instance._info['volume'] = instance.volume['size']
    if hasattr(instance, 'datastore'):
        instance._info['datastore'] = instance.datastore['type']
        instance._info['datastore_version'] = instance.datastore['version']
    del(instance._info['links'])

    _print_instance(instance)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='UUID of the instance')
@utils.arg('flavor_id',
           metavar='<flavor_id>',
           help='Flavor of the instance')
@utils.service_type('database')
def do_resize_flavor(cs, args):
    """Resizes the flavor of an instance."""
    cs.instances.resize_flavor(args.instance, args.flavor_id)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='UUID of the instance')
@utils.arg('size',
           metavar='<size>',
           type=int,
           default=None,
           help='Size of the instance disk in GB')
@utils.service_type('database')
def do_resize_volume(cs, args):
    """Resizes the volume size of an instance."""
    cs.instances.resize_volume(args.instance, args.size)


@utils.arg('instance',
           metavar='<instance>',
           type=str,
           help='UUID of the instance')
@utils.service_type('database')
def do_restart(cs, args):
    """Restarts the instance."""
    cs.instances.restart(args.instance)


# Backup related commands

@utils.arg('backup', metavar='<backup>', help='ID of the backup.')
@utils.service_type('database')
def do_backup_show(cs, args):
    """Show details of a backup."""
    backup = _find_backup(cs, args.backup)
    _print_instance(backup)


@utils.arg('--limit', metavar='<limit>',
           default=None,
           help='Return up to N number of the most recent backups.')
@utils.arg('instance', metavar='<instance>', help='ID of the instance.')
@utils.service_type('database')
def do_backup_list_instance(cs, args):
    """List available backups for an instance."""
    wrapper = cs.instances.backups(args.instance, limit=args.limit)
    backups = wrapper.items
    while wrapper.next and not args.limit:
        wrapper = cs.instances.backups(args.instance, marker=wrapper.next)
        backups += wrapper.items
    utils.print_list(backups, ['id', 'name', 'status',
                               'parent_id', 'updated'],
                     order_by='updated')


@utils.arg('--limit', metavar='<limit>',
           default=None,
           help='Return up to N number of the most recent backups.')
@utils.service_type('database')
def do_backup_list(cs, args):
    """List available backups."""
    wrapper = cs.backups.list(limit=args.limit)
    backups = wrapper.items
    while wrapper.next and not args.limit:
        wrapper = cs.backups.list(marker=wrapper.next)
        backups += wrapper.items
    utils.print_list(backups, ['id', 'instance_id', 'name',
                               'status', 'parent_id', 'updated'],
                     order_by='updated')


@utils.arg('backup', metavar='<backup>', help='ID of the backup.')
@utils.service_type('database')
def do_backup_delete(cs, args):
    """Deletes a backup."""
    cs.backups.delete(args.backup)


@utils.arg('name', metavar='<name>', help='Name of the backup.')
@utils.arg('instance', metavar='<instance>', help='UUID of the instance.')
@utils.arg('--description', metavar='<description>',
           default=None,
           help='An optional description for the backup.')
@utils.arg('--parent', metavar='<parent>', default=None,
           help='Optional UUID of the parent backup to preform an'
           ' incremental backup from.')
@utils.service_type('database')
def do_backup_create(cs, args):
    """Creates a backup."""
    backup = cs.backups.create(args.name, args.instance,
                               description=args.description,
                               parent_id=args.parent)
    _print_instance(backup)


# Database related actions

@utils.arg('instance', metavar='<instance>', help='UUID of the instance.')
@utils.arg('name', metavar='<name>', help='Name of the database.')
@utils.arg('--character_set', metavar='<character_set>',
           default=None,
           help='Optional character set for database')
@utils.arg('--collate', metavar='<collate>', default=None,
           help='Optional collation type for database')
@utils.service_type('database')
def do_database_create(cs, args):
    """Creates a database on an instance."""
    database_dict = {'name': args.name}
    if args.collate:
        database_dict['collate'] = args.collate
    if args.character_set:
        database_dict['character_set'] = args.character_set
    cs.databases.create(args.instance,
                        [database_dict])


@utils.arg('instance', metavar='<instance>', help='UUID of the instance.')
@utils.service_type('database')
def do_database_list(cs, args):
    """Lists available databases on an instance."""
    wrapper = cs.databases.list(args.instance)
    databases = wrapper.items
    while (wrapper.next):
        wrapper = cs.databases.list(args.instance, marker=wrapper.next)
        databases = wrapper.items

    utils.print_list(databases, ['name'])


@utils.arg('instance', metavar='<instance>', help='UUID of the instance.')
@utils.arg('database', metavar='<database>', help='Name of the database.')
@utils.service_type('database')
def do_database_delete(cs, args):
    """Deletes a database."""
    cs.databases.delete(args.instance, args.database)


# User related actions

@utils.arg('instance', metavar='<instance>', help='UUID of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user')
@utils.arg('password', metavar='<password>', help='Password of user')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user')
@utils.arg('--databases', metavar='<databases>',
           help='Optional list of databases.',
           nargs="+", default=[])
@utils.service_type('database')
def do_user_create(cs, args):
    """Creates a user."""
    databases = [{'name': value} for value in args.databases]
    user = {'name': args.name, 'password': args.password,
            'databases': databases}
    if args.host:
        user['host'] = args.host
    cs.users.create(args.instance, [user])


@utils.arg('instance', metavar='<instance>', help='UUID of the instance.')
@utils.service_type('database')
def do_user_list(cs, args):
    """Lists the users for a instance."""
    wrapper = cs.users.list(args.instance)
    users = wrapper.items
    while (wrapper.next):
        wrapper = cs.users.list(args.instance, marker=wrapper.next)
        users += wrapper.items
    for user in users:
        db_names = [db['name'] for db in user.databases]
        user.databases = ', '.join(db_names)
    utils.print_list(users, ['name', 'host', 'databases'])


@utils.arg('instance', metavar='<instance>', help='UUID of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user')
@utils.service_type('database')
def do_user_delete(cs, args):
    """Deletes a user from the instance."""
    cs.users.delete(args.instance, args.name, hostname=args.host)


@utils.arg('instance', metavar='<instance>', help='UUID of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user')
@utils.service_type('database')
# Quoting is not working now that we aren't using httplib2
# anymore and instead are using requests
def do_user_show(cs, args):
    """Gets a user from the instance."""
    user = cs.users.get(args.instance, args.name, hostname=args.host)
    _print_instance(user)


@utils.arg('instance', metavar='<instance>', help='UUID of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user')
@utils.service_type('database')
# Quoting is not working now that we aren't using httplib2
# anymore and instead are using requests
def do_user_show_access(cs, args):
    """Gets a users access from the instance."""
    access = cs.users.list_access(args.instance, args.name, hostname=args.host)
    utils.print_list(access, ['name'])


@utils.arg('instance', metavar='<instance>', help='UUID of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user')
@utils.arg('--new_name', metavar='<new_name>', default=None,
           help='Optional new name of user')
@utils.arg('--new_password', metavar='<new_password>', default=None,
           help='Optional new password of user')
@utils.arg('--new_host', metavar='<new_host>', default=None,
           help='Optional new host of user')
@utils.service_type('database')
# Quoting is not working now that we aren't using httplib2
# anymore and instead are using requests
def do_user_update_attributes(cs, args):
    """Updates a users attributes from the instance."""
    new_attrs = {}
    if args.new_name:
        new_attrs['name'] = args.new_name
    if args.new_password:
        new_attrs['password'] = args.new_password
    if args.new_host:
        new_attrs['host'] = args.new_host
    cs.users.update_attributes(args.instance, args.name,
                               newuserattr=new_attrs, hostname=args.host)


@utils.arg('instance', metavar='<instance>', help='UUID of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user')
@utils.arg('databases', metavar='<databases>',
           help='List of databases.',
           nargs="+", default=[])
@utils.service_type('database')
def do_user_grant_access(cs, args):
    """Grants access to a database(s) for a user."""
    cs.users.grant(args.instance, args.name,
                   args.databases, hostname=args.host)


@utils.arg('instance', metavar='<instance>', help='UUID of the instance.')
@utils.arg('name', metavar='<name>', help='Name of user')
@utils.arg('database', metavar='<database>', help='A single database.')
@utils.arg('--host', metavar='<host>', default=None,
           help='Optional host of user')
@utils.service_type('database')
def do_user_revoke_access(cs, args):
    """Revokes access to a database for a  user."""
    cs.users.revoke(args.instance, args.name,
                    args.database, hostname=args.host)


# Limits related commands

@utils.service_type('database')
def do_limit_list(cs, args):
    """Lists the limits for a tenant."""
    limits = cs.limits.list()
    # Pop the first one, its absolute limits
    absolute = limits.pop(0)
    _print_instance(absolute)
    utils.print_list(limits, ['value', 'verb', 'remaining', 'unit'])


# Root related commands

@utils.arg('instance', metavar='<instance>', help='UUID of the instance.')
@utils.service_type('database')
def do_root_enable(cs, args):
    """Enables root for a instance."""
    root = cs.root.create(args.instance)
    utils.print_dict({'name': root[0], 'password': root[1]})


@utils.arg('instance', metavar='<instance>', help='UUID of the instance.')
@utils.service_type('database')
def do_root_show(cs, args):
    """Gets root enabled status for a instance."""
    root = cs.root.is_root_enabled(args.instance)
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

    utils.print_list(sec_grps, ['id', 'name', 'rules', 'instance_id'])


@utils.arg('security_group', metavar='<security_group>',
           help='ID of the security group.')
@utils.service_type('database')
def do_secgroup_show(cs, args):
    """Shows details about a security group."""
    sec_grp = cs.security_groups.get(args.security_group)
    _print_instance(sec_grp)


@utils.arg('security_group', metavar='<security_group>',
           help='Security group name')
@utils.arg('protocol', metavar='<protocol>', help='Protocol')
@utils.arg('from_port', metavar='<from_port>', help='from port')
@utils.arg('to_port', metavar='<to_port>', help='to port')
@utils.arg('cidr', metavar='<cidr>', help='CIDR address')
@utils.service_type('database')
def do_secgroup_add_rule(cs, args):
    """Creates a security group rule."""
    rule = cs.security_group_rules.create(args.security_group,
                                          args.protocol,
                                          args.from_port,
                                          args.to_port,
                                          args.cidr)

    _print_instance(rule)


@utils.arg('security_group_rule', metavar='<security_group_rule>',
           help='Security group rule')
@utils.service_type('database')
def do_secgroup_delete_rule(cs, args):
    """Deletes a security group rule."""
    cs.security_group_rules.delete(args.security_group_rule)


@utils.service_type('database')
def do_datastore_list(cs, args):
    """List available datastores."""
    datastores = cs.datastores.list()
    utils.print_list(datastores, ['id', 'name'])


@utils.arg('datastore', metavar='<datastore>',
           help='ID of the datastore.')
@utils.service_type('database')
def do_datastore_show(cs, args):
    """Show details of a datastore."""
    datastore = cs.datastores.get(args.datastore)
    if hasattr(datastore, 'default_version'):
        datastore._info['default_version'] = getattr(datastore,
                                                     'default_version')
    _print_instance(datastore)


@utils.arg('datastore', metavar='<datastore>',
           help='ID of the datastore.')
@utils.service_type('database')
def do_datastore_version_list(cs, args):
    """List available versions for a datastore."""
    datastore_versions = cs.datastore_versions.list(args.datastore)
    utils.print_list(datastore_versions, ['id', 'name'])


@utils.arg('--datastore', metavar='<datastore>',
           default=None,
           help='ID or name of the datastore. Optional if UUID of the'
                ' datastore_version is provided.')
@utils.arg('datastore_version', metavar='<datastore_version>',
           help='ID of the datastore version.')
@utils.service_type('database')
def do_datastore_version_show(cs, args):
    """Show details of a datastore version."""
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
    _print_instance(datastore_version)
