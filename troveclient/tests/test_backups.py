# Copyright 2013 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
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

import mock
from mock import patch
import testtools
import uuid

from troveclient.v1 import backups

"""
Unit tests for backups.py
"""


class BackupTest(testtools.TestCase):

    def setUp(self):
        super(BackupTest, self).setUp()
        self.backup_id = str(uuid.uuid4())
        self.info = {'name': 'my backup', 'id': self.backup_id}
        self.api = mock.Mock()
        self.manager = backups.Backups(self.api)
        self.backup = backups.Backup(self.manager, self.info)

    def tearDown(self):
        super(BackupTest, self).tearDown()

    def test___repr__(self):
        self.assertEqual('<Backup: my backup>', repr(self.backup))


class BackupManagerTest(testtools.TestCase):

    def setUp(self):
        super(BackupManagerTest, self).setUp()
        self.backups = backups.Backups(mock.Mock())
        self.instance_with_id = mock.Mock()
        self.instance_with_id.id = 215

    def tearDown(self):
        super(BackupManagerTest, self).tearDown()

    def test_create(self):
        create_mock = mock.Mock()
        self.backups._create = create_mock
        args = {'name': 'test_backup', 'instance': '1', 'incremental': False}
        body = {'backup': args}
        self.backups.create(**args)
        create_mock.assert_called_with('/backups', body, 'backup')

    def test_create_description(self):
        create_mock = mock.Mock()
        self.backups._create = create_mock
        args = {'name': 'test_backup', 'instance': '1', 'description': 'foo',
                'incremental': False}
        body = {'backup': args}
        self.backups.create(**args)
        create_mock.assert_called_with('/backups', body, 'backup')

    def test_create_with_instance_obj(self):
        create_mock = mock.Mock()
        self.backups._create = create_mock
        args = {'name': 'test_backup', 'instance': self.instance_with_id.id,
                'incremental': False}
        body = {'backup': args}
        self.backups.create('test_backup', self.instance_with_id)
        create_mock.assert_called_with('/backups', body, 'backup')

    def test_create_incremental(self):
        create_mock = mock.Mock()
        self.backups._create = create_mock
        args = {'name': 'test_backup', 'instance': '1', 'parent_id': 'foo',
                'incremental': False}
        body = {'backup': args}
        self.backups.create(**args)
        create_mock.assert_called_with('/backups', body, 'backup')

    def test_create_incremental_2(self):
        create_mock = mock.Mock()
        self.backups._create = create_mock
        args = {'name': 'test_backup', 'instance': '1', 'incremental': True}
        body = {'backup': args}
        self.backups.create(**args)
        create_mock.assert_called_with('/backups', body, 'backup')

    def test_list(self):
        page_mock = mock.Mock()
        self.backups._paginated = page_mock
        limit = "test-limit"
        marker = "test-marker"
        self.backups.list(limit, marker)
        page_mock.assert_called_with("/backups", "backups", limit, marker, {})

    def test_list_by_datastore(self):
        page_mock = mock.Mock()
        self.backups._paginated = page_mock
        limit = "test-limit"
        marker = "test-marker"
        datastore = "test-mysql"
        self.backups.list(limit, marker, datastore)
        page_mock.assert_called_with("/backups", "backups", limit, marker,
                                     {'datastore': datastore})

    def test_list_by_instance(self):
        page_mock = mock.Mock()
        self.backups._paginated = page_mock
        instance_id = "fake_instance"

        self.backups.list(instance_id=instance_id)

        page_mock.assert_called_with("/backups", "backups", None, None,
                                     {'instance_id': instance_id})

    def test_list_by_all_projects(self):
        page_mock = mock.Mock()
        self.backups._paginated = page_mock
        all_projects = True

        self.backups.list(all_projects=all_projects)

        page_mock.assert_called_with("/backups", "backups", None, None,
                                     {'all_projects': all_projects})

    def test_get(self):
        get_mock = mock.Mock()
        self.backups._get = get_mock
        self.backups.get(1)
        get_mock.assert_called_with('/backups/1', 'backup')

    def test_delete(self):
        resp = mock.Mock()
        resp.status_code = 200
        delete_mock = mock.Mock(return_value=(resp, None))
        self.backups.api.client.delete = delete_mock
        self.backups.delete('backup1')
        delete_mock.assert_called_with('/backups/backup1')

    def test_delete_500(self):
        resp = mock.Mock()
        resp.status_code = 500
        self.backups.api.client.delete = mock.Mock(return_value=(resp, None))
        self.assertRaises(Exception, self.backups.delete, 'backup1')

    def test_delete_422(self):
        resp = mock.Mock()
        resp.status_code = 422
        self.backups.api.client.delete = mock.Mock(return_value=(resp, None))
        self.assertRaises(Exception, self.backups.delete, 'backup1')

    @patch('troveclient.v1.backups.mistral_client')
    def test_auth_mistral_client(self, mistral_client):
        with patch.object(self.backups.api.client, 'auth') as auth:
            self.backups._get_mistral_client()
            mistral_client.assert_called_with(
                auth_url=auth.auth_url, username=auth._username,
                api_key=auth._password,
                project_name=auth._project_name)

    def test_build_schedule(self):
        cron_trigger = mock.Mock()
        wf_input = {'name': 'foo', 'instance': 'myinst', 'parent_id': None}
        sched = self.backups._build_schedule(cron_trigger, wf_input)
        self.assertEqual(cron_trigger.name, sched.id)
        self.assertEqual(wf_input['name'], sched.name)
        self.assertEqual(wf_input['instance'], sched.instance)
        self.assertEqual(cron_trigger.workflow_input, sched.input)

    def test_schedule_create(self):
        instance = mock.Mock()
        pattern = mock.Mock()
        name = 'myback'

        def make_cron_trigger(name, wf, workflow_input=None, pattern=None):
            return mock.Mock(name=name, pattern=pattern,
                             workflow_input=workflow_input)
        cron_triggers = mock.Mock()
        cron_triggers.create = mock.Mock(side_effect=make_cron_trigger)
        mistral_client = mock.Mock(cron_triggers=cron_triggers)

        sched = self.backups.schedule_create(instance, pattern, name,
                                             mistral_client=mistral_client)
        self.assertEqual(pattern, sched.pattern)
        self.assertEqual(name, sched.name)
        self.assertEqual(instance.id, sched.instance)

    def test_schedule_list(self):
        instance = mock.Mock(id='the_uuid')
        backup_name = "wf2"

        test_input = [('wf1', 'foo'), (backup_name, instance.id)]
        cron_triggers = mock.Mock()
        cron_triggers.list = mock.Mock(
            return_value=[
                mock.Mock(workflow_input='{"name": "%s", "instance": "%s"}'
                          % (name, inst), name=name)
                for name, inst in test_input
            ])
        mistral_client = mock.Mock(cron_triggers=cron_triggers)

        sched_list = self.backups.schedule_list(instance, mistral_client)
        self.assertEqual(1, len(sched_list))
        the_sched = sched_list.pop()
        self.assertEqual(backup_name, the_sched.name)
        self.assertEqual(instance.id, the_sched.instance)

    def test_schedule_show(self):
        instance = mock.Mock(id='the_uuid')
        backup_name = "myback"

        cron_triggers = mock.Mock()
        cron_triggers.get = mock.Mock(
            return_value=mock.Mock(
                name=backup_name,
                workflow_input='{"name": "%s", "instance": "%s"}'
                % (backup_name, instance.id)))
        mistral_client = mock.Mock(cron_triggers=cron_triggers)

        sched = self.backups.schedule_show("dummy", mistral_client)
        self.assertEqual(backup_name, sched.name)
        self.assertEqual(instance.id, sched.instance)

    def test_schedule_delete(self):
        cron_triggers = mock.Mock()
        cron_triggers.delete = mock.Mock()
        mistral_client = mock.Mock(cron_triggers=cron_triggers)
        self.backups.schedule_delete("dummy", mistral_client)
        cron_triggers.delete.assert_called()

    def test_execution_list(self):
        instance = mock.Mock(id='the_uuid')
        wf_input = '{"name": "wf2", "instance": "%s"}' % instance.id
        wf_name = self.backups.backup_create_workflow

        execution_list_result = [
            [mock.Mock(id=1, input=wf_input, workflow_name=wf_name,
                       to_dict=mock.Mock(return_value={'id': 1})),
             mock.Mock(id=2, input="{}", workflow_name=wf_name)],
            [mock.Mock(id=3, input=wf_input, workflow_name=wf_name,
                       to_dict=mock.Mock(return_value={'id': 3})),
             mock.Mock(id=4, input="{}", workflow_name=wf_name)],
            [mock.Mock(id=5, input=wf_input, workflow_name=wf_name,
                       to_dict=mock.Mock(return_value={'id': 5})),
             mock.Mock(id=6, input="{}", workflow_name=wf_name)],
            [mock.Mock(id=7, input=wf_input, workflow_name="bar"),
             mock.Mock(id=8, input="{}", workflow_name=wf_name)]
        ]

        cron_triggers = mock.Mock()
        cron_triggers.get = mock.Mock(
            return_value=mock.Mock(workflow_name=wf_name,
                                   workflow_input=wf_input))

        mistral_executions = mock.Mock()
        mistral_executions.list = mock.Mock(side_effect=execution_list_result)
        mistral_client = mock.Mock(cron_triggers=cron_triggers,
                                   executions=mistral_executions)

        el = self.backups.execution_list("dummy", mistral_client, limit=2)
        self.assertEqual(2, len(el))
        el = self.backups.execution_list("dummy", mistral_client, limit=2)
        self.assertEqual(1, len(el))
        the_exec = el.pop()
        self.assertEqual(5, the_exec.id)

    def test_execution_delete(self):
        mistral_executions = mock.Mock()
        mistral_executions.delete = mock.Mock()
        mistral_client = mock.Mock(executions=mistral_executions)
        self.backups.execution_delete("dummy", mistral_client)
        mistral_executions.delete.assert_called()
