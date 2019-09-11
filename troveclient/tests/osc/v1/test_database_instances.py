#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import mock

from osc_lib import exceptions
from osc_lib import utils
from oslo_utils import uuidutils

from troveclient import common
from troveclient.osc.v1 import database_instances
from troveclient.tests.osc.v1 import fakes


class TestInstances(fakes.TestDatabasev1):
    def setUp(self):
        super(TestInstances, self).setUp()

        self.fake_instances = fakes.FakeInstances()
        self.instance_client = self.app.client_manager.database.instances
        self.mgmt_client = self.app.client_manager.database.mgmt_instances


class TestInstanceList(TestInstances):
    defaults = {
        'include_clustered': False,
        'limit': None,
        'marker': None
    }

    def setUp(self):
        super(TestInstanceList, self).setUp()
        self.cmd = database_instances.ListDatabaseInstances(self.app, None)
        self.data = self.fake_instances.get_instances()

    def test_instance_list_defaults(self):
        self.instance_client.list.return_value = common.Paginated(self.data)

        parsed_args = self.check_parser(self.cmd, [], [])
        columns, data = self.cmd.take_action(parsed_args)

        self.instance_client.list.assert_called_once_with(**self.defaults)
        self.assertEqual(
            database_instances.ListDatabaseInstances.columns,
            columns
        )

        values = [
            ('1234', 'test-member-1', 'mysql', '5.6', 'ACTIVE', '02', 2,
             'regionOne'),
            ('5678', 'test-member-2', 'mysql', '5.6', 'ACTIVE', '2', 2,
             'regionOne')
        ]
        self.assertEqual(values, data)

    def test_instance_list_all_projects(self):
        self.mgmt_client.list.return_value = common.Paginated(self.data)

        parsed_args = self.check_parser(self.cmd, ["--all-projects"],
                                        [("all_projects", True)])
        columns, instances = self.cmd.take_action(parsed_args)

        self.mgmt_client.list.assert_called_once_with(**self.defaults)
        self.assertEqual(
            database_instances.ListDatabaseInstances.admin_columns,
            columns
        )

        expected_instances = [
            ('1234', 'test-member-1', 'fake_tenant_id', 'mysql', '5.6',
             'ACTIVE', '02', 2),
            ('5678', 'test-member-2', 'fake_tenant_id', 'mysql', '5.6',
             'ACTIVE', '2', 2)
        ]
        self.assertEqual(expected_instances, instances)


class TestInstanceShow(TestInstances):
    values = ('mysql', '5.6', '02', '1234', '10.0.0.13',
              'test-member-1', 'regionOne', 'ACTIVE', 'fake_tenant_id', 2)

    def setUp(self):
        super(TestInstanceShow, self).setUp()
        self.cmd = database_instances.ShowDatabaseInstance(self.app, None)
        self.data = self.fake_instances.get_instances_1234()
        self.instance_client.get.return_value = self.data
        self.columns = (
            'datastore',
            'datastore_version',
            'flavor',
            'id',
            'ip',
            'name',
            'region',
            'status',
            'tenant_id',
            'volume',
        )

    def test_show(self):
        args = ['1234']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)


class TestDatabaseInstanceDelete(TestInstances):

    def setUp(self):
        super(TestDatabaseInstanceDelete, self).setUp()
        self.cmd = database_instances.DeleteDatabaseInstance(self.app, None)

    @mock.patch("troveclient.utils.get_resource_id_by_name")
    def test_instance_delete(self, mock_getid):
        mock_getid.return_value = "fake_uuid"

        args = ['instance1']
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)

        mock_getid.assert_called_once_with(self.instance_client, "instance1")
        self.instance_client.delete.assert_called_with('fake_uuid')

    @mock.patch("troveclient.utils.get_resource_id_by_name")
    def test_instance_delete_with_exception(self, mock_getid):
        mock_getid.side_effect = exceptions.CommandError

        args = ['fakeinstance']
        parsed_args = self.check_parser(self.cmd, args, [])

        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)

    @mock.patch("troveclient.utils.get_resource_id_by_name")
    def test_instance_bulk_delete(self, mock_getid):
        instance_1 = uuidutils.generate_uuid()
        instance_2 = uuidutils.generate_uuid()
        mock_getid.return_value = instance_1

        args = ["fake_instance", instance_2]
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)

        mock_getid.assert_called_once_with(self.instance_client,
                                           "fake_instance")

        calls = [mock.call(instance_1), mock.call(instance_2)]
        self.instance_client.delete.assert_has_calls(calls)


