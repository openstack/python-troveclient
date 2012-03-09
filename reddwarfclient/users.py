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

from novaclient import base
from reddwarfclient.common import check_for_exceptions
import exceptions


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

    def delete(self, instance_id, user):
        """Delete an existing user in the specified instance"""
        url = "/instances/%s/users/%s"% (instance_id, user)
        resp, body = self.api.client.delete(url)
        check_for_exceptions(resp, body)

    def _list(self, url, response_key):
        resp, body = self.api.client.get(url)
        check_for_exceptions(resp, body)
        if not body:
            raise Exception("Call to " + url +
                            " did not return a body.")
        return [self.resource_class(self, res) for res in body[response_key]]

    def list(self, instance):
        """
        Get a list of all Users from the instance's Database.

        :rtype: list of :class:`User`.
        """
        return self._list("/instances/%s/users" % base.getid(instance),
                          "users")