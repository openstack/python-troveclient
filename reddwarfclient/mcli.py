#!/usr/bin/env python

#    Copyright 2011 OpenStack LLC
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

"""
Reddwarf Management Command line tool
"""

import json
import optparse
import os
import sys


# If ../reddwarf/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir,
                                   os.pardir))
if os.path.exists(os.path.join(possible_topdir, 'reddwarfclient',
                               '__init__.py')):
    sys.path.insert(0, possible_topdir)


from reddwarfclient import common


oparser = None


def _pretty_print(info):
    print json.dumps(info, sort_keys=True, indent=4)


class HostCommands(common.AuthedCommandsBase):
    """Commands to list info on hosts"""

    params = [
              'name',
             ]

    def update_all(self):
        """Update all instances on a host"""
        self._require('name')
        self.dbaas.hosts.update_all(self.name)

    def get(self):
        """List details for the specified host"""
        self._require('name')
        self._pretty_print(self.dbaas.hosts.get, self.name)

    def list(self):
        """List all compute hosts"""
        self._pretty_list(self.dbaas.hosts.index)


class RootCommands(common.AuthedCommandsBase):
    """List details about the root info for an instance."""

    params = [
              'id',
             ]

    def history(self):
        """List root history for the instance."""
        self._require('id')
        self._pretty_print(self.dbaas.management.root_enabled_history, self.id)


class AccountCommands(common.AuthedCommandsBase):
    """Commands to list account info"""

    params = [
              'id',
             ]

    def list(self):
        """List all accounts with non-deleted instances"""
        self._pretty_print(self.dbaas.accounts.index)

    def get(self):
        """List details for the account provided"""
        self._require('id')
        self._pretty_print(self.dbaas.accounts.show, self.id)


class InstanceCommands(common.AuthedCommandsBase):
    """List details about an instance."""

    params = [
              'deleted',
              'id',
              'limit',
              'marker',
             ]

    def get(self):
        """List details for the instance."""
        self._require('id')
        self._pretty_print(self.dbaas.management.show, self.id)

    def list(self):
        """List all instances for account"""
        deleted = None
        if self.deleted is not None:
            if self.deleted.lower() in ['true']:
                deleted = True
            elif self.deleted.lower() in ['false']:
                deleted = False
        self._pretty_paged(self.dbaas.management.index, deleted=deleted)

    def diagnostic(self):
        """List diagnostic details about an instance."""
        self._require('id')
        dbaas = common.get_client()
        self._pretty_print(self.dbaas.diagnostics.get, self.id)

    def stop(self):
        """Stop MySQL on the given instance."""
        self._require('id')
        self._pretty_print(self.dbaas.management.stop, self.id)

    def reboot(self, id):
        """Reboot the instance."""
        self._require('id')
        self._pretty_print(self.dbaas.management.reboot, self.id)


class StorageCommands(common.AuthedCommandsBase):
    """Commands to list devices info"""

    params = []

    def list(self):
        """List details for the storage device"""
        dbaas = common.get_client()
        self._pretty_list(self.dbaas.storage.index)


def config_options(oparser):
    oparser.add_option("-u", "--url", default="http://localhost:5000/v1.1",
                       help="Auth API endpoint URL with port and version. \
                            Default: http://localhost:5000/v1.1")


COMMANDS = {'account': AccountCommands,
            'host': HostCommands,
            'instance': InstanceCommands,
            'root': RootCommands,
            'storage': StorageCommands,
            }


def main():
    # Parse arguments
    oparser = common.CliOptions.create_optparser()
    for k, v in COMMANDS.items():
        v._prepare_parser(oparser)
    (options, args) = oparser.parse_args()

    if not args:
        common.print_commands(COMMANDS)

    # Pop the command and check if it's in the known commands
    cmd = args.pop(0)
    if cmd in COMMANDS:
        fn = COMMANDS.get(cmd)
        command_object = None
        try:
            command_object = fn(oparser)
        except Exception as ex:
            if options.debug:
                raise
            print(ex)

        # Get a list of supported actions for the command
        actions = common.methods_of(command_object)

        if len(args) < 1:
            common.print_actions(cmd, actions)

        # Check for a valid action and perform that action
        action = args.pop(0)
        if action in actions:
            try:
                getattr(command_object, action)()
            except Exception as ex:
                if options.debug:
                    raise
                print ex
        else:
            common.print_actions(cmd, actions)
    else:
        common.print_commands(COMMANDS)


if __name__ == '__main__':
    main()
