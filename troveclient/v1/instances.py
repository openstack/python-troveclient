# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

import warnings

from troveclient import base
from troveclient import common
from troveclient import exceptions
from troveclient.i18n import _LW

from swiftclient import client as swift_client

REBOOT_SOFT = 'SOFT'
REBOOT_HARD = 'HARD'


class Instance(base.Resource):
    """An Instance is an opaque instance used to store Database instances."""
    def __repr__(self):
        return "<Instance: %s>" % self.name

    def list_databases(self):
        return self.manager.databases.list(self)

    def delete(self):
        """Delete the instance."""
        self.manager.delete(self)

    def restart(self):
        """Restart the database instance."""
        self.manager.restart(self.id)

    def detach_replica(self):
        """Stops the replica database from being replicated to."""
        self.manager.edit(self.id, detach_replica_source=True)


class DatastoreLog(base.Resource):
    """A DatastoreLog is a log on the database guest instance."""

    def __repr__(self):
        return "<DatastoreLog: %s>" % self.name


class Instances(base.ManagerWithFind):
    """Manage :class:`Instance` resources."""
    resource_class = Instance

    def _get_swift_client(self):
        if hasattr(self.api.client, 'auth'):
            auth_url = self.api.client.auth.auth_url
            user = self.api.client.auth._username
            key = self.api.client.auth._password
            tenant_name = self.api.client.auth._project_name
        else:
            auth_url = self.api.client.auth_url
            user = self.api.client.username
            key = self.api.client.password
            tenant_name = self.api.client.tenant
        # remove '/tokens' from the end of auth_url so it works for swift
        token_str = "/tokens"
        if auth_url.endswith(token_str):
            auth_url = auth_url[:-len(token_str)]
        region_name = self.api.client.region_name
        os_options = {'tenant_name': tenant_name, 'region_name': region_name}

        return swift_client.Connection(
            auth_url, user, key, auth_version="2.0", os_options=os_options)

    # TODO(mriedem): Remove slave_of after liberty-eol for Trove.
    def create(self, name, flavor_id, volume=None, databases=None, users=None,
               restorePoint=None, availability_zone=None, datastore=None,
               datastore_version=None, nics=None, configuration=None,
               replica_of=None, slave_of=None, replica_count=None):
        """Create (boot) a new instance."""

        body = {"instance": {
            "name": name,
            "flavorRef": flavor_id
        }}
        datastore_obj = {}
        if volume:
            body["instance"]["volume"] = volume
        if databases:
            body["instance"]["databases"] = databases
        if users:
            body["instance"]["users"] = users
        if restorePoint:
            body["instance"]["restorePoint"] = restorePoint
        if availability_zone:
            body["instance"]["availability_zone"] = availability_zone
        if datastore:
            datastore_obj["type"] = datastore
        if datastore_version:
            datastore_obj["version"] = datastore_version
        if datastore_obj:
            body["instance"]["datastore"] = datastore_obj
        if nics:
            body["instance"]["nics"] = nics
        if configuration:
            body["instance"]["configuration"] = configuration
        if replica_of or slave_of:
            if slave_of:
                warnings.warn(_LW("The 'slave_of' argument is deprecated in "
                                  "favor of 'replica_of' and will be removed "
                                  "after the Trove liberty series is end of "
                                  "life."),
                              category=DeprecationWarning)
            body["instance"]["replica_of"] = base.getid(replica_of) or slave_of
        if replica_count:
            body["instance"]["replica_count"] = replica_count

        return self._create("/instances", body, "instance")

    def modify(self, instance, configuration=None):
        body = {
            "instance": {
            }
        }
        if configuration is not None:
            body["instance"]["configuration"] = configuration
        url = "/instances/%s" % base.getid(instance)
        resp, body = self.api.client.put(url, body=body)
        common.check_for_exceptions(resp, body, url)

    def edit(self, instance, configuration=None, name=None,
             detach_replica_source=False, remove_configuration=False):
        body = {
            "instance": {
            }
        }
        if configuration and remove_configuration:
            raise Exception("Cannot attach and detach configuration "
                            "simultaneously.")
        if remove_configuration:
            body["instance"]["configuration"] = None
        if configuration is not None:
            body["instance"]["configuration"] = configuration
        if name is not None:
            body["instance"]["name"] = name
        if detach_replica_source:
            # NOTE(mriedem): We don't send slave_of since it was removed from
            # the trove API in mitaka.
            body["instance"]["replica_of"] = None

        url = "/instances/%s" % base.getid(instance)
        resp, body = self.api.client.patch(url, body=body)
        common.check_for_exceptions(resp, body, url)

    def list(self, limit=None, marker=None, include_clustered=False):
        """Get a list of all instances.

        :rtype: list of :class:`Instance`.
        """
        return self._paginated("/instances", "instances", limit, marker,
                               {"include_clustered": include_clustered})

    def get(self, instance):
        """Get a specific instances.

        :rtype: :class:`Instance`
        """
        return self._get("/instances/%s" % base.getid(instance),
                         "instance")

    def backups(self, instance, limit=None, marker=None):
        """Get the list of backups for a specific instance.

        :rtype: list of :class:`Backups`.
        """
        url = "/instances/%s/backups" % base.getid(instance)
        return self._paginated(url, "backups", limit, marker)

    def delete(self, instance):
        """Delete the specified instance.

        :param instance: A reference to the instance to delete
        """
        url = "/instances/%s" % base.getid(instance)
        resp, body = self.api.client.delete(url)
        common.check_for_exceptions(resp, body, url)

    def _action(self, instance, body):
        """Perform a server "action" -- reboot/rebuild/resize/etc."""
        url = "/instances/%s/action" % base.getid(instance)
        resp, body = self.api.client.post(url, body=body)
        common.check_for_exceptions(resp, body, url)
        if body:
            return self.resource_class(self, body, loaded=True)
        return body

    def resize_volume(self, instance, volume_size):
        """Resize the volume on an existing instances."""
        body = {"resize": {"volume": {"size": volume_size}}}
        self._action(instance, body)

    def resize_instance(self, instance, flavor_id):
        """Resizes an instance with a new flavor."""
        body = {"resize": {"flavorRef": flavor_id}}
        self._action(instance, body)

    def restart(self, instance):
        """Restart the database instance.

        :param instance: The :class:`Instance` (or its ID) of the database
        instance to restart.
        """
        body = {'restart': {}}
        self._action(instance, body)

    def configuration(self, instance):
        """Get a configuration on instances.

        :rtype: :class:`Instance`
        """
        return self._get("/instances/%s/configuration" % base.getid(instance),
                         "instance")

    def promote_to_replica_source(self, instance):
        """Promote a replica to be the new replica_source of its set

        :param instance: The :class:`Instance` (or its ID) of the database
        instance to promote.
        """
        body = {'promote_to_replica_source': {}}
        self._action(instance, body)

    def eject_replica_source(self, instance):
        """Eject a replica source from its set

        :param instance: The :class:`Instance` (or its ID) of the database
        instance to eject.
        """
        body = {'eject_replica_source': {}}
        self._action(instance, body)

    def log_list(self, instance):
        """Get a list of all guest logs.

        :param instance: The :class:`Instance` (or its ID) of the database
        instance to get the log for.
        :rtype: list of :class:`DatastoreLog`.
        """
        url = '/instances/%s/log' % base.getid(instance)
        resp, body = self.api.client.get(url)
        common.check_for_exceptions(resp, body, url)
        return [DatastoreLog(self, log, loaded=True) for log in body['logs']]

    def log_show(self, instance, log_name):
        return self._log_action(instance, log_name)

    def log_enable(self, instance, log_name):
        return self._log_action(instance, log_name, enable=True)

    def log_disable(self, instance, log_name, discard=None):
        return self._log_action(instance, log_name,
                                disable=True, discard=discard)

    def log_publish(self, instance, log_name, disable=None, discard=None):
        return self._log_action(instance, log_name, disable=disable,
                                publish=True, discard=discard)

    def log_discard(self, instance, log_name):
        return self._log_action(instance, log_name, discard=True)

    def _log_action(self, instance, log_name, enable=None, disable=None,
                    publish=None, discard=None):
        """Perform action on guest log.

        :param instance: The :class:`Instance` (or its ID) of the database
        instance to get the log for.
        :param log_name: The name of <log> to publish
        :param enable: Turn on <log>
        :param disable: Turn off <log>
        :param publish: Publish log to associated container
        :param discard: Delete the associated container
        :rtype: List of :class:`DatastoreLog`.
        """
        body = {"name": log_name}
        if enable:
            body.update({'enable': int(enable)})
        if disable:
            body.update({'disable': int(disable)})
        if publish:
            body.update({'publish': int(publish)})
        if discard:
            body.update({'discard': int(discard)})
        url = "/instances/%s/log" % base.getid(instance)
        resp, body = self.api.client.post(url, body=body)
        common.check_for_exceptions(resp, body, url)
        return DatastoreLog(self, body['log'], loaded=True)

    def _get_container_info(self, instance, log_name, publish):
        try:
            log_info = self._log_action(instance, log_name, publish=publish)
            container = log_info.container
            prefix = log_info.prefix
            metadata_file = log_info.metafile
            return container, prefix, metadata_file
        except swift_client.ClientException as ex:
            if ex.http_status == 404:
                raise exceptions.GuestLogNotFoundError()
            raise

    def log_generator(self, instance, log_name, publish=None, lines=50,
                      swift=None):
        """Return generator to yield the last <lines> lines of guest log.

        :param instance: The :class:`Instance` (or its ID) of the database
        instance to get the log for.
        :param log_name: The name of <log> to publish
        :param publish: Publish updates before displaying log
        :param lines: Display last <lines> lines of log (0 for all lines)
        :param swift: Connection to swift
        :rtype: generator function to yield log as chunks.
        """

        if not swift:
            swift = self._get_swift_client()

        def _log_generator(instance, log_name, publish, lines, swift):
            try:
                container, prefix, metadata_file = self._get_container_info(
                    instance, log_name, publish)
                head, body = swift.get_container(container, prefix=prefix)
                log_obj_to_display = []
                if lines:
                    total_lines = lines
                    partial_results = False
                    parts = sorted(body, key=lambda obj: obj['last_modified'],
                                   reverse=True)
                    for part in parts:
                        obj_hdrs = swift.head_object(container, part['name'])
                        obj_lines = int(obj_hdrs['x-object-meta-lines'])
                        log_obj_to_display.insert(0, part)
                        if obj_lines >= lines:
                            partial_results = True
                            break
                        lines -= obj_lines
                    if not partial_results:
                        lines = total_lines
                    part = log_obj_to_display.pop(0)
                    hdrs, log_obj = swift.get_object(container, part['name'])
                    log_by_lines = log_obj.splitlines()
                    yield "\n".join(log_by_lines[-1 * lines:]) + "\n"
                else:
                    log_obj_to_display = sorted(
                        body, key=lambda obj: obj['last_modified'])
                for log_part in log_obj_to_display:
                    headers, log_obj = swift.get_object(container,
                                                        log_part['name'])
                    yield log_obj
            except swift_client.ClientException as ex:
                if ex.http_status == 404:
                    raise exceptions.GuestLogNotFoundError()
                raise

        return lambda: _log_generator(instance, log_name, publish,
                                      lines, swift)

    def log_save(self, instance, log_name, publish=None, filename=None):
        """Saves a guest log to a file.

        :param instance: The :class:`Instance` (or its ID) of the database
        instance to get the log for.
        :param log_name: The name of <log> to publish
        :param publish: Publish updates before displaying log
        :rtype: Filename to which log was saved
        """
        written_file = filename or (instance.name + '-' + log_name + ".log")
        log_gen = self.log_generator(instance, log_name, publish, 0)
        with open(written_file, 'w') as f:
            for log_obj in log_gen():
                f.write(log_obj)
        return written_file


class InstanceStatus(object):

    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    BUILD = "BUILD"
    FAILED = "FAILED"
    REBOOT = "REBOOT"
    RESIZE = "RESIZE"
    SHUTDOWN = "SHUTDOWN"
    RESTART_REQUIRED = "RESTART_REQUIRED"
    PROMOTING = "PROMOTING"
    EJECTING = "EJECTING"
    LOGGING = "LOGGING"