class TestDatabaseInstanceCreate(TestInstances):

    values = ('2017-12-22T20:02:32', 'mysql', '5.6', '310',
              '2468', 'test', 'test-net', 'net-id', 'BUILD',
              '2017-12-22T20:02:32', 1)
    columns = (
        'created',
        'datastore',
        'datastore_version',
        'flavor',
        'id',
        'name',
        'networks',
        'networks_id',
        'status',
        'updated',
        'volume',
    )

    def setUp(self):
        super(TestDatabaseInstanceCreate, self).setUp()
        self.cmd = database_instances.CreateDatabaseInstance(self.app, None)
        self.data = self.fake_instances.get_instance_create()
        self.instance_client.create.return_value = self.data

    @mock.patch.object(utils, 'find_resource')
    def test_instance_create(self, mock_find):
        mock_find.id.side_effect = ['103', 'test', 'mod_id']
        args = ['test-name', '103',
                '--size', '1',
                '--databases', 'db1', 'db2',
                '--users', 'u1:111', 'u2:111',
                '--datastore', "datastore",
                '--datastore_version', "datastore_version",
                '--nic', 'net-id=net1',
                '--replica_of', 'test',
                '--replica_count', '4',
                '--module', 'mod_id',
                '--is-public',
                '--allowed-cidr', '10.0.0.1/24',
                '--allowed-cidr', '192.168.0.1/24']
        verifylist = [
            ('name', 'test-name'),
            ('flavor', '103'),
            ('size', 1),
            ('databases', ['db1', 'db2']),
            ('users', ['u1:111', 'u2:111']),
            ('datastore', "datastore"),
            ('datastore_version', "datastore_version"),
            ('nics', 'net-id=net1'),
            ('replica_of', 'test'),
            ('replica_count', 4),
            ('modules', ['mod_id']),
            ('is_public', True),
            ('allowed_cidrs', ['10.0.0.1/24', '192.168.0.1/24'])
        ]
        parsed_args = self.check_parser(self.cmd, args, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)


class TestDatabaseInstanceResetStatus(TestInstances):

    def setUp(self):
        super(TestDatabaseInstanceResetStatus, self).setUp()
        self.cmd = database_instances.ResetDatabaseInstanceStatus(self.app,
                                                                  None)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_reset_status(self, mock_find):
        args = ['instance1']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.instance_client.reset_status.assert_called_with('instance1')
        self.assertIsNone(result)


class TestDatabaseInstanceResizeFlavor(TestInstances):

    def setUp(self):
        super(TestDatabaseInstanceResizeFlavor, self).setUp()
        self.cmd = database_instances.ResizeDatabaseInstanceFlavor(self.app,
                                                                   None)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_resize_flavor(self, mock_find):
        args = ['instance1', 'flavor_id']
        mock_find.side_effect = ['instance1', 'flavor_id']
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.instance_client.resize_instance.assert_called_with('instance1',
                                                                'flavor_id')
        self.assertIsNone(result)


