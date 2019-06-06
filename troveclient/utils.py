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

import base64
import os
import simplejson as json
import sys
import uuid

from oslo_utils import encodeutils
import prettytable
import six

from troveclient.apiclient import exceptions


def arg(*args, **kwargs):
    """Decorator for CLI args."""
    def _decorator(func):
        add_arg(func, *args, **kwargs)
        return func
    return _decorator


def env(*vars, **kwargs):
    """Returns environment variables.

    Returns the first environment variable set
    if none are non-empty, defaults to '' or keyword arg default
    """
    for v in vars:
        value = os.environ.get(v, None)
        if value:
            return value
    return kwargs.get('default', '')


def add_arg(f, *args, **kwargs):
    """Bind CLI arguments to a shell.py `do_foo` function."""

    if not hasattr(f, 'arguments'):
        f.arguments = []

    # NOTE(sirp): avoid dups that can occur when the module is shared across
    # tests.
    if (args, kwargs) not in f.arguments:
        # Because of the semantics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        f.arguments.insert(0, (args, kwargs))


def unauthenticated(f):
    """Adds 'unauthenticated' attribute to decorated function.

    Usage::

        @unauthenticated
        def mymethod(f):
            ...

    """
    f.unauthenticated = True
    return f


def isunauthenticated(f):
    """Decorator to mark authentication-non-required.

    Checks to see if the function is marked as not requiring authentication
    with the @unauthenticated decorator. Returns True if decorator is
    set to True, False otherwise.
    """
    return getattr(f, 'unauthenticated', False)


def service_type(stype):
    """Adds 'service_type' attribute to decorated function.

    Usage::

        @service_type('database')
        def mymethod(f):
            ...

    """
    def inner(f):
        f.service_type = stype
        return f
    return inner


def get_service_type(f):
    """Retrieves service type from function."""
    return getattr(f, 'service_type', None)


def translate_keys(collection, convert):
    for item in collection:
        keys = list(item.__dict__.keys())
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


def _output_override(objs, print_as):
    """Output override flag checking.

    If an output override global flag is set, print with override
    raise BaseException if no printing was overridden.
    """
    if globals().get('json_output', False):
        if print_as == 'list':
            new_objs = []
            for o in objs:
                new_objs.append(o._info)
        elif print_as == 'dict':
            new_objs = objs
        # pretty print the json
        print(json.dumps(new_objs, indent='  '))
    else:
        raise BaseException('No valid output override')


def _print(pt, order):

    if sys.version_info >= (3, 0):
        print(pt.get_string(sortby=order))
    else:
        print(encodeutils.safe_encode(pt.get_string(sortby=order)))


def print_list(objs, fields, formatters={}, order_by=None, obj_is_dict=False,
               labels={}):
    try:
        _output_override(objs, 'list')
        return
    except BaseException:
        pass
    # Make nice labels from the fields, if not provided in the labels arg
    if not labels:
        labels = {}
    for field in fields:
        if field not in labels:
            # No underscores (use spaces instead) and uppercase any ID's
            label = field.replace("_", " ").replace(" id", " ID")
            # Uppercase anything else that's less than 3 chars
            if len(label) < 3:
                label = label.upper()
            # Capitalize each word otherwise
            else:
                label = ' '.join(word[0].upper() + word[1:]
                                 for word in label.split())
            labels[field] = label

    pt = prettytable.PrettyTable(
        [labels[field] for field in fields], caching=False)
    # set the default alignment to left-aligned
    align = dict((labels[field], 'l') for field in fields)
    set_align = True
    for obj in objs:
        row = []
        for field in fields:
            if formatters and field in formatters:
                row.append(formatters[field](obj))
            elif obj_is_dict:
                data = obj.get(field, '')
            else:
                data = getattr(obj, field, '')
            if isinstance(data, six.string_types):
                row.append(data.encode('utf-8'))
            else:
                row.append(str(data))
            # set the alignment to right-aligned if it's a numeric
            if set_align and hasattr(data, '__int__'):
                align[labels[field]] = 'r'
        set_align = False
        pt.add_row(row)
    pt._align = align

    if not order_by:
        order_by = fields[0]
    order_by = labels[order_by]
    _print(pt, order_by)


