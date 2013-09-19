# Copyright (c) 2011 OpenStack Foundation
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
import exceptions


class Backup(base.Resource):
    """
    Backup is a resource used to hold backup information.
    """
    def __repr__(self):
        return "<Backup: %s>" % self.name


class Backups(base.ManagerWithFind):
    """
    Manage :class:`Backups` information.
    """

    resource_class = Backup

    def get(self, backup):
        """
        Get a specific backup.

        :rtype: :class:`Backups`
        """
        return self._get("/backups/%s" % base.getid(backup),
                         "backup")

    def list(self, limit=None, marker=None):
        """
        Get a list of all backups.

        :rtype: list of :class:`Backups`.
        """
        return self._list("/backups", "backups", limit, marker)

    def create(self, name, instance, description=None):
        """
        Create a new backup from the given instance.
        """
        body = {
            "backup": {
                "name": name,
                "instance": instance
            }
        }
        if description:
            body['backup']['description'] = description
        return self._create("/backups", body, "backup")

    def delete(self, backup_id):
        """
        Delete the specified backup.

        :param backup_id: The backup id to delete
        """
        resp, body = self.api.client.delete("/backups/%s" % backup_id)
        if resp.status in (422, 500):
            raise exceptions.from_response(resp, body)