class TestDatabaseInstanceUpgrade(TestInstances):

    def setUp(self):
        super(TestDatabaseInstanceUpgrade, self).setUp()
        self.cmd = database_instances.UpgradeDatabaseInstance(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_upgrade(self, mock_find):
        args = ['instance1', 'datastore_version1']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.instance_client.upgrade.assert_called_with('instance1',
                                                        'datastore_version1')
        self.assertIsNone(result)


class TestDatabaseInstanceResizeVolume(TestInstances):

    def setUp(self):
        super(TestDatabaseInstanceResizeVolume, self).setUp()
        self.cmd = database_instances.ResizeDatabaseInstanceVolume(self.app,
                                                                   None)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_resize_volume(self, mock_find):
        args = ['instance1', '5']
        mock_find.side_effect = ['instance1']
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.instance_client.resize_volume.assert_called_with('instance1',
                                                              5)
        self.assertIsNone(result)


class TestDatabaseInstanceForceDelete(TestInstances):

    def setUp(self):
        super(TestDatabaseInstanceForceDelete, self).setUp()
        self.cmd = (database_instances
                    .ForceDeleteDatabaseInstance(self.app, None))

    @mock.patch.object(utils, 'find_resource')
    def test_instance_force_delete(self, mock_find):
        args = ['instance1']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.instance_client.reset_status.assert_called_with('instance1')
        self.instance_client.delete.assert_called_with('instance1')
        self.assertIsNone(result)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_force_delete_with_exception(self, mock_find):
        args = ['fakeinstance']
        parsed_args = self.check_parser(self.cmd, args, [])
        mock_find.return_value = args[0]

        self.instance_client.delete.side_effect = exceptions.CommandError
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)


class TestDatabaseInstanceEnableLog(TestInstances):

    def setUp(self):
        super(TestDatabaseInstanceEnableLog, self).setUp()
        self.cmd = database_instances.EnableDatabaseInstanceLog(self.app,
                                                                None)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_enable_log(self, mock_find):
        args = ['instance1', 'log_name']
        mock_find.side_effect = ['instance1']
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)
        self.instance_client.log_enable.assert_called_with('instance1',
                                                           'log_name')


class TestDatabaseInstancePromoteToReplicaSource(TestInstances):

    def setUp(self):
        super(TestDatabaseInstancePromoteToReplicaSource, self).setUp()
        self.cmd = database_instances.PromoteDatabaseInstanceToReplicaSource(
            self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_promote_to_replica_source(self, mock_find):
        args = ['instance']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.instance_client.promote_to_replica_source.assert_called_with(
            'instance')
        self.assertIsNone(result)


class TestDatabaseInstanceRestart(TestInstances):

    def setUp(self):
        super(TestDatabaseInstanceRestart, self).setUp()
        self.cmd = database_instances.RestartDatabaseInstance(self.app,
                                                              None)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_restart(self, mock_find):
        args = ['instance1']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.instance_client.restart.assert_called_with('instance1')
        self.assertIsNone(result)


class TestDatabaseInstanceEjectReplicaSource(TestInstances):

    def setUp(self):
        super(TestDatabaseInstanceEjectReplicaSource, self).setUp()
        self.cmd = database_instances.EjectDatabaseInstanceReplicaSource(
            self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_eject_replica_source(self, mock_find):
        args = ['instance']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.instance_client.eject_replica_source.assert_called_with(
            'instance')
        self.assertIsNone(result)


class TestDatabaseInstanceUpdate(TestInstances):

    def setUp(self):
        super(TestDatabaseInstanceUpdate, self).setUp()
        self.cmd = database_instances.UpdateDatabaseInstance(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_update(self, mock_find):
        args = ['instance1',
                '--name', 'new_instance_name',
                '--detach_replica_source',
                '--remove_configuration']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.instance_client.edit.assert_called_with('instance1',
                                                     None,
                                                     'new_instance_name',
                                                     True, True)
        self.assertIsNone(result)


class TestInstanceReplicaDetach(TestInstances):

    def setUp(self):
        super(TestInstanceReplicaDetach, self).setUp()
        self.cmd = database_instances.DetachDatabaseInstanceReplica(
            self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_replica_detach(self, mock_find):
        args = ['instance']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])
        result = self.cmd.take_action(parsed_args)
        self.instance_client.edit.assert_called_with(
            'instance', detach_replica_source=True)
        self.assertIsNone(result)
