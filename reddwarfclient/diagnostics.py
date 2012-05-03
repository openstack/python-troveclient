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


class Diagnostics(base.Resource):
    """
    Account is an opaque instance used to hold account information.
    """
    def __repr__(self):
        return "<Diagnostics: %s>" % self.version


class Interrogator(base.ManagerWithFind):
    """
    Manager class for Interrogator resource
    """
    resource_class = Diagnostics
    url = "/mgmt/instances/%s/diagnostics"

    def get(self, instance_id):
        """
        Get the diagnostics of the guest on the instance.
        """
        return self._get(self.url % base.getid(instance_id), "diagnostics")
