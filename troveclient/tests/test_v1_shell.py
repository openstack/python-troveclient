# Copyright [2015] Hewlett-Packard Development Company, L.P.
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

import base64
import fixtures
import mock
import re
import six
import testtools

import troveclient.client
from troveclient import exceptions
import troveclient.shell
from troveclient.tests import fakes
from troveclient.tests import utils
import troveclient.v1.modules
import troveclient.v1.shell


class ShellFixture(fixtures.Fixture):

    def setUp(self):
        super(ShellFixture, self).setUp()
        self.shell = troveclient.shell.OpenStackTroveShell()

    def tearDown(self):
        if hasattr(self.shell, 'cs'):
            self.shell.cs.clear_callstack()
        super(ShellFixture, self).tearDown()


class ShellTest(utils.TestCase):
    FAKE_ENV = {
        'OS_USERNAME': 'username',
        'OS_PASSWORD': 'password',
        'OS_PROJECT_ID': 'project_id',
        'OS_AUTH_URL': 'http://no.where/v2.0',
    }

    def setUp(self, *args):
        """Run before each test."""
        super(ShellTest, self).setUp()

        for var in self.FAKE_ENV:
            self.useFixture(fixtures.EnvironmentVariable(var,
                                                         self.FAKE_ENV[var]))
        self.shell = self.useFixture(ShellFixture()).shell

    @mock.patch('sys.stdout', new_callable=six.StringIO)
    @mock.patch('troveclient.client.get_version_map',
                return_value=fakes.get_version_map())
    @mock.patch('troveclient.v1.shell._find_instance_or_cluster',
                return_value=('1234', 'instance'))
    def run_command(self, cmd, mock_find_instance_or_cluster,
                    mock_get_version_map, mock_stdout):
        if isinstance(cmd, list):
            self.shell.main(cmd)
        else:
            self.shell.main(cmd.split())
        return mock_stdout.getvalue()

    @mock.patch('sys.stdout', new_callable=six.StringIO)
    @mock.patch('troveclient.client.get_version_map',
                return_value=fakes.get_version_map())
    @mock.patch('troveclient.v1.shell._find_instance_or_cluster',
                return_value=('cls-1234', 'cluster'))
    def run_command_clusters(self, cmd, mock_find_instance_or_cluster,
                             mock_get_version_map, mock_stdout):
        if isinstance(cmd, list):
            self.shell.main(cmd)
        else:
            self.shell.main(cmd.split())
        return mock_stdout.getvalue()

    def assert_called(self, method, url, body=None, **kwargs):
        return self.shell.cs.assert_called(method, url, body, **kwargs)

    def assert_called_anytime(self, method, url, body=None):
        return self.shell.cs.assert_called_anytime(method, url, body)

    def test__strip_option(self):
        # Format is: opt_name, opt_string, _strip_options_kwargs,
        #            expected_value, expected_opt_string, exception_msg
        data = [
            ["volume", "volume=10",
             {}, "10", "", None],
            ["volume", ",volume=10,,type=mine,",
             {}, "10", "type=mine", None],
            ["volume", "type=mine",
             {}, "", "type=mine", "Missing option 'volume'.*"],
            ["volume", "type=mine",
             {'is_required': False}, None, "type=mine", None],
            ["volume", "volume=1, volume=2",
             {}, "", "", "Option 'volume' found more than once.*"],
            ["volume", "volume=1, volume=2",
             {'allow_multiple': True}, ['1', '2'], "", None],
            ["volume", "volume=1, volume=2,,  volume=4, volume=6",
             {'allow_multiple': True}, ['1', '2', '4', '6'], "", None],
            ["module", ",flavor=10,,nic='net-id=net',module=test, module=test",
             {'allow_multiple': True}, ['test'],
             "flavor=10,,nic='net-id=net'", None],
            ["nic", ",flavor=10,,nic=net-id=net, module=test",
             {'quotes_required': True}, "", "",
             "Invalid 'nic' option. The value must be quoted.*"],
            ["nic", ",flavor=10,,nic='net-id=net', module=test",
             {'quotes_required': True}, "net-id=net",
             "flavor=10,, module=test", None],
            ["nic",
             ",nic='port-id=port',flavor=10,,nic='net-id=net', module=test",
             {'quotes_required': True, 'allow_multiple': True},
             ["net-id=net", "port-id=port"],
             "flavor=10,, module=test", None],
        ]

        count = 0
        for datum in data:
            count += 1
            opt_name = datum[0]
            opts_str = datum[1]
            kwargs = datum[2]
            expected_value = datum[3]
            expected_opt_string = datum[4]
            exception_msg = datum[5]
            msg = "Error (test data line %s): " % count
            try:
                value, opt_string = troveclient.v1.shell._strip_option(
                    opts_str, opt_name, **kwargs)
                if exception_msg:
                    self.assertEqual(True, False,
                                     "%sException not thrown, expecting %s" %
                                     (msg, exception_msg))
                if isinstance(expected_value, list):
                    self.assertEqual(
                        set(value), set(expected_value),
                        "%sValue not correct" % msg)
                else:
                    self.assertEqual(value, expected_value,
                                     "%sValue not correct" % msg)
                self.assertEqual(opt_string, expected_opt_string,
                                 "%sOption string not correct" % msg)
            except Exception as ex:
                if exception_msg:
                    msg = ex.message if hasattr(ex, 'message') else str(ex)
                    self.assertThat(msg,
                                    testtools.matchers.MatchesRegex(
                                        exception_msg, re.DOTALL),
                                    exception_msg, "%sWrong ex" % msg)
                else:
                    raise

    def test_instance_list(self):
        self.run_command('list')
        self.assert_called('GET', '/instances?include_clustered=False')

    def test_instance_show(self):
        self.run_command('show 1234')
        self.assert_called('GET', '/instances/1234')

    def test_reset_status(self):
        self.run_command('reset-status 1234')
        self.assert_called('POST', '/instances/1234/action')

    def test_instance_delete(self):
        self.run_command('delete 1234')
        self.assert_called('DELETE', '/instances/1234')

    def test_instance_force_delete(self):
        self.run_command('force-delete 1234')
        self.assert_called('DELETE', '/instances/1234')

    def test_instance_update(self):
        self.run_command('update 1234')
        self.assert_called('PATCH', '/instances/1234')

    def test_resize_instance(self):
        self.run_command('resize-instance 1234 1')
        self.assert_called('POST', '/instances/1234/action')

    def test_resize_volume(self):
        self.run_command('resize-volume 1234 3')
        self.assert_called('POST', '/instances/1234/action')

    def test_restart(self):
        self.run_command('restart 1234')
        self.assert_called('POST', '/instances/1234/action')

    def test_detach_replica(self):
        self.run_command('detach-replica 1234')
        self.assert_called('PATCH', '/instances/1234')

    def test_promote_to_replica_source(self):
        self.run_command('promote-to-replica-source 1234')
        self.assert_called('POST', '/instances/1234/action')

    def test_eject_replica_source(self):
        self.run_command('eject-replica-source 1234')
        self.assert_called('POST', '/instances/1234/action')

    def test_flavor_list(self):
        self.run_command('flavor-list')
        self.assert_called('GET', '/flavors')

    def test_flavor_list_with_datastore(self):
        cmd = ('flavor-list --datastore_type mysql '
               '--datastore_version_id some-version-id')
        self.run_command(cmd)
        self.assert_called(
            'GET', '/datastores/mysql/versions/some-version-id/flavors')

    def test_flavor_list_error(self):
        cmd = 'flavor-list --datastore_type mysql'
        exepcted_error_msg = ('Missing argument\(s\): '
                              'datastore_type, datastore_version_id')
        self.assertRaisesRegex(
            exceptions.MissingArgs, exepcted_error_msg, self.run_command,
            cmd)

    def test_flavor_show(self):
        self.run_command('flavor-show 1')
        self.assert_called('GET', '/flavors/1')

    def test_flavor_show_leading_zero(self):
        self.run_command('flavor-show 02')
        self.assert_called('GET', '/flavors/02')

    def test_flavor_show_by_name(self):
        self.run_command('flavor-show m1.tiny')  # defined in fakes.py
        self.assert_called('GET', '/flavors/m1.tiny')

    def test_flavor_show_uuid(self):
        self.run_command('flavor-show m1.uuid')
        self.assert_called('GET', '/flavors/m1.uuid')

    def test_volume_type_list(self):
        self.run_command('volume-type-list')
        self.assert_called('GET', '/volume-types')

    def test_volume_type_list_with_datastore(self):
        cmd = ('volume-type-list --datastore_type mysql '
               '--datastore_version_id some-version-id')
        self.run_command(cmd)
        self.assert_called(
            'GET', '/datastores/mysql/versions/some-version-id/volume-types')

    def test_volume_type_list_error(self):
        cmd = 'volume-type-list --datastore_type mysql'
        exepcted_error_msg = ('Missing argument\(s\): '
                              'datastore_type, datastore_version_id')
        self.assertRaisesRegex(
            exceptions.MissingArgs, exepcted_error_msg, self.run_command,
            cmd)

    def test_volume_type_show(self):
        self.run_command('volume-type-show 1')
        self.assert_called('GET', '/volume-types/1')

    def test_cluster_list(self):
        self.run_command('cluster-list')
        self.assert_called('GET', '/clusters')

    def test_cluster_show(self):
        self.run_command('cluster-show cls-1234')
        self.assert_called('GET', '/clusters/cls-1234')

    def test_cluster_instances(self):
        self.run_command('cluster-instances cls-1234')
        self.assert_called('GET', '/clusters/cls-1234')

    def test_cluster_reset_status(self):
        self.run_command('cluster-reset-status cls-1234')
        self.assert_called('POST', '/clusters/cls-1234')

    def test_cluster_delete(self):
        self.run_command('cluster-delete cls-1234')
        self.assert_called('DELETE', '/clusters/cls-1234')

    def test_cluster_force_delete(self):
        self.run_command('cluster-force-delete cls-1234')
        self.assert_called('DELETE', '/clusters/cls-1234')

    def test_boot_fail_with_size_0(self):
        self.assertRaises(exceptions.ValidationError, self.run_command,
                          'create test-member-1 1 --size 0 --volume_type lvm')

    def test_boot(self):
        self.run_command('create test-member-1 1 --size 1 --volume_type lvm')
        self.assert_called_anytime(
            'POST', '/instances',
            {'instance': {
                'volume': {'size': 1, 'type': 'lvm'},
                'flavorRef': 1,
                'name': 'test-member-1'
            }})

    def test_boot_with_modules(self):
        self.run_command('create test-member-1 1 --size 1 --volume_type lvm '
                         '--module 4321 --module 8765')
        self.assert_called_anytime(
            'POST', '/instances',
            {'instance': {
                'volume': {'size': 1, 'type': 'lvm'},
                'flavorRef': 1,
                'name': 'test-member-1',
                'modules': [{'id': '4321'}, {'id': '8765'}]
            }})

    def test_boot_by_flavor_name(self):
        self.run_command(
            'create test-member-1 m1.tiny --size 1 --volume_type lvm')
        self.assert_called_anytime(
            'POST', '/instances',
            {'instance': {
                'volume': {'size': 1, 'type': 'lvm'},
                'flavorRef': 1,
                'name': 'test-member-1'
            }})

    def test_boot_by_flavor_leading_zero(self):
        self.run_command(
            'create test-member-zero 02 --size 1 --volume_type lvm')
        self.assert_called_anytime(
            'POST', '/instances',
            {'instance': {
                'volume': {'size': 1, 'type': 'lvm'},
                'flavorRef': '02',
                'name': 'test-member-zero'
            }})

    def test_boot_repl_set(self):
        self.run_command('create repl-1 1 --size 1 --locality=anti-affinity '
                         '--replica_count=4')
        self.assert_called_anytime(
            'POST', '/instances',
            {'instance': {
                'volume': {'size': 1, 'type': None},
                'flavorRef': 1,
                'name': 'repl-1',
                'replica_count': 4,
                'locality': 'anti-affinity'
            }})

    def test_boot_replica(self):
        self.run_command('create slave-1 1 --size 1 --replica_of=master_1')
        self.assert_called_anytime(
            'POST', '/instances',
            {'instance': {
                'volume': {'size': 1, 'type': None},
                'flavorRef': 1,
                'name': 'slave-1',
                'replica_of': 'myid',
                'replica_count': 1
            }})

    def test_boot_replica_count(self):
        self.run_command('create slave-1 1 --size 1 --replica_of=master_1 '
                         '--replica_count=3')
        self.assert_called_anytime(
            'POST', '/instances',
            {'instance': {
                'volume': {'size': 1, 'type': None},
                'flavorRef': 1,
                'name': 'slave-1',
                'replica_of': 'myid',
                'replica_count': 3
            }})

    def test_boot_locality(self):
        self.run_command('create master-1 1 --size 1 --locality=affinity')
        self.assert_called_anytime(
            'POST', '/instances',
            {'instance': {
                'volume': {'size': 1, 'type': None},
                'flavorRef': 1,
                'name': 'master-1',
                'locality': 'affinity'
            }})

    def test_boot_locality_error(self):
        cmd = ('create slave-1 1 --size 1 --locality=affinity '
               '--replica_of=master_1')
        self.assertRaisesRegex(
            exceptions.ValidationError,
            'Cannot specify locality when adding replicas to existing '
            'master.',
            self.run_command, cmd)

    def test_boot_nic_error(self):
        cmd = ('create test-member-1 1 --size 1 --volume_type lvm '
               '--nic net-id=some-id,port-id=some-id')
        self.assertRaisesRegex(
            exceptions.ValidationError,
            'Invalid NIC argument: nic=\'net-id=some-id,port-id=some-id\'',
            self.run_command, cmd)

    def test_boot_restore_by_id(self):
        self.run_command('create test-restore-1 1 --size 1 --backup bk_1234')
        self.assert_called_anytime(
            'POST', '/instances',
            {'instance': {
                'volume': {'size': 1, 'type': None},
                'flavorRef': 1,
                'name': 'test-restore-1',
                'restorePoint': {'backupRef': 'bk-1234'},
            }})

    def test_boot_restore_by_name(self):
        self.run_command('create test-restore-1 1 --size 1 --backup bkp_1')
        self.assert_called_anytime(
            'POST', '/instances',
            {'instance': {
                'volume': {'size': 1, 'type': None},
                'flavorRef': 1,
                'name': 'test-restore-1',
                'restorePoint': {'backupRef': 'bk-1234'},
            }})

    def test_cluster_create(self):
        cmd = ('cluster-create test-clstr vertica 7.1 '
               '--instance flavor=02,volume=2 '
               '--instance flavor=2,volume=1 '
               '--instance flavor=2,volume=1,volume_type=my-type-1')
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/clusters',
            {'cluster': {
                'instances': [
                    {
                        'volume': {'size': '2'},
                        'flavorRef': '02'
                    },
                    {
                        'volume': {'size': '1'},
                        'flavorRef': '2'
                    },
                    {
                        'volume': {'size': '1', 'type': 'my-type-1'},
                        'flavorRef': '2'
                    }],
                'datastore': {'version': '7.1', 'type': 'vertica'},
                'name': 'test-clstr'}})

    def test_cluster_create_by_flavor_name(self):
        cmd = ('cluster-create test-clstr vertica 7.1 '
               '--instance flavor=m1.small,volume=2 '
               '--instance flavor=m1.leading-zero,volume=1')
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/clusters',
            {'cluster': {
                'instances': [
                    {
                        'volume': {'size': '2'},
                        'flavorRef': '2'
                    },
                    {
                        'volume': {'size': '1'},
                        'flavorRef': '02'
                    }],
                'datastore': {'version': '7.1', 'type': 'vertica'},
                'name': 'test-clstr'}})

    def test_cluster_create_error(self):
        cmd = ('cluster-create test-clstr vertica 7.1 --instance volume=2 '
               '--instance flavor=2,volume=1')
        self.assertRaisesRegex(
            exceptions.MissingArgs, "Missing option 'flavor'",
            self.run_command, cmd)

    def test_cluster_grow(self):
        cmd = ('cluster-grow cls-1234 '
               '--instance flavor=2,volume=2 '
               '--instance flavor=02,volume=1')
        self.run_command(cmd)
        self.assert_called('POST', '/clusters/cls-1234')

    def test_cluster_shrink(self):
        cmd = ('cluster-shrink cls-1234 1234')
        self.run_command(cmd)
        self.assert_called('POST', '/clusters/cls-1234')

    def test_cluster_upgrade(self):
        cmd = ('cluster-upgrade cls-1234 1234')
        self.run_command(cmd)
        self.assert_called('POST', '/clusters/cls-1234')

    def test_cluster_create_with_locality(self):
        cmd = ('cluster-create test-clstr2 redis 3.0 --locality=affinity '
               '--instance flavor=2,volume=1 '
               '--instance flavor=02,volume=1 '
               '--instance flavor=2,volume=1 ')
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/clusters',
            {'cluster': {
                'instances': [
                    {'flavorRef': '2',
                     'volume': {'size': '1'}},
                    {'flavorRef': '02',
                     'volume': {'size': '1'}},
                    {'flavorRef': '2',
                     'volume': {'size': '1'}},
                ],
                'datastore': {'version': '3.0', 'type': 'redis'},
                'name': 'test-clstr2',
                'locality': 'affinity'}})

    def test_cluster_create_with_configuration(self):
        cmd = ('cluster-create test-clstr2 redis 3.0 '
               '--configuration=config01 '
               '--instance flavor=2,volume=1 '
               '--instance flavor=02,volume=1 '
               '--instance flavor=2,volume=1 ')
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/clusters',
            {'cluster': {
                'instances': [
                    {'flavorRef': '2',
                     'volume': {'size': '1'}},
                    {'flavorRef': '02',
                     'volume': {'size': '1'}},
                    {'flavorRef': '2',
                     'volume': {'size': '1'}},
                ],
                'datastore': {'version': '3.0', 'type': 'redis'},
                'name': 'test-clstr2',
                'configuration': 'config01'}})

    def test_cluster_create_with_extended_properties(self):
        cmd = ('cluster-create test-clstr3 mongodb 4.0 '
               '--instance flavor=2,volume=1 '
               '--instance flavor=02,volume=1 '
               '--instance flavor=2,volume=1 '
               '--extended_properties num_mongos=3')
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/clusters',
            {'cluster': {
                'instances': [
                    {'flavorRef': '2',
                     'volume': {'size': '1'}},
                    {'flavorRef': '02',
                     'volume': {'size': '1'}},
                    {'flavorRef': '2',
                     'volume': {'size': '1'}},
                ],
                'datastore': {'version': '4.0', 'type': 'mongodb'},
                'name': 'test-clstr3',
                'extended_properties': {'num_mongos': '3'}}})

    def test_cluster_create_with_nic_az(self):
        cmd = ('cluster-create test-clstr1 vertica 7.1 '
               '--instance flavor=2,volume=2,nic=\'net-id=some-id\','
               'availability_zone=2 '
               '--instance flavor=2,volume=2,nic=\'net-id=some-id\','
               'availability_zone=2')
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/clusters',
            {'cluster': {
                'instances': [
                    {
                        'flavorRef': '2',
                        'volume': {'size': '2'},
                        'nics': [{'net-id': 'some-id'}],
                        'availability_zone': '2'
                    },
                    {
                        'flavorRef': '2',
                        'volume': {'size': '2'},
                        'nics': [{'net-id': 'some-id'}],
                        'availability_zone': '2'
                    }],
                'datastore': {'version': '7.1', 'type': 'vertica'},
                'name': 'test-clstr1'}})

    def test_cluster_create_with_nic_az_error(self):
        cmd = ('cluster-create test-clstr vertica 7.1 '
               '--instance flavor=2,volume=2,nic=net-id=some-id,'
               'port-id=some-port-id,availability_zone=2 '
               '--instance flavor=2,volume=1,nic=net-id=some-id,'
               'port-id=some-port-id,availability_zone=2')
        self.assertRaisesRegex(
            exceptions.ValidationError, "Invalid 'nic' option. "
            "The value must be quoted.",
            self.run_command, cmd)

    def test_cluster_create_with_nic_az_error_again(self):
        cmd = ('cluster-create test-clstr vertica 7.1 '
               '--instance flavor=2,volume=2,nic=\'v4-fixed-ip=10.0.0.1\','
               'availability_zone=2 '
               '--instance flavor=2,volume=1,nic=\'v4-fixed-ip=10.0.0.1\','
               'availability_zone=2')
        self.assertRaisesRegex(
            exceptions.ValidationError, 'Invalid NIC argument',
            self.run_command, cmd)

    def test_datastore_list(self):
        self.run_command('datastore-list')
        self.assert_called('GET', '/datastores')

    def test_datastore_show(self):
        self.run_command('datastore-show d-123')
        self.assert_called('GET', '/datastores/d-123')

    def test_datastore_version_list(self):
        self.run_command('datastore-version-list d-123')
        self.assert_called('GET', '/datastores/d-123/versions')

    def test_datastore_version_show(self):
        self.run_command('datastore-version-show v-56 --datastore d-123')
        self.assert_called('GET', '/datastores/d-123/versions/v-56')

    def test_datastore_version_show_error(self):
        expected_error_msg = ('The datastore name or id is required to '
                              'retrieve a datastore version by name.')
        self.assertRaisesRegex(exceptions.NoUniqueMatch, expected_error_msg,
                               self.run_command,
                               'datastore-version-show v-56')

    def test_configuration_list(self):
        self.run_command('configuration-list')
        self.assert_called('GET', '/configurations')

    def test_configuration_show(self):
        self.run_command('configuration-show c-123')
        self.assert_called('GET', '/configurations/c-123')

    def test_configuration_create(self):
        cmd = "configuration-create c-123 some-thing"
        self.assertRaises(ValueError, self.run_command, cmd)

    def test_configuration_update(self):
        cmd = "configuration-update c-123 some-thing"
        self.assertRaises(ValueError, self.run_command, cmd)

    def test_configuration_patch(self):
        cmd = "configuration-patch c-123 some-thing"
        self.assertRaises(ValueError, self.run_command, cmd)

    def test_configuration_parameter_list(self):
        cmd = 'configuration-parameter-list v-156 --datastore d-123'
        self.run_command(cmd)
        self.assert_called('GET',
                           '/datastores/d-123/versions/v-156/parameters')

    def test_configuration_parameter_list_error(self):
        expected_error_msg = ('The datastore name or id is required to '
                              'retrieve the parameters for the configuration '
                              'group by name')
        self.assertRaisesRegex(
            exceptions.NoUniqueMatch, expected_error_msg,
            self.run_command, 'configuration-parameter-list v-156')

    def test_configuration_parameter_show(self):
        cmd = ('configuration-parameter-show v_56 '
               'max_connections --datastore d_123')
        self.run_command(cmd)
        self.assert_called(
            'GET',
            '/datastores/d_123/versions/v_56/parameters/max_connections')

    def test_configuration_instances(self):
        cmd = 'configuration-instances c-123'
        self.run_command(cmd)
        self.assert_called('GET', '/configurations/c-123/instances')

    def test_configuration_delete(self):
        self.run_command('configuration-delete c-123')
        self.assert_called('DELETE', '/configurations/c-123')

    def test_configuration_default(self):
        self.run_command('configuration-default 1234')
        self.assert_called('GET', '/instances/1234/configuration')

    def test_configuration_attach(self):
        self.run_command('configuration-attach 1234 c-123')
        self.assert_called('PUT', '/instances/1234')

    def test_configuration_detach(self):
        self.run_command('configuration-detach 1234')
        self.assert_called('PUT', '/instances/1234')

    def test_upgrade(self):
        self.run_command('upgrade 1234 c-123')
        self.assert_called('PATCH', '/instances/1234')

    def test_metadata_edit(self):
        self.run_command('metadata-edit 1234 key-123 value-123')
        self.assert_called('PATCH', '/instances/1234/metadata/key-123')

    def test_metadata_update(self):
        self.run_command('metadata-update 1234 key-123 key-456 value-123')
        self.assert_called('PUT', '/instances/1234/metadata/key-123')

    def test_metadata_delete(self):
        self.run_command('metadata-delete 1234 key-123')
        self.assert_called('DELETE', '/instances/1234/metadata/key-123')

    def test_metadata_create(self):
        self.run_command('metadata-create 1234 key123 value123')
        self.assert_called_anytime(
            'POST', '/instances/1234/metadata/key123',
            {'metadata': {'value': 'value123'}})

    def test_metadata_list(self):
        self.run_command('metadata-list 1234')
        self.assert_called('GET', '/instances/1234/metadata')

    def test_metadata_show(self):
        self.run_command('metadata-show 1234 key123')
        self.assert_called('GET', '/instances/1234/metadata/key123')

    def test_module_list(self):
        self.run_command('module-list')
        self.assert_called('GET', '/modules')

    def test_module_list_datastore(self):
        self.run_command('module-list --datastore all')
        self.assert_called('GET', '/modules?datastore=all')

    def test_module_show(self):
        self.run_command('module-show 4321')
        self.assert_called('GET', '/modules/4321')

    def test_module_create(self):
        with mock.patch('argparse.open'):
            return_value = b'mycontents'
            expected_contents = str(return_value.decode('utf-8'))
            mock_encode = mock.Mock(return_value=return_value)
            with mock.patch.object(base64, 'b64encode', mock_encode):
                self.run_command('module-create mod1 type filename')
                self.assert_called_anytime(
                    'POST', '/modules',
                    {'module': {'contents': expected_contents,
                                'all_tenants': 0,
                                'module_type': 'type', 'visible': 1,
                                'auto_apply': 0, 'live_update': 0,
                                'name': 'mod1', 'priority_apply': 0,
                                'apply_order': 5}})

    def test_module_update(self):
        with mock.patch.object(troveclient.v1.modules.Module, '__repr__',
                               mock.Mock(return_value='4321')):
            self.run_command('module-update 4321 --name mod3')
            self.assert_called_anytime(
                'PUT', '/modules/4321',
                {'module': {'name': 'mod3'}})

    def test_module_delete(self):
        with mock.patch.object(troveclient.v1.modules.Module, '__repr__',
                               mock.Mock(return_value='4321')):
            self.run_command('module-delete 4321')
            self.assert_called_anytime('DELETE', '/modules/4321')

    def test_module_list_instance(self):
        self.run_command('module-list-instance 1234')
        self.assert_called_anytime('GET', '/instances/1234/modules')

    def test_module_instances(self):
        with mock.patch.object(troveclient.v1.modules.Module, '__repr__',
                               mock.Mock(return_value='4321')):
            self.run_command('module-instances 4321')
            self.assert_called_anytime('GET', '/modules/4321/instances')

    def test_module_instances_clustered(self):
        with mock.patch.object(troveclient.v1.modules.Module, '__repr__',
                               mock.Mock(return_value='4321')):
            self.run_command('module-instances 4321 --include_clustered')
            self.assert_called_anytime(
                'GET', '/modules/4321/instances?include_clustered=True')

    def test_module_instance_count(self):
        with mock.patch.object(troveclient.v1.modules.Module, '__repr__',
                               mock.Mock(return_value='4321')):
            self.run_command('module-instance-count 4321')
            self.assert_called(
                'GET', '/modules/4321/instances?count_only=True')

    def test_module_instance_count_clustered(self):
        with mock.patch.object(troveclient.v1.modules.Module, '__repr__',
                               mock.Mock(return_value='4321')):
            self.run_command('module-instance-count 4321 --include_clustered')
            self.assert_called(
                'GET', '/modules/4321/instances?count_only=True&'
                       'include_clustered=True')

    def test_module_reapply(self):
        with mock.patch.object(troveclient.v1.modules.Module, '__repr__',
                               mock.Mock(return_value='4321')):
            self.run_command('module-reapply 4321 --delay=5')
            self.assert_called_anytime('PUT', '/modules/4321/instances')

    def test_cluster_modules(self):
        self.run_command('cluster-modules cls-1234')
        self.assert_called_anytime('GET', '/clusters/cls-1234')

    def test_module_apply(self):
        self.run_command('module-apply 1234 4321 8765')
        self.assert_called_anytime('POST', '/instances/1234/modules',
                                   {'modules':
                                    [{'id': '4321'}, {'id': '8765'}]})

    def test_module_remove(self):
        self.run_command('module-remove 1234 4321')
        self.assert_called_anytime('DELETE', '/instances/1234/modules/4321')

    def test_module_query(self):
        self.run_command('module-query 1234')
        self.assert_called('GET', '/instances/1234/modules?from_guest=True')

    def test_module_retrieve(self):
        with mock.patch.object(troveclient.v1.modules.Module, '__getattr__',
                               mock.Mock(return_value='4321')):
            with mock.patch('troveclient.v1.instances.open'):
                self.run_command('module-retrieve 1234')
                self.assert_called(
                    'GET',
                    '/instances/1234/modules?'
                    'include_contents=True&from_guest=True')

    def test_limit_list(self):
        self.run_command('limit-list')
        self.assert_called('GET', '/limits')

    def test_backup_list(self):
        self.run_command('backup-list')
        self.assert_called('GET', '/backups')

    def test_backup_show(self):
        self.run_command('backup-show bk-1234')
        self.assert_called('GET', '/backups/bk-1234')

    def test_backup_list_instance(self):
        self.run_command('backup-list-instance 1234')
        self.assert_called('GET', '/instances/1234/backups')

    def test_backup_delete(self):
        self.run_command('backup-delete bk-1234')
        self.assert_called('DELETE', '/backups/bk-1234')

    def test_backup_create(self):
        self.run_command('backup-create 1234 bkp_1')
        self.assert_called_anytime(
            'POST', '/backups',
            {'backup': {
                'instance': '1234',
                'name': 'bkp_1',
                'incremental': False
            }})

    def test_database_list(self):
        self.run_command('database-list 1234')
        self.assert_called('GET', '/instances/1234/databases')

    def test_database_delete(self):
        self.run_command('database-delete 1234 db_1')
        self.assert_called('DELETE', '/instances/1234/databases/db_1')

    def test_database_create(self):
        cmd = ('database-create 1234 db_1 --character_set utf8 '
               '--collate utf8_general_ci')
        self.run_command(cmd)
        self.assert_called_anytime(
            'POST', '/instances/1234/databases',
            {'databases': [{'character_set': 'utf8',
                            'name': 'db_1',
                            'collate': 'utf8_general_ci'}]})

    def test_user_list(self):
        self.run_command('user-list 1234')
        self.assert_called('GET', '/instances/1234/users')

    def test_user_show(self):
        self.run_command('user-show 1234 jacob')
        self.assert_called('GET', '/instances/1234/users/jacob')

    def test_user_delete(self):
        self.run_command('user-delete 1234 jacob')
        self.assert_called('DELETE', '/instances/1234/users/jacob')

    def test_user_create(self):
        self.run_command('user-create 1234 jacob password')
        self.assert_called_anytime(
            'POST', '/instances/1234/users',
            {'users': [{
                'password': 'password',
                'name': 'jacob',
                'databases': []}]})

    def test_user_show_access(self):
        self.run_command('user-show-access 1234 jacob')
        self.assert_called('GET', '/instances/1234/users/jacob/databases')

    def test_user_update_host(self):
        cmd = 'user-update-attributes 1234 jacob --new_host 10.0.0.1'
        self.run_command(cmd)
        self.assert_called('PUT', '/instances/1234/users/jacob')

    def test_user_update_name(self):
        self.run_command('user-update-attributes 1234 jacob --new_name sam')
        self.assert_called('PUT', '/instances/1234/users/jacob')

    def test_user_update_password(self):
        cmd = 'user-update-attributes 1234 jacob --new_password new_pwd'
        self.run_command(cmd)
        self.assert_called('PUT', '/instances/1234/users/jacob')

    def test_user_grant_access(self):
        self.run_command('user-grant-access 1234 jacob  db1 db2')
        self.assert_called('PUT', '/instances/1234/users/jacob/databases')

    def test_user_revoke_access(self):
        self.run_command('user-revoke-access 1234 jacob  db1')
        self.assert_called('DELETE',
                           '/instances/1234/users/jacob/databases/db1')

    def test_root_enable_instance(self):
        self.run_command('root-enable 1234')
        self.assert_called_anytime('POST', '/instances/1234/root')

    def test_root_enable_cluster(self):
        self.run_command_clusters('root-enable cls-1234')
        self.assert_called_anytime('POST', '/clusters/cls-1234/root')

    def test_root_disable_instance(self):
        self.run_command('root-disable 1234')
        self.assert_called_anytime('DELETE', '/instances/1234/root')

    def test_root_show_instance(self):
        self.run_command('root-show 1234')
        self.assert_called('GET', '/instances/1234/root')

    def test_root_show_cluster(self):
        self.run_command_clusters('root-show cls-1234')
        self.assert_called('GET', '/clusters/cls-1234/root')

    def test_secgroup_list(self):
        self.run_command('secgroup-list')
        self.assert_called('GET', '/security-groups')

    def test_secgroup_show(self):
        self.run_command('secgroup-show 2')
        self.assert_called('GET', '/security-groups/2')

    def test_secgroup_list_rules(self):
        self.run_command('secgroup-list-rules 2')
        self.assert_called('GET', '/security-groups/2')

    def test_secgroup_delete_rule(self):
        self.run_command('secgroup-delete-rule 2')
        self.assert_called('DELETE', '/security-group-rules/2')

    def test_secgroup_add_rule(self):
        self.run_command('secgroup-add-rule 2 15.0.0.0/24')
        self.assert_called_anytime(
            'POST', '/security-group-rules',
            {'security_group_rule': {
                'cidr': '15.0.0.0/24',
                'group_id': '2',
            }})

    @mock.patch('sys.stdout', new_callable=six.StringIO)
    @mock.patch('troveclient.client.get_version_map',
                return_value=fakes.get_version_map())
    @mock.patch('troveclient.v1.shell._find_instance',
                side_effect=exceptions.CommandError)
    @mock.patch('troveclient.v1.shell._find_cluster',
                return_value='cls-1234')
    def test_find_instance_or_cluster_find_cluster(self, mock_find_cluster,
                                                   mock_find_instance,
                                                   mock_get_version_map,
                                                   mock_stdout):
        cmd = 'root-show cls-1234'
        self.shell.main(cmd.split())
        self.assert_called('GET', '/clusters/cls-1234/root')

    @mock.patch('sys.stdout', new_callable=six.StringIO)
    @mock.patch('troveclient.client.get_version_map',
                return_value=fakes.get_version_map())
    @mock.patch('troveclient.v1.shell._find_instance',
                return_value='1234')
    def test_find_instance_or_cluster(self, mock_find_instance,
                                      mock_get_version_map, mock_stdout):
        cmd = 'root-show 1234'
        self.shell.main(cmd.split())
        self.assert_called('GET', '/instances/1234/root')
