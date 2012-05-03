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


class Config(base.Resource):
    """
    A configuration entry
    """
    def __repr__(self):
        return "<Config: %s>" % self.key


class Configs(base.ManagerWithFind):
    """
    Manage :class:`Configs` resources.
    """
    resource_class = Config

    def create(self, configs):
        """
        Create the configuration entries
        """
        body = {"configs": configs}
        url = "/mgmt/configs"
        resp, body = self.api.client.post(url, body=body)

    def delete(self, config):
        """
        Delete an existing configuration
        """
        url = "/mgmt/configs/%s" % config
        self._delete(url)

    def list(self):
        """
        Get a list of all configuration entries
        """
        resp, body = self.api.client.get("/mgmt/configs")
        if not body:
            raise Exception("Call to /mgmt/configs did not return a body.")
        return [self.resource_class(self, res) for res in body['configs']]

    def get(self, config):
        """
        Get the specified configuration entry
        """
        url = "/mgmt/configs/%s" % config
        resp, body = self.api.client.get(url)
        if not body:
            raise Exception("Call to %s did not return a body." % url)
        return self.resource_class(self, body['config'])

    def update(self, config):
        """
        Update the configuration entries
        """
        body = {"config": config}
        url = "/mgmt/configs/%s" % config['key']
        resp, body = self.api.client.put(url, body=body)
