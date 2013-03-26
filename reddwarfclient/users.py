# Copyright (c) 2011 OpenStack, LLC.
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

from reddwarfclient import base
from reddwarfclient import databases
from reddwarfclient.common import check_for_exceptions
from reddwarfclient.common import limit_url
from reddwarfclient.common import Paginated
from reddwarfclient.common import quote_user_host
import exceptions
import urlparse


class User(base.Resource):
    """
    A database user
    """
    def __repr__(self):
        return "<User: %s>" % self.name


class Users(base.ManagerWithFind):
    """
    Manage :class:`Users` resources.
    """
    resource_class = User

    def create(self, instance_id, users):
        """
        Create users with permissions to the specified databases
        """
        body = {"users": users}
        url = "/instances/%s/users" % instance_id
        resp, body = self.api.client.post(url, body=body)
        check_for_exceptions(resp, body)

    def delete(self, instance_id, username, hostname=None):
        """Delete an existing user in the specified instance"""
        user = quote_user_host(username, hostname)
        url = "/instances/%s/users/%s" % (instance_id, user)
        resp, body = self.api.client.delete(url)
        check_for_exceptions(resp, body)

    def _list(self, url, response_key, limit=None, marker=None):
        resp, body = self.api.client.get(limit_url(url, limit, marker))
        check_for_exceptions(resp, body)
        if not body:
            raise Exception("Call to " + url +
                            " did not return a body.")
        links = body.get('links', [])
        next_links = [link['href'] for link in links if link['rel'] == 'next']
        next_marker = None
        for link in next_links:
            # Extract the marker from the url.
            parsed_url = urlparse.urlparse(link)
            query_dict = dict(urlparse.parse_qsl(parsed_url.query))
            next_marker = query_dict.get('marker', None)
        users = [self.resource_class(self, res) for res in body[response_key]]
        return Paginated(users, next_marker=next_marker, links=links)

    def list(self, instance, limit=None, marker=None):
        """
        Get a list of all Users from the instance's Database.

        :rtype: list of :class:`User`.
        """
        return self._list("/instances/%s/users" % base.getid(instance),
                          "users", limit, marker)

    def get(self, instance_id, username, hostname=None):
        """
        Get a single User from the instance's Database.

        :rtype: :class:`User`.
        """
        user = quote_user_host(username, hostname)
        url = "/instances/%s/users/%s" % (instance_id, user)
        return self._get(url, "user")

    def list_access(self, instance, username, hostname=None):
        """Show all databases the given user has access to. """
        instance_id = base.getid(instance)
        user = quote_user_host(username, hostname)
        url = "/instances/%(instance_id)s/users/%(user)s/databases"
        resp, body = self.api.client.get(url % locals())
        check_for_exceptions(resp, body)
        if not body:
            raise Exception("Call to %s did not return to a body" % url)
        return [databases.Database(self, db) for db in body['databases']]

    def grant(self, instance, username, databases, hostname=None):
        """Allow an existing user permissions to access a database."""
        instance_id = base.getid(instance)
        user = quote_user_host(username, hostname)
        url = "/instances/%(instance_id)s/users/%(user)s/databases"
        dbs = {'databases': [{'name': db} for db in databases]}
        resp, body = self.api.client.put(url % locals(), body=dbs)
        check_for_exceptions(resp, body)

    def revoke(self, instance, username, database, hostname=None):
        """Revoke from an existing user access permissions to a database."""
        instance_id = base.getid(instance)
        user = quote_user_host(username, hostname)
        url = ("/instances/%(instance_id)s/users/%(user)s/"
               "databases/%(database)s")
        resp, body = self.api.client.delete(url % locals())
        check_for_exceptions(resp, body)

    def change_passwords(self, instance, users):
        """Change the password for one or more users."""
        instance_id = base.getid(instance)
        user_dict = {"users": users}
        url = "/instances/%s/users" % instance_id
        resp, body = self.api.client.put(url, body=user_dict)
        check_for_exceptions(resp, body)
