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

import exceptions

from reddwarfclient.common import check_for_exceptions


REBOOT_SOFT, REBOOT_HARD = 'SOFT', 'HARD'


class Instance(base.Resource):
    """
    An Instance is an opaque instance used to store Database instances.
    """
    def __repr__(self):
        return "<Instance: %s>" % self.name

    def list_databases(self):
        return self.manager.databases.list(self)

    def delete(self):
        """
        Delete the instance.
        """
        self.manager.delete(self)

    def restart(self):
        """
        Restart the database instance
        """
        self.manager.restart(self.id)


class Instances(base.ManagerWithFind):
    """
    Manage :class:`Instance` resources.
    """
    resource_class = Instance

    def create(self, name, flavor_id, volume, databases=None, users=None):
        """
        Create (boot) a new instance.
        """
        body = {"instance": {
            "name": name,
            "flavorRef": flavor_id,
            "volume": volume
        }}
        if databases:
            body["instance"]["databases"] = databases
        if users:
            body["instance"]["users"] = users

        return self._create("/instances", body, "instance")

    def _list(self, url, response_key):
        resp, body = self.api.client.get(url)
        if not body:
            raise Exception("Call to " + url + " did not return a body.")
        return [self.resource_class(self, res) for res in body[response_key]]

    def list(self):
        """
        Get a list of all instances.

        :rtype: list of :class:`Instance`.
        """
        return self._list("/instances/detail", "instances")

    def index(self):
        """
        Get a list of all instances.

        :rtype: list of :class:`Instance`.
        """
        return self._list("/instances", "instances")

    def details(self):
        """
        Get details of all instances.

        :rtype: list of :class:`Instance`.
        """
        return self._list("/instances/detail", "instances")

    def get(self, instance):
        """
        Get a specific instances.

        :rtype: :class:`Instance`
        """
        return self._get("/instances/%s" % base.getid(instance),
                        "instance")

    def delete(self, instance):
        """
        Delete the specified instance.

        :param instance_id: The instance id to delete
        """
        resp, body = self.api.client.delete("/instances/%s" %
                                            base.getid(instance))
        if resp.status in (422, 500):
            raise exceptions.from_response(resp, body)

    def _action(self, instance_id, body):
        """
        Perform a server "action" -- reboot/rebuild/resize/etc.
        """
        url = "/instances/%s/action" % instance_id
        resp, body = self.api.client.post(url, body=body)
        check_for_exceptions(resp, body)

    def resize_volume(self, instance_id, volume_size):
        """
        Resize the volume on an existing instances
        """
        body = {"resize": {"volume": {"size": volume_size}}}
        self._action(instance_id, body)

    def resize_instance(self, instance_id, flavor_id):
        """
        Resize the volume on an existing instances
        """
        body = {"resize": {"flavorRef": flavor_id}}
        self._action(instance_id, body)

    def restart(self, instance_id):
        """
        Restart the database instance.

        :param instance_id: The :class:`Instance` (or its ID) to share onto.
        """
        body = {'restart': {}}
        self._action(instance_id, body)


class InstanceStatus(object):

    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    BUILD = "BUILD"
    FAILED = "FAILED"
    REBOOT = "REBOOT"
    RESIZE = "RESIZE"
    SHUTDOWN = "SHUTDOWN"
