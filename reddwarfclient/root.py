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

from reddwarfclient import users
from reddwarfclient.common import check_for_exceptions
import exceptions


class Root(base.ManagerWithFind):
    """
    Manager class for Root resource
    """
    resource_class = users.User
    url = "/instances/%s/root"

    def create(self, instance_id):
        """
        Enable the root user and return the root password for the
        sepcified db instance
        """
        resp, body = self.api.client.post(self.url % instance_id)
        check_for_exceptions(resp, body)
        return body['user']['name'], body['user']['password']

    def is_root_enabled(self, instance_id):
        """ Return True if root is enabled for the instance;
        False otherwise"""
        resp, body = self.api.client.get(self.url % instance_id)
        check_for_exceptions(resp, body)
        return body['rootEnabled']
