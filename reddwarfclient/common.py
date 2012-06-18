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

import os
import pickle
import sys

from reddwarfclient.client import Dbaas
import exceptions


APITOKEN = os.path.expanduser("~/.apitoken")


def get_client():
    """Load an existing apitoken if available"""
    try:
        with open(APITOKEN, 'rb') as token:
            apitoken = pickle.load(token)
            dbaas = Dbaas(apitoken._user, apitoken._apikey,
                          tenant=apitoken._tenant, auth_url=apitoken._auth_url,
                          auth_strategy=apitoken._auth_strategy,
                          service_name=apitoken._service_name,
                          service_url=apitoken._service_url,
                          insecure=apitoken._insecure)
            dbaas.client.auth_token = apitoken._token
            return dbaas
    except IOError:
        print "ERROR: You need to login first and get an auth token\n"
        sys.exit(1)
    except:
        print "ERROR: There was an error using your existing auth token, " \
              "please login again.\n"
        sys.exit(1)


def methods_of(obj):
    """Get all callable methods of an object that don't start with underscore
    returns a list of tuples of the form (method_name, method)"""
    result = {}
    for i in dir(obj):
        if callable(getattr(obj, i)) and not i.startswith('_'):
            result[i] = getattr(obj, i)
    return result


def check_for_exceptions(resp, body):
    if resp.status in (400, 422, 500):
            raise exceptions.from_response(resp, body)


def print_actions(cmd, actions):
    """Print help for the command with list of options and description"""
    print ("Available actions for '%s' cmd:") % cmd
    for k, v in actions.iteritems():
        print "\t%-20s%s" % (k, v.__doc__)
    sys.exit(2)


def print_commands(commands):
    """Print the list of available commands and description"""

    print "Available commands"
    for k, v in commands.iteritems():
        print "\t%-20s%s" % (k, v.__doc__)
    sys.exit(2)


def limit_url(url, limit=None, marker=None):
    if not limit and not marker:
        return url
    query = []
    if marker:
        query.append("marker=%s" % marker)
    if limit:
        query.append("limit=%s" % limit)
    query = '?' + '&'.join(query)
    return url + query


class APIToken(object):
    """A token object containing the user, apikey and token which
       is pickleable."""

    def __init__(self, user, apikey, tenant, token, auth_url, auth_strategy,
                 service_name, service_url, region_name, insecure):
        self._user = user
        self._apikey = apikey
        self._tenant = tenant
        self._token = token
        self._auth_url = auth_url
        self._auth_strategy = auth_strategy
        self._service_name = service_name
        self._service_url = service_url
        self._region_name = region_name
        self._insecure = insecure


class Auth(object):
    """Authenticate with your username and api key"""

    def __init__(self):
        pass

    def login(self, user, apikey, tenant="dbaas",
              auth_url="http://localhost:5000/v1.1",
              auth_strategy="basic", service_name="reddwarf",
              region_name="default", service_url=None, insecure=True):
        """Login to retrieve an auth token to use for other api calls"""
        try:
            dbaas = Dbaas(user, apikey, tenant, auth_url=auth_url,
                          auth_strategy=auth_strategy,
                          service_name=service_name, region_name=None,
                          service_url=service_url, insecure=insecure)
            dbaas.authenticate()
            apitoken = APIToken(user, apikey, tenant, dbaas.client.auth_token,
                                auth_url, auth_strategy, service_name,
                                service_url, region_name, insecure)

            with open(APITOKEN, 'wb') as token:
                pickle.dump(apitoken, token, protocol=2)
            print apitoken._token
        except:
            print sys.exc_info()[1]


class Paginated(object):
    """ Pretends to be a list if you iterate over it, but also keeps a
        next property you can use to get the next page of data. """

    def __init__(self, items=[], next_marker=None, links=[]):
        self.items = items
        self.next = next_marker
        self.links = links

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return self.items.__iter__()

    def __getitem__(self, key):
        return self.items[key]

    def __setitem__(self, key, value):
        self.items[key] = value

    def __delitem(self, key):
        del self.items[key]

    def __reversed__(self):
        return reversed(self.items)

    def __contains__(self, needle):
        return needle in self.items