def print_dict(d, property="Property"):
    try:
        _output_override(d, 'dict')
        return
    except BaseException:
        pass
    pt = prettytable.PrettyTable([property, 'Value'], caching=False)
    pt.align = 'l'
    [pt.add_row(list(r)) for r in six.iteritems(d)]
    _print(pt, property)


def get_resource_id_by_name(manager, name):
    resource = manager.find(name=name)
    return resource.id


def find_resource(manager, name_or_id):
    """Helper for the _find_* methods."""
    # first try to get entity as integer id

    # When the 'name_or_id' is int, covert it to string.
    # Reason is that manager cannot find instance when name_or_id
    # is integer and instance name is digital.
    # Related to bug/1740015.
    if isinstance(name_or_id, int):
        name_or_id = six.text_type(name_or_id)
    elif sys.version_info <= (3, 0):
        name_or_id = encodeutils.safe_decode(name_or_id)

    try:
        return manager.get(name_or_id)
    except exceptions.NotFound:
        pass

    try:
        try:
            return manager.find(human_id=name_or_id)
        except exceptions.NotFound:
            pass

        # finally try to find entity by name
        try:
            return manager.find(name=name_or_id)
        except exceptions.NotFound:
            try:
                return manager.find(display_name=name_or_id)
            except (UnicodeDecodeError, exceptions.NotFound):
                try:
                    # Instances does not have name, but display_name
                    return manager.find(display_name=name_or_id)
                except exceptions.NotFound:
                    msg = "No %s with a name or ID of '%s' exists." % \
                        (manager.resource_class.__name__.lower(), name_or_id)
                    raise exceptions.CommandError(msg)
    except exceptions.NoUniqueMatch:
        msg = ("Multiple %s matches found for '%s', use an ID to be more"
               " specific." % (manager.resource_class.__name__.lower(),
                               name_or_id))
        raise exceptions.CommandError(msg)


def is_admin(cs):
    is_admin = False
    try:
        is_admin = 'admin' in cs.client.auth.auth_ref.role_names
    except Exception:
        print("Warning: Could not determine current role. Assuming non-admin")
        pass

    return is_admin


class HookableMixin(object):
    """Mixin so classes can register and run hooks."""
    _hooks_map = {}

    @classmethod
    def add_hook(cls, hook_type, hook_func):
        if hook_type not in cls._hooks_map:
            cls._hooks_map[hook_type] = []

        cls._hooks_map[hook_type].append(hook_func)

    @classmethod
    def run_hooks(cls, hook_type, *args, **kwargs):
        hook_funcs = cls._hooks_map.get(hook_type) or []
        for hook_func in hook_funcs:
            hook_func(*args, **kwargs)


def safe_issubclass(*args):
    """Like issubclass, but will just return False if not a class."""

    try:
        if issubclass(*args):
            return True
    except TypeError:
        pass

    return False


def is_uuid_like(val):
    """Returns validation of a value as a UUID.

    For our purposes, a UUID is a canonical form string:
    aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa

    """
    try:
        return str(uuid.UUID(val)) == val
    except (TypeError, ValueError, AttributeError):
        return False


def encode_data(data):
    """Encode the data using the base64 codec."""

    try:
        # py27str - if we've got text data, this should encode it
        # py27aa/py34aa - if we've got a bytearray, this should work too
        encoded = str(base64.b64encode(data).decode('utf-8'))
    except TypeError:
        # py34str - convert to bytes first, then we can encode
        data_bytes = bytes([ord(item) for item in data])
        encoded = base64.b64encode(data_bytes).decode('utf-8')

    return encoded


def decode_data(data):
    """Encode the data using the base64 codec."""

    # py27 & py34 seem to understand bytearray the same
    return bytearray([item for item in base64.b64decode(data)])


def do_action_with_msg(action, success_msg):
    """Helper to run an action with return message."""

    action
    print(success_msg)


def do_action_on_many(action, resources, success_msg, error_msg):
    """Helper to run an action on many resources."""
    failure_flag = False

    for resource in resources:
        try:
            action(resource)
            print(success_msg % resource)
        except Exception as e:
            failure_flag = True
            print(encodeutils.safe_encode(six.text_type(e)))

    if failure_flag:
        raise exceptions.CommandError(error_msg)
