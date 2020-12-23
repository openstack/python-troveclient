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

from unittest import mock

from osc_lib import utils
from oslo_utils import uuidutils

from troveclient import common
from troveclient import exceptions
from troveclient.osc.v1 import database_instances
from troveclient.tests.osc.v1 import fakes
from troveclient.v1 import instances


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

    def test_instance_list_defaults(self):
        instance_id = self.random_uuid()
        name = self.random_name('test-list')
        tenant_id = self.random_uuid()
        insts = [
            {
                "id": instance_id,
                "name": name,
                "status": "ACTIVE",
                "operating_status": "HEALTHY",
                "addresses": [
                    {"type": "private", "address": "10.0.0.13"}
                ],
                "volume": {"size": 2},
                "flavor": {"id": "02"},
                "region": "regionOne",
                "datastore": {
                    "version": "5.6", "type": "mysql",
                    "version_number": "5.7.29"
                },
                "tenant_id": tenant_id,
                "replica_of": self.random_uuid(),
                "access": {"is_public": False, "allowed_cidrs": []},
            }
        ]
        self.instance_client.list.return_value = common.Paginated(
            [instances.Instance(mock.MagicMock(), inst) for inst in insts])

        parsed_args = self.check_parser(self.cmd, [], [])
        columns, data = self.cmd.take_action(parsed_args)

        self.instance_client.list.assert_called_once_with(**self.defaults)
        self.assertEqual(
            database_instances.ListDatabaseInstances.columns,
            columns
        )

        values = [
            (instance_id, name, 'mysql', '5.6', 'ACTIVE', 'HEALTHY', False,
             [{"type": "private", "address": "10.0.0.13"}],
             '02', 2, 'replica'),
        ]
        self.assertEqual(values, data)

    def test_instance_list_all_projects(self):
        instance_id = self.random_uuid()
        name = self.random_name('test-list')
        tenant_id = self.random_uuid()
        server_id = self.random_uuid()
        insts = [
            {
                "id": instance_id,
                "name": name,
                "status": "ACTIVE",
                "operating_status": "HEALTHY",
                "addresses": [
                    {"type": "private", "address": "10.0.0.13"}
                ],
                "volume": {"size": 2},
                "flavor": {"id": "02"},
                "region": "regionOne",
                "datastore": {
                    "version": "5.6", "type": "mysql",
                    "version_number": "5.7.29"
                },
                "tenant_id": tenant_id,
                "access": {"is_public": False, "allowed_cidrs": []},
                "server_id": server_id,
                'server': {
                    'id': server_id
                }
            }
        ]
        self.mgmt_client.list.return_value = common.Paginated(
            [instances.Instance(mock.MagicMock(), inst) for inst in insts])

        parsed_args = self.check_parser(self.cmd, ["--all-projects"],
                                        [("all_projects", True)])
        columns, data = self.cmd.take_action(parsed_args)

        self.mgmt_client.list.assert_called_once_with(**self.defaults)
        self.assertEqual(
            database_instances.ListDatabaseInstances.admin_columns,
            columns
        )

        expected_instances = [
            (instance_id, name, 'mysql', '5.6', 'ACTIVE', 'HEALTHY', False,
             [{"type": "private", "address": "10.0.0.13"}],
             '02', 2, '', server_id, tenant_id),
        ]
        self.assertEqual(expected_instances, data)

    def test_instance_list_for_project(self):
        instance_id = self.random_uuid()
        name = self.random_name('test-list')
        tenant_id = self.random_uuid()
        server_id = self.random_uuid()
        insts = [
            {
                "id": instance_id,
                "name": name,
                "status": "ACTIVE",
                "operating_status": "HEALTHY",
                "addresses": [
                    {"type": "private", "address": "10.0.0.13"}
                ],
                "volume": {"size": 2},
                "flavor": {"id": "02"},
                "region": "regionOne",
                "datastore": {
                    "version": "5.6", "type": "mysql",
                    "version_number": "5.7.29"
                },
                "tenant_id": tenant_id,
                "access": {"is_public": False, "allowed_cidrs": []},
                "server_id": server_id,
                'server': {
                    'id': server_id
                }
            }
        ]
        self.mgmt_client.list.return_value = common.Paginated(
            [instances.Instance(mock.MagicMock(), inst) for inst in insts])

        parsed_args = self.check_parser(self.cmd, ["--project-id", tenant_id],
                                        [("project_id", tenant_id)])
        columns, data = self.cmd.take_action(parsed_args)

        self.assertEqual(
            database_instances.ListDatabaseInstances.admin_columns,
            columns
        )
        expected_instances = [
            (instance_id, name, 'mysql', '5.6', 'ACTIVE', 'HEALTHY', False,
             [{"type": "private", "address": "10.0.0.13"}],
             '02', 2, '', server_id, tenant_id),
        ]
        self.assertEqual(expected_instances, data)

        expected_params = {
            'include_clustered': False,
            'limit': None,
            'marker': None,
            'project_id': tenant_id
        }
        self.mgmt_client.list.assert_called_once_with(**expected_params)


