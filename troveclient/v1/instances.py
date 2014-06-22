# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from troveclient import base
from troveclient import common

REBOOT_SOFT = 'SOFT'
REBOOT_HARD = 'HARD'


class Instance(base.Resource):
    """An Instance is an opaque instance used to store Database instances."""
    def __repr__(self):
        return "<Instance: %s>" % self.name

    def list_databases(self):
        return self.manager.databases.list(self)

    def delete(self):
        """Delete the instance."""
        self.manager.delete(self)

    def restart(self):
        """Restart the database instance."""
        self.manager.restart(self.id)

    def detach_replica(self):
        """Stops the replica database from being replicated to."""
        self.manager.edit(self.id, detach_replica_source=True)


class Instances(base.ManagerWithFind):
    """Manage :class:`Instance` resources."""
    resource_class = Instance

    def create(self, name, flavor_id, volume=None, databases=None, users=None,
               restorePoint=None, availability_zone=None, datastore=None,
               datastore_version=None, nics=None, configuration=None,
               slave_of=None):
        """Create (boot) a new instance."""
        body = {"instance": {
            "name": name,
            "flavorRef": flavor_id
        }}
        datastore_obj = {}
        if volume:
            body["instance"]["volume"] = volume
        if databases:
            body["instance"]["databases"] = databases
        if users:
            body["instance"]["users"] = users
        if restorePoint:
            body["instance"]["restorePoint"] = restorePoint
        if availability_zone:
            body["instance"]["availability_zone"] = availability_zone
        if datastore:
            datastore_obj["type"] = datastore
        if datastore_version:
            datastore_obj["version"] = datastore_version
        if datastore_obj:
            body["instance"]["datastore"] = datastore_obj
        if nics:
            body["instance"]["nics"] = nics
        if configuration:
            body["instance"]["configuration"] = configuration
        if slave_of:
            body["instance"]["slave_of"] = slave_of

        return self._create("/instances", body, "instance")

    def modify(self, instance_id, configuration=None):
        body = {
            "instance": {
            }
        }
        if configuration is not None:
            body["instance"]["configuration"] = configuration
        url = "/instances/%s" % instance_id
        resp, body = self.api.client.put(url, body=body)
        common.check_for_exceptions(resp, body, url)

    def edit(self, instance_id, configuration=None, name=None,
             detach_replica_source=False):
        body = {
            "instance": {
            }
        }
        if configuration is not None:
            body["instance"]["configuration"] = configuration
        if name is not None:
            body["instance"]["name"] = name
        if detach_replica_source:
            body["instance"]["slave_of"] = None

        url = "/instances/%s" % instance_id
        resp, body = self.api.client.patch(url, body=body)
        common.check_for_exceptions(resp, body, url)

    def list(self, limit=None, marker=None):
        """Get a list of all instances.

        :rtype: list of :class:`Instance`.
        """
        return self._paginated("/instances", "instances", limit, marker)

    def get(self, instance):
        """Get a specific instances.

        :rtype: :class:`Instance`
        """
        return self._get("/instances/%s" % base.getid(instance),
                         "instance")

    def backups(self, instance, limit=None, marker=None):
        """Get the list of backups for a specific instance.

        :rtype: list of :class:`Backups`.
        """
        url = "/instances/%s/backups" % base.getid(instance)
        return self._paginated(url, "backups", limit, marker)

    def delete(self, instance):
        """Delete the specified instance.

        :param instance_id: The instance id to delete
        """
        url = "/instances/%s" % base.getid(instance)
        resp, body = self.api.client.delete(url)
        common.check_for_exceptions(resp, body, url)

    def _action(self, instance_id, body):
        """Perform a server "action" -- reboot/rebuild/resize/etc."""
        url = "/instances/%s/action" % instance_id
        resp, body = self.api.client.post(url, body=body)
        common.check_for_exceptions(resp, body, url)
        if body:
            return self.resource_class(self, body, loaded=True)
        return body

    def resize_volume(self, instance_id, volume_size):
        """Resize the volume on an existing instances."""
        body = {"resize": {"volume": {"size": volume_size}}}
        self._action(instance_id, body)

    def resize_instance(self, instance_id, flavor_id):
        """Resizes an instance with a new flavor."""
        body = {"resize": {"flavorRef": flavor_id}}
        self._action(instance_id, body)

    def restart(self, instance_id):
        """Restart the database instance.

        :param instance_id: The :class:`Instance` (or its ID) to share onto.
        """
        body = {'restart': {}}
        self._action(instance_id, body)

    def configuration(self, instance):
        """Get a configuration on instances.

        :rtype: :class:`Instance`
        """
        return self._get("/instances/%s/configuration" % base.getid(instance),
                         "instance")


class InstanceStatus(object):

    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    BUILD = "BUILD"
    FAILED = "FAILED"
    REBOOT = "REBOOT"
    RESIZE = "RESIZE"
    SHUTDOWN = "SHUTDOWN"
    RESTART_REQUIRED = "RESTART_REQUIRED"
