# Copyright (c) 2012 OpenStack, LLC.
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

import exceptions

from reddwarfclient.common import check_for_exceptions


class Flavor(base.Resource):
    """
    A Flavor is an Instance type, specifying among other things, RAM size.
    """
    def __repr__(self):
        return "<Flavor: %s>" % self.name


class Flavors(base.ManagerWithFind):
    """
    Manage :class:`Flavor` resources.
    """
    resource_class = Flavor

    def __repr__(self):
        return "<Flavors Manager at %s>" % id(self)

    def _list(self, url, response_key):
        resp, body = self.api.client.get(url)
        if not body:
            raise Exception("Call to " + url + " did not return a body.")
        return [self.resource_class(self, res) for res in body[response_key]]

    def list(self):
        """
        Get a list of all flavors.

        :rtype: list of :class:`Flavor`.
        """
        return self._list("/flavors", "flavors")

    def get(self, flavor):
        """
        Get a specific flavor.

        :rtype: :class:`Flavor`
        """
        return self._get("/flavors/%s" % base.getid(flavor),
                        "flavor")
