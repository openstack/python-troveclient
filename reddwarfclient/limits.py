# Copyright (c) 2013 OpenStack, LLC.
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


class Limits(base.ManagerWithFind):
    """
    Manages :class `Limit` resources
    """
    resource_class = base.Resource

    def index(self):
        """
        Retrieve the limits
        """
        RESPONSE_KEY = "limits"
        URL = "/limits"
        resp, body = self.api.client.get(URL)

        if resp is None or resp.status != 200:
            raise exceptions.from_response(resp, body)

        if not body:
            raise Exception("Call to " + URL + " did not return a body.")

        rates = body[RESPONSE_KEY]['rate'][0]['limit']
        return [self.resource_class(self, res) for res in rates]
