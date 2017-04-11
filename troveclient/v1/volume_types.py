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

from troveclient import base


class VolumeType(base.Resource):
    """A VolumeType is an Cinder volume type."""

    def __init__(self, manager, info, loaded=False):
        super(VolumeType, self).__init__(manager, info, loaded)
        if self.id is None and self.str_id is not None:
            self.id = self.str_id

    def __repr__(self):
        return "<VolumeType: %s>" % self.name


class VolumeTypes(base.ManagerWithFind):
    """Manage :class:`VolumeType` resources."""
    resource_class = VolumeType

    def list(self):
        """Get a list of all volume-types.
        :rtype: list of :class:`VolumeType`.
        """
        return self._list("/volume-types", "volume_types")

    def list_datastore_version_associated_volume_types(self, datastore,
                                                       version_id):
        """Get a list of all volume-types for the specified datastore type
        and datastore version .
        :rtype: list of :class:`VolumeType`.
        """
        return self._list("/datastores/%s/versions/%s/volume-types" %
                          (datastore, version_id),
                          "volume_types")

    def get(self, volume_type):
        """Get a specific volume-type.

        :rtype: :class:`VolumeType`
        """
        return self._get("/volume-types/%s" % base.getid(volume_type),
                         "volume_type")