class TestInstanceShow(TestInstances):
    def setUp(self):
        super(TestInstanceShow, self).setUp()
        self.cmd = database_instances.ShowDatabaseInstance(self.app, None)
        self.columns = (
            'addresses',
            'allowed_cidrs',
            'datastore',
            'datastore_version',
            'datastore_version_number',
            'flavor',
            'id',
            'name',
            'operating_status',
            'public',
            'region',
            'replica_of',
            'status',
            'tenant_id',
            'volume',
        )

    def test_show(self):
        instance_id = self.random_uuid()
        name = self.random_name('test-show')
        flavor_id = self.random_uuid()
        primary_id = self.random_uuid()
        tenant_id = self.random_uuid()
        inst = {
            "id": instance_id,
            "name": name,
            "status": "ACTIVE",
            "operating_status": "HEALTHY",
            "addresses": [
                {"type": "private", "address": "10.0.0.13"}
            ],
            "volume": {"size": 2},
            "flavor": {"id": flavor_id},
            "region": "regionOne",
            "datastore": {
                "version": "5.7.29", "type": "mysql",
                "version_number": "5.7.29"
            },
            "tenant_id": tenant_id,
            "replica_of": {'id': primary_id},
            "access": {"is_public": False, "allowed_cidrs": []},
        }
        self.instance_client.get.return_value = instances.Instance(
            mock.MagicMock(), inst)

        parsed_args = self.check_parser(self.cmd, [instance_id], [])
        columns, data = self.cmd.take_action(parsed_args)

        values = ([{'address': '10.0.0.13', 'type': 'private'}], [], 'mysql',
                  '5.7.29', '5.7.29', flavor_id, instance_id, name, 'HEALTHY',
                  False, 'regionOne', primary_id, 'ACTIVE',
                  tenant_id, 2)
        self.assertEqual(self.columns, columns)
        self.assertEqual(values, data)


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

    @mock.patch("troveclient.utils.get_resource_id_by_name")
    def test_instance_force_delete(self, mock_getid):
        mock_getid.return_value = "fake_uuid"

        args = ['instance1', '--force']
        parsed_args = self.check_parser(self.cmd, args, [('force', True)])
        self.cmd.take_action(parsed_args)

        mock_getid.assert_called_once_with(self.instance_client, "instance1")
        self.instance_client.force_delete.assert_called_with('fake_uuid')


