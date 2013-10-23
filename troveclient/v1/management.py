# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from troveclient.common import check_for_exceptions
from troveclient.common import limit_url
from troveclient.common import Paginated
from troveclient.openstack.common.py3kcompat import urlutils
from troveclient.v1.instances import Instance
from troveclient.v1.flavors import Flavor


class RootHistory(base.Resource):
    def __repr__(self):
        return ("<Root History: Instance %s enabled at %s by %s>"
                % (self.id, self.created, self.user))


class Management(base.ManagerWithFind):
    """
    Manage :class:`Instances` resources.
    """
    resource_class = Instance

    # Appease the abc gods
    def list(self):
        pass

    def _list(self, url, response_key, limit=None, marker=None):
        resp, body = self.api.client.get(limit_url(url, limit, marker))
        if not body:
            raise Exception("Call to " + url + " did not return a body.")
        links = body.get('links', [])
        next_links = [link['href'] for link in links if link['rel'] == 'next']
        next_marker = None
        for link in next_links:
            # Extract the marker from the url.
            parsed_url = urlutils.urlparse(link)
            query_dict = dict(urlutils.parse_qsl(parsed_url.query))
            next_marker = query_dict.get('marker', None)
        instances = body[response_key]
        instances = [self.resource_class(self, res) for res in instances]
        return Paginated(instances, next_marker=next_marker, links=links)

    def show(self, instance):
        """
        Get details of one instance.

        :rtype: :class:`Instance`.
        """

        return self._get("/mgmt/instances/%s" % base.getid(instance),
                         'instance')

    def index(self, deleted=None, limit=None, marker=None):
        """
        Show an overview of all local instances.
        Optionally, filter by deleted status.

        :rtype: list of :class:`Instance`.
        """
        form = ''
        if deleted is not None:
            if deleted:
                form = "?deleted=true"
            else:
                form = "?deleted=false"

        url = "/mgmt/instances%s" % form
        return self._list(url, "instances", limit, marker)

    def root_enabled_history(self, instance):
        """
        Get root access history of one instance.

        """
        url = "/mgmt/instances/%s/root" % base.getid(instance)
        resp, body = self.api.client.get(url)
        if not body:
            raise Exception("Call to " + url + " did not return a body.")
        return RootHistory(self, body['root_history'])

    def _action(self, instance_id, body):
        """
        Perform a server "action" -- reboot/rebuild/resize/etc.
        """
        url = "/mgmt/instances/%s/action" % instance_id
        resp, body = self.api.client.post(url, body=body)
        check_for_exceptions(resp, body)

    def stop(self, instance_id):
        body = {'stop': {}}
        self._action(instance_id, body)

    def reboot(self, instance_id):
        """
        Reboot the underlying OS.

        :param instance_id: The :class:`Instance` (or its ID) to share onto.
        """
        body = {'reboot': {}}
        self._action(instance_id, body)

    def migrate(self, instance_id, host=None):
        """
        Migrate the instance.

        :param instance_id: The :class:`Instance` (or its ID) to share onto.
        """
        if host:
            body = {'migrate': {'host': host}}
        else:
            body = {'migrate': {}}
        self._action(instance_id, body)

    def update(self, instance_id):
        """
        Update the guest agent via apt-get.
        """
        body = {'update': {}}
        self._action(instance_id, body)

    def reset_task_status(self, instance_id):
        """
        Set the task status to NONE.
        """
        body = {'reset-task-status': {}}
        self._action(instance_id, body)


class MgmtFlavors(base.ManagerWithFind):
    """
    Manage :class:`Flavor` resources.
    """
    resource_class = Flavor

    def __repr__(self):
        return "<Flavors Manager at %s>" % id(self)

    # Appease the abc gods
    def list(self):
        pass

    def create(self, name, ram, disk, vcpus,
               flavorid="auto", ephemeral=None, swap=None, rxtx_factor=None,
               service_type=None):
        """
        Create a new flavor.
        """
        body = {"flavor": {
            "flavor_id": flavorid,
            "name": name,
            "ram": ram,
            "disk": disk,
            "vcpu": vcpus,
            "ephemeral": 0,
            "swap": 0,
            "rxtx_factor": "1.0",
            "is_public": "True"
        }}
        if ephemeral:
            body["flavor"]["ephemeral"] = ephemeral
        if swap:
            body["flavor"]["swap"] = swap
        if rxtx_factor:
            body["flavor"]["rxtx_factor"] = rxtx_factor
        if service_type:
            body["flavor"]["service_type"] = service_type

        return self._create("/mgmt/flavors", body, "flavor")
