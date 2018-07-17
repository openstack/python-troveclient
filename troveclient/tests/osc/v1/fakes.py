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
from troveclient.v1 import configurations
from troveclient.v1 import databases
from troveclient.v1 import datastores
from troveclient.v1 import flavors
from troveclient.v1 import instances
from troveclient.v1 import limits
from troveclient.v1 import modules
from troveclient.v1 import quota
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
    fake_cluster = (fakes.FakeHTTPClient()
                    .get_clusters_cls_1234()[2]['cluster'])
    fake_cluster_member = fake_cluster['instances'][1]
    fake_cluster_instance_modules = (fakes.FakeHTTPClient().
                                     get_cluster_instance_modules()[2]
                                     ['modules'])

    def get_clusters_cls_1234(self):
        return clusters.Cluster(None, self.fake_cluster)

    def get_clusters_member_2(self):
        return instances.Instance(None, self.fake_cluster_member)

    def cluster_instance_modules(self):
        return [[modules.Module(None, mod)]
                for mod in self.fake_cluster_instance_modules]


class FakeConfigurations(object):
    fake_config = (fakes.FakeHTTPClient().get_configurations()
                   [2]['configurations'])
    fake_config_instances = (fakes.FakeHTTPClient().
                             get_configurations_c_123_instances()[2])
    fake_default_config = (
        fakes.FakeHTTPClient().get_instances_1234_configuration()
        [2]['instance'])

    def get_configurations_c_123(self):
        return configurations.Configuration(None, self.fake_config[0])

    def get_configuration_instances(self):
        return [instances.Instance(None, fake_instance)
                for fake_instance in self.fake_config_instances['instances']]

    def get_default_configuration(self):
        return instances.Instance(None, self.fake_default_config)


class FakeConfigurationParameters(object):
    fake_config_param = (fakes.FakeHTTPClient().
                         get_datastores_d_123_versions_v_156_parameters()
                         [2]['configuration-parameters'])

    def get_params_connect_timeout(self):
        return configurations.\
            ConfigurationParameter(None, self.fake_config_param[1])


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
    fake_user_access = fakes.FakeHTTPClient().\
        get_instances_1234_users_jacob_databases()[2]

    def get_instances_1234_users_harry(self):
        return users.User(None, self.fake_users[2])

    def get_instances_1234_users_access(self):
        return [databases.Database(self, db) for db in
                self.fake_user_access['databases']]


class FakeInstances(object):
    fake_instances = (fakes.FakeHTTPClient().get_instances()[2]['instances'])
    fake_instance = fakes.FakeHTTPClient().get_instance_create()[2]

    def get_instances_1234(self):
        return instances.Instance(None, self.fake_instances[0])

    def get_instances(self):
        return [instances.Instance(None, fake_instance)
                for fake_instance in self.fake_instances]

    def get_instance_create(self):
        return instances.Instance(None, self.fake_instance['instance'])


class FakeDatabases(object):
    fake_databases = [{'name': 'fakedb1'}]

    def get_databases_1(self):
        return databases.Database(None, self.fake_databases[0])


class FakeDatastores(object):
    fake_datastores = fakes.FakeHTTPClient().get_datastores()[2]['datastores']
    fake_datastore_versions = fake_datastores[0]['versions']

    def get_datastores_d_123(self):
        return datastores.Datastore(None, self.fake_datastores[0])

    def get_datastores_d_123_versions(self):
        return datastores.Datastore(None, self.fake_datastore_versions[0])


class FakeRoot(object):
    fake_instance_1234_root = (fakes.FakeHTTPClient()
                               .get_instances_1234_root()[2])
    fake_cls_1234_root = (fakes.FakeHTTPClient()
                          .get_clusters_cls_1234_root()[2])

    def get_instance_1234_root(self):
        return users.User(None, self.fake_instance_1234_root,
                          loaded=True)

    def get_cls_1234_root(self):
        return users.User(None, self.fake_cls_1234_root,
                          loaded=True)

    def post_instance_1234_root(self):
        root = fakes.FakeHTTPClient().post_instances_1234_root()[2]['user']
        return root['name'], root['password']

    def post_cls_1234_root(self):
        root = fakes.FakeHTTPClient().post_instances_1234_root()[2]['user']
        return root['name'], root['password']

    def delete_instance_1234_root(self):
        return fakes.FakeHTTPClient().delete_instances_1234_root()[2]


class FakeQuota(object):
    fake_quotas = fakes.FakeHTTPClient().get_quotas()[2]['quotas']
    fake_instances_quota = (fakes.FakeHTTPClient()
                            .update_instances_quota()[2]['quotas'])

    def get_quotas(self):
        return [quota.Quotas.resource_class(None, q)
                for q in self.fake_quotas]


class FakeLogs(object):
    fake_logs = fakes.FakeHTTPClient().get_logs()[2]['logs']

    def get_logs(self):
        return [instances.DatastoreLog(None, fake_log)
                for fake_log in self.fake_logs]
