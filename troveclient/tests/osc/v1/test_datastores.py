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
from oslo_utils import uuidutils

from troveclient import common
from troveclient import exceptions
from troveclient.osc.v1 import datastores
from troveclient.tests.osc.v1 import fakes


class TestDatastores(fakes.TestDatabasev1):
    fake_datastores = fakes.FakeDatastores()

    def setUp(self):
        super(TestDatastores, self).setUp()
        self.datastore_client = self.app.client_manager.database.datastores
        self.datastore_version_client =\
            self.app.client_manager.database.datastore_versions
        self.dsversion_mgmt_client =\
            self.app.client_manager.database.mgmt_ds_versions


class TestDatastoreList(TestDatastores):
    columns = datastores.ListDatastores.columns
    values = ('d-123', 'mysql')

    def setUp(self):
        super(TestDatastoreList, self).setUp()
        self.cmd = datastores.ListDatastores(self.app, None)
        data = [self.fake_datastores.get_datastores_d_123()]
        self.datastore_client.list.return_value = common.Paginated(data)

    def test_datastore_list_defaults(self):
        parsed_args = self.check_parser(self.cmd, [], [])
        columns, data = self.cmd.take_action(parsed_args)
        self.datastore_client.list.assert_called_once_with()
        self.assertEqual(self.columns, columns)
        self.assertEqual([self.values], data)


class TestDatastoreShow(TestDatastores):

    values = ('5.6', 'd-123', 'mysql', '5.6 (v-56)')

    def setUp(self):
        super(TestDatastoreShow, self).setUp()
        self.cmd = datastores.ShowDatastore(self.app, None)
        self.data = self.fake_datastores.get_datastores_d_123()
        self.datastore_client.get.return_value = self.data
        self.columns = (
            'default_version',
            'id',
            'name',
            'versions (id)',
        )

    def test_show(self):
        args = ['mysql']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)


class TestDeleteDatastore(TestDatastores):
    def setUp(self):
        super(TestDeleteDatastore, self).setUp()
        self.cmd = datastores.DeleteDatastore(self.app, None)

    def test_delete_datastore(self):
        ds_id = uuidutils.generate_uuid()
        args = [ds_id]
        parsed_args = self.check_parser(self.cmd, args, [])

        self.cmd.take_action(parsed_args)

        self.datastore_client.delete.assert_called_once_with(ds_id)


class TestDatastoreVersionList(TestDatastores):
    columns = datastores.ListDatastoreVersions.columns
    values = ('v-56', '5.6', '')

    def setUp(self):
        super(TestDatastoreVersionList, self).setUp()
        self.cmd = datastores.ListDatastoreVersions(self.app, None)
        self.data = [self.fake_datastores.get_datastores_d_123_versions()]
        self.datastore_version_client.list.return_value =\
            common.Paginated(self.data)

    def test_datastore_version_list_defaults(self):
        args = ['mysql']
        parsed_args = self.check_parser(self.cmd, args, [])
        columns, data = self.cmd.take_action(parsed_args)
        self.datastore_version_client.list.assert_called_once_with(args[0])
        self.assertEqual(self.columns, columns)
        self.assertEqual([self.values], data)


class TestDatastoreVersionShow(TestDatastores):
    values = ('v-56', '5.6')

    def setUp(self):
        super(TestDatastoreVersionShow, self).setUp()
        self.cmd = datastores.ShowDatastoreVersion(self.app, None)
        self.data = self.fake_datastores.get_datastores_d_123_versions()
        self.datastore_version_client.get.return_value = self.data
        self.columns = (
            'id',
            'name',
        )

    def test_datastore_version_show_defaults(self):
        args = ['5.6', '--datastore', 'mysql']
        verifylist = [
            ('datastore_version', '5.6'),
            ('datastore', 'mysql'),
        ]
        parsed_args = self.check_parser(self.cmd, args, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(self.columns, columns)
        self.assertEqual(self.values, data)

    def test_datastore_version_show_with_version_id_exception(self):
        args = [
            'v-56',
        ]
        verifylist = [
            ('datastore_version', 'v-56'),
        ]
        parsed_args = self.check_parser(self.cmd, args, verifylist)
        self.assertRaises(exceptions.NoUniqueMatch,
                          self.cmd.take_action,
                          parsed_args)


class TestDeleteDatastoreVersion(TestDatastores):
    def setUp(self):
        super(TestDeleteDatastoreVersion, self).setUp()
        self.cmd = datastores.DeleteDatastoreVersion(self.app, None)

    def test_delete_datastore_version(self):
        dsversion_id = uuidutils.generate_uuid()
        args = [dsversion_id]
        parsed_args = self.check_parser(self.cmd, args, [])

        self.cmd.take_action(parsed_args)

        self.dsversion_mgmt_client.delete.assert_called_once_with(dsversion_id)


class TestCreateDatastoreVersion(TestDatastores):
    def setUp(self):
        super(TestCreateDatastoreVersion, self).setUp()
        self.cmd = datastores.CreateDatastoreVersion(self.app, None)

    def test_create_datastore_version(self):
        image_id = uuidutils.generate_uuid()
        args = ['new_name', 'ds_name', 'ds_manager', image_id, '--active',
                '--default', '--image-tags', 'trove,mysql']
        parsed_args = self.check_parser(self.cmd, args, [])

        self.cmd.take_action(parsed_args)

        self.dsversion_mgmt_client.create.assert_called_once_with(
            'new_name', 'ds_name', 'ds_manager', image_id, active='true',
            default='true', image_tags=['trove', 'mysql'],
            version=None)


class TestUpdateDatastoreVersion(TestDatastores):
    def setUp(self):
        super(TestUpdateDatastoreVersion, self).setUp()
        self.cmd = datastores.UpdateDatastoreVersion(self.app, None)

    def test_update_datastore_version(self):
        version_id = uuidutils.generate_uuid()
        args = [version_id, '--image-tags', 'trove,mysql', '--enable',
                '--non-default']
        parsed_args = self.check_parser(self.cmd, args, [])

        self.cmd.take_action(parsed_args)

        self.dsversion_mgmt_client.edit.assert_called_once_with(
            version_id, datastore_manager=None, image=None,
            active='true', default='false', image_tags=['trove', 'mysql'],
            name=None)
