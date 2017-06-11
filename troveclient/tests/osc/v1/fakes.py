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
#

import mock

from troveclient.tests import fakes
from troveclient.tests.osc import utils
from troveclient.v1 import backups
from troveclient.v1 import clusters
from troveclient.v1 import databases
from troveclient.v1 import datastores
from troveclient.v1 import flavors
from troveclient.v1 import instances
from troveclient.v1 import limits
from troveclient.v1 import users


class TestDatabasev1(utils.TestCommand):
    def setUp(self):
        super(TestDatabasev1, self).setUp()
        self.app.client_manager.database = mock.MagicMock()


class FakeFlavors(object):
    fake_flavors = fakes.FakeHTTPClient().get_flavors()[2]['flavors']

    def get_flavors_1(self):
        return flavors.Flavor(None, self.fake_flavors[0])


class FakeBackups(object):
    fake_backups = fakes.FakeHTTPClient().get_backups()[2]['backups']

    def get_backup_bk_1234(self):
        return backups.Backup(None, self.fake_backups[0])


class FakeClusters(object):
    fake_clusters = fakes.FakeHTTPClient().get_clusters()[2]['clusters']

    def get_clusters_cls_1234(self):
        return clusters.Cluster(None, self.fake_clusters[0])


class FakeConfigurations(object):
    fake_config = (fakes.FakeHTTPClient().get_configurations()
                   [2]['configurations'])

    def get_configurations_c_123(self):
        return flavors.Flavor(None, self.fake_config[0])


class FakeLimits(object):
    fake_limits = fakes.FakeHTTPClient().get_limits()[2]['limits']

    def get_absolute_limits(self):
        return limits.Limit(None, self.fake_limits[0])

    def get_non_absolute_limits(self):
        return limits.Limit(None,
                            {'value': 200,
                             'verb': 'DELETE',
                             'remaining': 200,
                             'unit': 'MINUTE'})


class FakeUsers(object):
    fake_users = fakes.FakeHTTPClient().get_instances_1234_users()[2]['users']

    def get_instances_1234_users_harry(self):
        return users.User(None, self.fake_users[2])


class FakeInstances(object):
    fake_instances = (fakes.FakeHTTPClient().get_instances()[2]['instances'])

    def get_instances_1234(self):
        return instances.Instance(None, self.fake_instances[0])


class FakeDatabases(object):
    fake_databases = [{'name': 'fakedb1'}]

    def get_databases_1(self):
        return databases.Database(None, self.fake_databases[0])


class FakeDatastores(object):
    fake_datastores = fakes.FakeHTTPClient().get_datastores()[2]['datastores']

    def get_datastores_d_123(self):
        return datastores.Datastore(None, self.fake_datastores[0])
