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

from troveclient import base
from troveclient import common
from troveclient import utils


class Module(base.Resource):

    ALL_KEYWORD = 'all'

    def __repr__(self):
        return "<Module: %s>" % self.name

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False


class Modules(base.ManagerWithFind):
    """Manage :class:`Module` resources."""
    resource_class = Module

    def create(self, name, module_type, contents, description=None,
               all_tenants=None, datastore=None,
               datastore_version=None, auto_apply=None,
               visible=None, live_update=None,
               priority_apply=None, apply_order=None,
               full_access=None):
        """Create a new module."""

        contents = utils.encode_data(contents)
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
        if priority_apply is not None:
            body["module"]["priority_apply"] = int(priority_apply)
        if apply_order is not None:
            body["module"]["apply_order"] = apply_order
        if full_access is not None:
            body["module"]["full_access"] = int(full_access)

        return self._create("/modules", body, "module")

    def update(self, module, name=None, module_type=None,
               contents=None, description=None,
               all_tenants=None, datastore=None,
               datastore_version=None, auto_apply=None,
               visible=None, live_update=None,
               all_datastores=None, all_datastore_versions=None,
               priority_apply=None, apply_order=None,
               full_access=None):
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
            contents = utils.encode_data(contents)
            body["module"]["contents"] = contents
        if description is not None:
            body["module"]["description"] = description
        datastore_obj = {}
        if datastore:
            datastore_obj["type"] = datastore
        if datastore_version:
            datastore_obj["version"] = datastore_version
        if datastore_obj:
            body["module"]["datastore"] = datastore_obj
        if all_datastores:
            body["module"]["all_datastores"] = int(all_datastores)
        if all_datastore_versions:
            body["module"]["all_datastore_versions"] = int(
                all_datastore_versions)
        if all_tenants is not None:
            body["module"]["all_tenants"] = int(all_tenants)
        if auto_apply is not None:
            body["module"]["auto_apply"] = int(auto_apply)
        if visible is not None:
            body["module"]["visible"] = int(visible)
        if live_update is not None:
            body["module"]["live_update"] = int(live_update)
        if priority_apply is not None:
            body["module"]["priority_apply"] = int(priority_apply)
        if apply_order is not None:
            body["module"]["apply_order"] = apply_order
        if full_access is not None:
            body["module"]["full_access"] = int(full_access)

        url = "/modules/%s" % base.getid(module)
        resp, body = self.api.client.put(url, body=body)
        common.check_for_exceptions(resp, body, url)
        return Module(self, body['module'], loaded=True)

    def list(self, limit=None, marker=None, datastore=None):
        """Get a list of all modules."""
        query_strings = None
        if datastore:
            query_strings = {"datastore": base.getid(datastore)}
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

    def instances(self, module, limit=None, marker=None,
                  include_clustered=False, count_only=False):
        """Get a list of all instances this module has been applied to."""
        url = "/modules/%s/instances" % base.getid(module)
        query_strings = {}
        if include_clustered:
            query_strings['include_clustered'] = include_clustered
        if count_only:
            query_strings['count_only'] = count_only
        return self._paginated(url, "instances", limit, marker,
                               query_strings=query_strings)

    def reapply(self, module, md5=None, include_clustered=None,
                batch_size=None, delay=None, force=None):
        """Reapplies the specified module."""
        url = "/modules/%s/instances" % base.getid(module)
        body = {
            "reapply": {
            }
        }
        if md5:
            body["reapply"]["md5"] = md5
        if include_clustered is not None:
            body["reapply"]["include_clustered"] = int(include_clustered)
        if batch_size is not None:
            body["reapply"]["batch_size"] = batch_size
        if delay is not None:
            body["reapply"]["batch_delay"] = delay
        if force is not None:
            body["reapply"]["force"] = int(force)
        resp, body = self.api.client.put(url, body=body)
        common.check_for_exceptions(resp, body, url)
