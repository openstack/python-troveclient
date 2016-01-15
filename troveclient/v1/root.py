# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
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
from troveclient.v1 import users


class Root(base.ManagerWithFind):
    """Manager class for Root resource."""
    resource_class = users.User
    instances_url = "/instances/%s/root"
    clusters_url = "/clusters/%s/root"

    def create(self, instance):
        """Implements root-enable API.
        Enable the root user and return the root password for the
        specified db instance.
        """
        return self.create_instance_root(instance)

    def create_instance_root(self, instance, root_password=None):
        """Implements root-enable for instances."""
        return self._enable_root(self.instances_url % base.getid(instance),
                                 root_password)

    def create_cluster_root(self, cluster, root_password=None):
        """Implements root-enable for clusters."""
        return self._enable_root(self.clusters_url % base.getid(cluster),
                                 root_password)

    def _enable_root(self, uri, root_password=None):
        """Implements root-enable API.
        Enable the root user and return the root password for the
        specified db instance or cluster.
        """
        if root_password:
            resp, body = self.api.client.post(uri,
                                              body={"password": root_password})
        else:
            resp, body = self.api.client.post(uri)
        common.check_for_exceptions(resp, body, uri)
        return body['user']['name'], body['user']['password']

    def delete(self, instance):
        """Implements root-disable API.
        Disables access to the root user for the specified db instance.
        :param instance: The instance on which the root user is enabled
        """
        self.disable_instance_root(instance)

    def disable_instance_root(self, instance):
        """Implements root-disable for instances."""
        self._disable_root(self.instances_url % base.getid(instance))

    def _disable_root(self, url):
        resp, body = self.api.client.delete(url)
        common.check_for_exceptions(resp, body, url)

    def is_root_enabled(self, instance):
        """Return whether root is enabled for the instance."""
        return self.is_instance_root_enabled(instance)

    def is_instance_root_enabled(self, instance):
        """Returns whether root is enabled for the instance."""
        return self._is_root_enabled(self.instances_url % base.getid(instance))

    def is_cluster_root_enabled(self, cluster):
        """Returns whether root is enabled for the cluster."""
        return self._is_root_enabled(self.clusters_url % base.getid(cluster))

    def _is_root_enabled(self, uri):
        """Return whether root is enabled for the instance or the cluster."""
        resp, body = self.api.client.get(uri)
        common.check_for_exceptions(resp, body, uri)
        return self.resource_class(self, body, loaded=True)

    # Appease the abc gods
    def list(self):
        pass
