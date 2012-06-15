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
if os.path.exists(os.path.join(possible_topdir, 'nova', '__init__.py')):
    sys.path.insert(0, possible_topdir)


from reddwarfclient import common


oparser = None


def _pretty_print(info):
    print json.dumps(info, sort_keys=True, indent=4)


class HostCommands(object):
    """Commands to list info on hosts"""

    def __init__(self):
        pass

    def get(self, name):
        """List details for the specified host"""
        dbaas = common.get_client()
        try:
            _pretty_print(dbaas.hosts.get(name)._info)
        except:
            print sys.exc_info()[1]

    def list(self):
        """List all compute hosts"""
        dbaas = common.get_client()
        try:
            for host in dbaas.hosts.index():
                _pretty_print(host._info)
        except:
            print sys.exc_info()[1]


class RootCommands(object):
    """List details about the root info for an instance."""

    def __init__(self):
        pass

    def history(self, id):
        """List root history for the instance."""
        dbaas = common.get_client()
        try:
            result = dbaas.management.root_enabled_history(id)
            _pretty_print(result._info)
        except:
            print sys.exc_info()[1]


class AccountCommands(object):
    """Commands to list account info"""

    def __init__(self):
        pass

    def get(self, acct):
        """List details for the account provided"""
        dbaas = common.get_client()
        try:
            _pretty_print(dbaas.accounts.show(acct)._info)
        except:
            print sys.exc_info()[1]


def config_options():
    global oparser
    oparser.add_option("-u", "--url", default="http://localhost:5000/v1.1",
                       help="Auth API endpoint URL with port and version. \
                            Default: http://localhost:5000/v1.1")


COMMANDS = {'account': AccountCommands,
            'host': HostCommands,
            'root': RootCommands,
            }


def main():
    # Parse arguments
    global oparser
    oparser = optparse.OptionParser("%prog [options] <cmd> <action> <args>",
                                    version='1.0')
    config_options()
    (options, args) = oparser.parse_args()

    if not args:
        common.print_commands(COMMANDS)

    # Pop the command and check if it's in the known commands
    cmd = args.pop(0)
    if cmd in COMMANDS:
        fn = COMMANDS.get(cmd)
        command_object = fn()

        # Get a list of supported actions for the command
        actions = common.methods_of(command_object)

        if len(args) < 1:
            common.print_actions(cmd, actions)

        # Check for a valid action and perform that action
        action = args.pop(0)
        if action in actions:
            fn = actions.get(action)

            try:
                fn(*args)
                sys.exit(0)
            except TypeError as err:
                print "Possible wrong number of arguments supplied."
                print "%s %s: %s" % (cmd, action, fn.__doc__)
                print "\t\t", [fn.func_code.co_varnames[i] for i in
                                            range(fn.func_code.co_argcount)]
                print "ERROR: %s" % err
            except Exception:
                print "Command failed, please check the log for more info."
                raise
        else:
            common.print_actions(cmd, actions)
    else:
        common.print_commands(COMMANDS)


if __name__ == '__main__':
    main()
