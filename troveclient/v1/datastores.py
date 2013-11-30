# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack Foundation
# Copyright 2013 Mirantis, Inc.
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


class Datastore(base.Resource):

    def __repr__(self):
        return "<Datastore: %s>" % self.name


class DatastoreVersion(base.Resource):

    def __repr__(self):
        return "<DatastoreVersion: %s>" % self.name


class Datastores(base.ManagerWithFind):
    """
    Manage :class:`Datastore` resources.
    """
    resource_class = Datastore

    def __repr__(self):
        return "<Datastore Manager at %s>" % id(self)

    def list(self, limit=None, marker=None):
        """
        Get a list of all datastores.

        :rtype: list of :class:`Datastore`.
        """
        return self._list("/datastores", "datastores", limit, marker)

    def get(self, datastore):
        """
        Get a specific datastore.

        :rtype: :class:`Datastore`
        """
        return self._get("/datastores/%s" % base.getid(datastore),
                         "datastore")


class DatastoreVersions(base.ManagerWithFind):
    """
    Manage :class:`DatastoreVersion` resources.
    """
    resource_class = DatastoreVersion

    def __repr__(self):
        return "<DatastoreVersions Manager at %s>" % id(self)

    def list(self, datastore, limit=None, marker=None):
        """
        Get a list of all datastore versions.

        :rtype: list of :class:`DatastoreVersion`.
        """
        return self._list("/datastores/%s/versions" % datastore,
                          "versions", limit, marker)

    def get(self, datastore, datastore_version):
        """
        Get a specific datastore version.

        :rtype: :class:`DatastoreVersion`
        """
        return self._get("/datastores/%s/versions/%s" %
                         (datastore, base.getid(datastore_version)),
                         "version")