class TestDatabaseInstanceCreate(TestInstances):

    values = ('2017-12-22T20:02:32', 'mysql', '5.6', '5.7.29', '310',
              '2468', 'test', 'test-net', 'net-id', 'BUILD',
              '2017-12-22T20:02:32', 1)
    columns = (
        'created',
        'datastore',
        'datastore_version',
        'datastore_version_number',
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
        args = ['test-name', '--flavor', '103',
                '--size', '1',
                '--databases', 'db1', 'db2',
                '--users', 'u1:111', 'u2:111',
                '--datastore', "datastore",
                '--datastore-version', "datastore_version",
                '--nic', 'net-id=net1',
                '--replica-of', 'test',
                '--replica-count', '4',
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

    @mock.patch.object(utils, 'find_resource')
    def test_instance_create_without_allowed_cidrs(self, mock_find):
        resp = {
            "id": "a1fea1cf-18ad-48ab-bdfd-fce99a4b834e",
            "name": "test-mysql",
            "status": "BUILD",
            "flavor": {
                "id": "a48ea749-7ee3-4003-8aae-eb4e79773e2d"
            },
            "datastore": {
                "type": "mysql",
                "version": "5.7.29",
                "version_number": "5.7.29"
            },
            "region": "RegionOne",
            "access": {
                "is_public": True
            },
            "volume": {
                "size": 1
            },
            "created": "2020-08-12T09:41:47",
            "updated": "2020-08-12T09:41:47",
            "service_status_updated": "2020-08-12T09:41:47"
        }
        self.instance_client.create.return_value = instances.Instance(
            mock.MagicMock(), resp)

        args = [
            'test-mysql',
            '--flavor', 'a48ea749-7ee3-4003-8aae-eb4e79773e2d',
            '--size', '1',
            '--datastore', "mysql",
            '--datastore-version', "5.7.29",
            '--nic', 'net-id=net1',
            '--is-public'
        ]
        verifylist = [
            ('name', 'test-mysql'),
            ('flavor', 'a48ea749-7ee3-4003-8aae-eb4e79773e2d'),
            ('size', 1),
            ('datastore', "mysql"),
            ('datastore_version', "5.7.29"),
            ('nics', 'net-id=net1'),
            ('is_public', True),
            ('allowed_cidrs', None)
        ]

        parsed_args = self.check_parser(self.cmd, args, verifylist)
        columns, data = self.cmd.take_action(parsed_args)

        expected_columns = (
            'allowed_cidrs',
            'created',
            'datastore',
            'datastore_version',
            'datastore_version_number',
            'flavor',
            'id',
            'name',
            'public',
            'region',
            'service_status_updated',
            'status',
            'updated',
            'volume',
        )
        expected_values = (
            [],
            "2020-08-12T09:41:47",
            "mysql",
            "5.7.29",
            "5.7.29",
            "a48ea749-7ee3-4003-8aae-eb4e79773e2d",
            "a1fea1cf-18ad-48ab-bdfd-fce99a4b834e",
            "test-mysql",
            True,
            "RegionOne",
            "2020-08-12T09:41:47",
            "BUILD",
            "2020-08-12T09:41:47",
            1,
        )
        self.assertEqual(expected_columns, columns)
        self.assertEqual(expected_values, data)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_create_nic_param(self, mock_find):
        fake_id = self.random_uuid()
        mock_find.return_value.id = fake_id
        args = [
            'test-mysql',
            '--flavor', 'a48ea749-7ee3-4003-8aae-eb4e79773e2d',
            '--size', '1',
            '--datastore', "mysql",
            '--datastore-version', "5.7.29",
            '--nic', 'net-id=net1,subnet-id=subnet_id,ip-address=192.168.1.11',
        ]
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)

        self.instance_client.create.assert_called_once_with(
            'test-mysql',
            flavor_id=fake_id,
            volume={"size": 1, "type": None},
            databases=[],
            users=[],
            restorePoint=None,
            availability_zone=None,
            datastore='mysql',
            datastore_version='5.7.29',
            datastore_version_number=None,
            nics=[
                {'network_id': 'net1', 'subnet_id': 'subnet_id',
                 'ip_address': '192.168.1.11'}
            ],
            configuration=None,
            replica_of=None,
            replica_count=None,
            modules=[],
            locality=None,
            region_name=None,
            access={'is_public': False}
        )


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
        mock_find.side_effect = [
            mock.MagicMock(id='fake_instance_id'),
            mock.MagicMock(id='fake_flavor_id')
        ]
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)

        self.instance_client.resize_instance.assert_called_with(
            'fake_instance_id', 'fake_flavor_id')


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
        self.instance_client.update.assert_called_with(
            'instance1',
            None,
            'new_instance_name',
            True, True,
            is_public=None, allowed_cidrs=None)
        self.assertIsNone(result)

    def test_instance_update_access(self):
        ins_id = '4c397f77-750d-43df-8fc5-f7388e4316ee'
        args = [ins_id,
                '--name', 'new_instance_name',
                '--is-private', '--allowed-cidr', '10.0.0.0/24',
                '--allowed-cidr', '10.0.1.0/24']
        parsed_args = self.check_parser(self.cmd, args, [])
        self.cmd.take_action(parsed_args)

        self.instance_client.update.assert_called_with(
            ins_id,
            None,
            'new_instance_name',
            False, False,
            is_public=False, allowed_cidrs=['10.0.0.0/24', '10.0.1.0/24'])


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
        self.instance_client.update.assert_called_with(
            'instance', detach_replica_source=True)
        self.assertIsNone(result)


class TestDatabaseInstanceReboot(TestInstances):
    def setUp(self):
        super(TestDatabaseInstanceReboot, self).setUp()
        self.cmd = database_instances.RebootDatabaseInstance(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_restart(self, mock_find):
        args = ['instance1']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])

        self.cmd.take_action(parsed_args)

        self.mgmt_client.reboot.assert_called_with('instance1')


class TestDatabaseInstanceRebuild(TestInstances):
    def setUp(self):
        super(TestDatabaseInstanceRebuild, self).setUp()
        self.cmd = database_instances.RebuildDatabaseInstance(self.app, None)

    @mock.patch.object(utils, 'find_resource')
    def test_instance_rebuild(self, mock_find):
        args = ['instance1', 'image_id']
        mock_find.return_value = args[0]
        parsed_args = self.check_parser(self.cmd, args, [])

        self.cmd.take_action(parsed_args)

        self.mgmt_client.rebuild.assert_called_with('instance1', 'image_id')
