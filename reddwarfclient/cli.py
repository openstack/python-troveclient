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
Reddwarf Command line tool
"""

#TODO(tim.simpson): optparse is deprecated. Replace with argparse.
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


class InstanceCommands(common.AuthedCommandsBase):
    """Commands to perform various instances operations and actions"""

    params = [
              'flavor',
              'id',
              'limit',
              'marker',
              'name',
              'size',
             ]

    def create(self):
        """Create a new instance"""
        self._require('name', 'size')
        # flavorRef is not required.
        flavorRef = self.flavor or "http://localhost:8775/v1.0/flavors/1"
        volume = {"size": self.size}
        self._pretty_print(self.dbaas.instances.create, self.name,
                          flavorRef, volume)

    def delete(self):
        """Delete the specified instance"""
        self._require('id')
        print self.dbaas.instances.delete(self.id)

    def get(self):
        """Get details for the specified instance"""
        self._require('id')
        self._pretty_print(self.dbaas.instances.get, self.id)

    def list(self):
        """List all instances for account"""
        # limit and marker are not required.
        limit = self.limit or None
        if limit:
            limit = int(limit, 10)
        self._pretty_paged(self.dbaas.instances.list)

    def resize_volume(self):
        """Resize an instance volume"""
        self._require('id', 'size')
        self._pretty_print(self.dbaas.instances.resize_volume, self.id,
                          self.size)

    def resize_instance(self):
        """Resize an instance flavor"""
        self._require('id', 'flavor')
        self._pretty_print(self.dbaas.instances.resize_instance, self.id,
                          self.flavor)

    def restart(self):
        """Restart the database"""
        self._require('id')
        self._pretty_print(self.dbaas.instances.restart, self.id)

    def reset_password(self):
        """Reset the root user Password"""
        self._require('id')
        self._pretty_print(self.dbaas.instances.reset_password, self.id)
            

class FlavorsCommands(common.AuthedCommandsBase):
    """Commands for listing Flavors"""

    params = []

    def list(self):
        """List the available flavors"""
        self._pretty_list(self.dbaas.flavors.list)


class DatabaseCommands(common.AuthedCommandsBase):
    """Database CRUD operations on an instance"""

    params = [
              'name',
              'id',
              'limit',
              'marker',
             ]

    def create(self):
        """Create a database"""
        self._require('id', 'name')
        databases = [{'name': self.name}]
        print self.dbaas.databases.create(self.id, databases)

    def delete(self):
        """Delete a database"""
        self._require('id', 'name')
        print self.dbaas.databases.delete(self.id, self.name)

    def list(self):
        """List the databases"""
        self._require('id')
        self._pretty_paged(self.dbaas.databases.list, self.id)


class UserCommands(common.AuthedCommandsBase):
    """User CRUD operations on an instance"""
    params = [
              'id',
              'databases',
              'name',
              'password',
             ]

    def create(self):
        """Create a user in instance, with access to one or more databases"""
        self._require('id', 'name', 'password', 'databases')
        self._make_list('databases')
        databases = [{'name': dbname} for dbname in self.databases]
        users = [{'name': self.username, 'password': self.password,
                  'databases': databases}]
        self.dbaas.users.create(self.id, users)

    def delete(self):
        """Delete the specified user"""
        self._require('id', 'name')
        self.users.delete(self.id, self.name)

    def list(self):
        """List all the users for an instance"""
        self._require('id')
        self._pretty_paged(self.dbaas.users.list, self.id)


class RootCommands(common.AuthedCommandsBase):
    """Root user related operations on an instance"""

    params = [
              'id',
             ]

    def create(self):
        """Enable the instance's root user."""
        self._require('id')
        try:
            user, password = self.dbaas.root.create(self.id)
            print "User:\t\t%s\nPassword:\t%s" % (user, password)
        except:
            print sys.exc_info()[1]

    def enabled(self):
        """Check the instance for root access"""
        self._require('id')
        self._pretty_print(self.dbaas.root.is_root_enabled, self.id)


class VersionCommands(common.AuthedCommandsBase):
    """List available versions"""

    params = [
              'url',
             ]

    def list(self):
        """List all the supported versions"""
        self._require('url')
        self._pretty_print(self.dbaas.versions.index, self.url)


COMMANDS = {'auth': common.Auth,
            'instance': InstanceCommands,
            'flavor': FlavorsCommands,
            'database': DatabaseCommands,
            'user': UserCommands,
            'root': RootCommands,
            'version': VersionCommands,
            }

def main():
    # Parse arguments
    oparser = common.CliOptions.create_optparser()
    for k, v in COMMANDS.items():
        v._prepare_parser(oparser)
    (options, args) = oparser.parse_args()

    if not args:
        common.print_commands(COMMANDS)

    if options.verbose:
        os.environ['RDC_PP']  = "True"
        os.environ['REDDWARFCLIENT_DEBUG'] = "True"

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
            if not options.debug:
                try:
                    getattr(command_object, action)()
                except Exception as ex:
                    if options.debug:
                        raise
                    print ex
            else:
                getattr(command_object, action)()
        else:
            common.print_actions(cmd, actions)
    else:
        common.print_commands(COMMANDS)


if __name__ == '__main__':
    main()
