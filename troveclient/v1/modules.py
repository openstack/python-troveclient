# Copyright 2016 Tesora, Inc.
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
#

import base64

from troveclient import base
from troveclient import common


class Module(base.Resource):

    NO_CHANGE_TO_ARG = 'no_change_to_argument'

    def __repr__(self):
        return "<Module: %s>" % self.name


class Modules(base.ManagerWithFind):
    """Manage :class:`Module` resources."""
    resource_class = Module

    def _encode_string(self, data_str):
        byte_array = bytearray(data_str, 'utf-8')
        return base64.b64encode(byte_array)

    def create(self, name, module_type, contents, description=None,
               all_tenants=None, datastore=None,
               datastore_version=None, auto_apply=None,
               visible=None, live_update=None):
        """Create a new module."""

        contents = self._encode_string(contents)
        body = {"module": {
            "name": name,
            "module_type": module_type,
            "contents": contents,
        }}
        if description is not None:
            body["module"]["description"] = description
        datastore_obj = {}
        if datastore:
            datastore_obj["type"] = datastore
        if datastore_version:
            datastore_obj["version"] = datastore_version
        if datastore_obj:
            body["module"]["datastore"] = datastore_obj
        if all_tenants is not None:
            body["module"]["all_tenants"] = int(all_tenants)
        if auto_apply is not None:
            body["module"]["auto_apply"] = int(auto_apply)
        if visible is not None:
            body["module"]["visible"] = int(visible)
        if live_update is not None:
            body["module"]["live_update"] = int(live_update)

        return self._create("/modules", body, "module")

    def update(self, module, name=None, module_type=None,
               contents=None, description=None,
               all_tenants=None, datastore=Module.NO_CHANGE_TO_ARG,
               datastore_version=Module.NO_CHANGE_TO_ARG, auto_apply=None,
               visible=None, live_update=None):
        """Update an existing module. Passing in
        datastore=None or datastore_version=None has the effect of
        making it available for all datastores/versions.
        """
        body = {
            "module": {
            }
        }
        if name is not None:
            body["module"]["name"] = name
        if module_type is not None:
            body["module"]["type"] = module_type
        if contents is not None:
            contents = self._encode_string(contents)
            body["module"]["contents"] = contents
        if description is not None:
            body["module"]["description"] = description
        datastore_obj = {}
        if datastore is None or datastore != Module.NO_CHANGE_TO_ARG:
            datastore_obj["type"] = datastore
        if (datastore_version is None or
                datastore_version != Module.NO_CHANGE_TO_ARG):
            datastore_obj["version"] = datastore_version
        if datastore_obj:
            body["module"]["datastore"] = datastore_obj
        if all_tenants is not None:
            body["module"]["all_tenants"] = int(all_tenants)
        if auto_apply is not None:
            body["module"]["auto_apply"] = int(auto_apply)
        if visible is not None:
            body["module"]["visible"] = int(visible)
        if live_update is not None:
            body["module"]["live_update"] = int(live_update)

        url = "/modules/%s" % base.getid(module)
        resp, body = self.api.client.put(url, body=body)
        common.check_for_exceptions(resp, body, url)
        return Module(self, body['module'], loaded=True)

    def list(self, limit=None, marker=None, datastore=None):
        """Get a list of all modules."""
        query_strings = None
        if datastore:
            query_strings = {"datastore": datastore}
        return self._paginated(
            "/modules", "modules", limit, marker, query_strings=query_strings)

    def get(self, module):
        """Get a specific module."""
        return self._get(
            "/modules/%s" % base.getid(module), "module")

    def delete(self, module):
        """Delete the specified module."""
        url = "/modules/%s" % base.getid(module)
        resp, body = self.api.client.delete(url)
        common.check_for_exceptions(resp, body, url)
