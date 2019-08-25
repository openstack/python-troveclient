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

import json
import six
import uuid

from mistralclient.api.client import client as mistral_client

from troveclient import base
from troveclient import common


class Backup(base.Resource):
    """Backup is a resource used to hold backup information."""
    def __repr__(self):
        return "<Backup: %s>" % self.name


class Schedule(base.Resource):
    """Schedule is a resource used to hold information about scheduled backups.
    """
    def __repr__(self):
        return "<Schedule: %s>" % self.name


class ScheduleExecution(base.Resource):
    """ScheduleExecution is a resource used to hold information about
    the execution of a scheduled backup.
    """
    def __repr__(self):
        return "<Execution: %s>" % self.name


class Backups(base.ManagerWithFind):
    """Manage :class:`Backups` information."""

    resource_class = Backup

    def get(self, backup):
        """Get a specific backup.

        :rtype: :class:`Backups`
        """
        return self._get("/backups/%s" % base.getid(backup),
                         "backup")

    def list(self, limit=None, marker=None, datastore=None, instance_id=None,
             all_projects=False):
        """Get a list of all backups."""
        query_strings = {}
        if datastore:
            query_strings["datastore"] = datastore
        if instance_id:
            query_strings["instance_id"] = instance_id
        if all_projects:
            query_strings["all_projects"] = True

        return self._paginated("/backups", "backups", limit, marker,
                               query_strings)

    def create(self, name, instance, description=None,
               parent_id=None, incremental=False):
        """Create a new backup from the given instance.

        :param name: name for backup.
        :param instance: instance to backup.
        :param description: (optional).
        :param parent_id: base for incremental backup (optional).
        :param incremental: flag to indicate incremental backup based on
                            last backup
        :returns: :class:`Backups`
        """
        body = {
            "backup": {
                "name": name,
                "incremental": int(incremental)
            }
        }

        if instance:
            body['backup']['instance'] = base.getid(instance)
        if description:
            body['backup']['description'] = description
        if parent_id:
            body['backup']['parent_id'] = parent_id
        return self._create("/backups", body, "backup")

    def delete(self, backup):
        """Delete the specified backup.

        :param backup: The backup to delete
        """
        url = "/backups/%s" % base.getid(backup)
        resp, body = self.api.client.delete(url)
        common.check_for_exceptions(resp, body, url)

    backup_create_workflow = "trove.backup_create"

    def _get_mistral_client(self):
        if hasattr(self.api.client, 'auth'):
            auth_url = self.api.client.auth.auth_url
            user = self.api.client.auth._username
            key = self.api.client.auth._password
            tenant_name = self.api.client.auth._project_name
        else:
            auth_url = self.api.client.auth_url
            user = self.api.client.user
            key = self.api.client.password
            tenant_name = self.api.client.projectid

        return mistral_client(auth_url=auth_url, username=user, api_key=key,
                              project_name=tenant_name)

    def _build_schedule(self, cron_trigger, wf_input):
        if isinstance(wf_input, six.string_types):
            wf_input = json.loads(wf_input)
        sched_info = {"id": cron_trigger.name,
                      "name": wf_input["name"],
                      "instance": wf_input['instance'],
                      "parent_id": wf_input.get('parent_id', None),
                      "created_at": cron_trigger.created_at,
                      "next_execution_time": cron_trigger.next_execution_time,
                      "pattern": cron_trigger.pattern,
                      "input": cron_trigger.workflow_input
                      }
        if hasattr(cron_trigger, 'updated_at'):
            sched_info["updated_at"] = cron_trigger.updated_at
        return Schedule(self, sched_info, loaded=True)

    def schedule_create(self, instance, pattern, name,
                        description=None, incremental=None,
                        mistral_client=None):
        """Create a new schedule to backup the given instance.

        :param instance: instance to backup.
        :param: pattern: cron pattern for schedule.
        :param name: name for backup.
        :param description: (optional).
        :param incremental: flag for incremental backup (optional).
        :returns: :class:`Backups`
        """

        if not mistral_client:
            mistral_client = self._get_mistral_client()

        inst_id = base.getid(instance)
        cron_name = str(uuid.uuid4())
        wf_input = {"instance": inst_id,
                    "name": name,
                    "description": description,
                    "incremental": incremental
                    }

        cron_trigger = mistral_client.cron_triggers.create(
            cron_name, self.backup_create_workflow, pattern=pattern,
            workflow_input=wf_input)

        return self._build_schedule(cron_trigger, wf_input)

    def schedule_list(self, instance, mistral_client=None):
        """Get a list of all backup schedules for an instance.

        :param: instance for which to list schedules.
        :rtype: list of :class:`Schedule`.
        """
        inst_id = base.getid(instance)
        if not mistral_client:
            mistral_client = self._get_mistral_client()

        return [self._build_schedule(cron_trig, cron_trig.workflow_input)
                for cron_trig in mistral_client.cron_triggers.list()
                if inst_id in cron_trig.workflow_input]

    def schedule_show(self, schedule, mistral_client=None):
        """Get details of a backup schedule.

        :param: schedule to show.
        :rtype: :class:`Schedule`.
        """
        if isinstance(schedule, Schedule):
            schedule = schedule.id

        if not mistral_client:
            mistral_client = self._get_mistral_client()

        schedule = mistral_client.cron_triggers.get(schedule)
        return self._build_schedule(schedule, schedule.workflow_input)

    def schedule_delete(self, schedule, mistral_client=None):
        """Remove a given backup schedule.

        :param schedule: schedule to delete.
        """

        if isinstance(schedule, Schedule):
            schedule = schedule.id

        if not mistral_client:
            mistral_client = self._get_mistral_client()

        mistral_client.cron_triggers.delete(schedule)

    def execution_list(self, schedule, mistral_client=None,
                       marker='', limit=None):
        """Get a list of all executions of a scheduled backup.

        :param: schedule for which to list executions.
        :rtype: list of :class:`ScheduleExecution`.
        """

        if isinstance(schedule, Schedule):
            schedule = schedule.id

        if isinstance(marker, ScheduleExecution):
            marker = getattr(marker, 'id')

        if not mistral_client:
            mistral_client = self._get_mistral_client()

        cron_trigger = mistral_client.cron_triggers.get(schedule)
        ct_input = json.loads(cron_trigger.workflow_input)

        def mistral_execution_generator():
            m = marker
            while True:
                try:
                    the_list = mistral_client.executions.list(
                        marker=m, limit=50,
                        sort_dirs='desc'
                    )
                    if the_list:
                        for the_item in the_list:
                            yield the_item
                        m = the_list[-1].id
                    else:
                        return
                except StopIteration:
                    return

        def execution_list_generator():
            yielded = 0
            for sexec in mistral_execution_generator():
                if (sexec.workflow_name == cron_trigger.workflow_name and
                        ct_input == json.loads(sexec.input)):
                    yield ScheduleExecution(self, sexec.to_dict(),
                                            loaded=True)
                    yielded += 1
                if limit and yielded == limit:
                    return

        return list(execution_list_generator())

    def execution_delete(self, execution, mistral_client=None):
        """Remove a given schedule execution.

        :param id: id of execution to remove.
        """

        exec_id = (execution.id if isinstance(execution, ScheduleExecution)
                   else execution)

        if isinstance(execution, ScheduleExecution):
            execution = execution.name

        if not mistral_client:
            mistral_client = self._get_mistral_client()

        mistral_client.executions.delete(exec_id)
