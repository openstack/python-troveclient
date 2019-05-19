# Copyright [2015] Hewlett-Packard Development Company, L.P.
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

from six.moves.urllib import parse
from troveclient import client as base_client
from troveclient.tests import utils
from troveclient.v1 import client


def get_version_map():
    return {
        '1.0': 'troveclient.tests.fakes.FakeClient',
    }


def assert_has_keys(dict, required=None, optional=None):
    required = required or []
    optional = optional or []
    keys = dict.keys()
    for k in required:
        try:
            assert k in keys
        except AssertionError:
            raise AssertionError("key: %s not found." % k)


class FakeClient(client.Client):

    URL_QUERY_SEPARATOR = '&'
    URL_SEPARATOR = '?'

    def __init__(self, *args, **kwargs):
        client.Client.__init__(self, 'username', 'password',
                               'project_id', 'auth_url',
                               extensions=kwargs.get('extensions'))
        self.client = FakeHTTPClient(**kwargs)

    def _order_url_query_str(self, url):
        """Returns the url with the query strings ordered, if they exist and
        there's more than one. Otherwise the url is returned unaltered.
        """
        if self.URL_QUERY_SEPARATOR in url:
            parts = url.split(self.URL_SEPARATOR)
            if len(parts) == 2:
                queries = sorted(parts[1].split(self.URL_QUERY_SEPARATOR))
                url = self.URL_SEPARATOR.join(
                    [parts[0], self.URL_QUERY_SEPARATOR.join(queries)])
        return url

    def assert_called(self, method, url, body=None, pos=-1):
        """Assert than an API method was just called."""
        expected = (method, utils.order_url(url))
        called = (self.client.callstack[pos][0],
                  utils.order_url(self.client.callstack[pos][1]))

        assert self.client.callstack, \
            "Expected %s %s but no calls were made." % expected

        assert expected == called, \
            'Expected %s %s; got %s %s' % (expected + called)

        if body is not None:
            if self.client.callstack[pos][2] != body:
                raise AssertionError('%r != %r' %
                                     (self.client.callstack[pos][2], body))

    def assert_called_anytime(self, method, url, body=None):
        """Assert than an API method was called anytime in the test."""
        expected = (method, utils.order_url(url))

        assert self.client.callstack, \
            "Expected %s %s but no calls were made." % expected

        found = False
        for entry in self.client.callstack:
            if expected == (entry[0], utils.order_url(entry[1])):
                found = True
                break

        assert found, 'Expected %s; got %s' % (expected, self.client.callstack)
        if body is not None:
            try:
                assert entry[2] == body
            except AssertionError:
                print(entry[2])
                print("!=")
                print(body)
                raise

        self.client.callstack = []


class FakeHTTPClient(base_client.HTTPClient):

    def __init__(self, **kwargs):
        self.username = 'username'
        self.password = 'password'
        self.auth_url = 'auth_url'
        self.management_url = (
            'http://trove-api:8779/v1.0/14630bc0e9ef4e248c9753eaf57b0f6e')
        self.tenant_id = 'tenant_id'
        self.callstack = []
        self.projectid = 'projectid'
        self.user = 'user'
        self.region_name = 'region_name'
        self.endpoint_type = 'endpoint_type'
        self.service_type = 'service_type'
        self.service_name = 'service_name'
        self.volume_service_name = 'volume_service_name'
        self.timings = 'timings'
        self.bypass_url = 'bypass_url'
        self.os_cache = 'os_cache'
        self.http_log_debug = 'http_log_debug'

    def _cs_request(self, url, method, **kwargs):
        # Check that certain things are called correctly
        if method in ['GET', 'DELETE']:
            assert 'body' not in kwargs
        elif method == 'PUT':
            assert 'body' in kwargs

        if url is not None:
            # Call the method
            args = parse.parse_qsl(parse.urlparse(url)[4])
            kwargs.update(args)
            munged_url = url.rsplit('?', 1)[0]
            munged_url = munged_url.strip('/').replace('/', '_')
            munged_url = munged_url.replace('.', '_')
            munged_url = munged_url.replace('-', '_')
            munged_url = munged_url.replace(' ', '_')
            callback = "%s_%s" % (method.lower(), munged_url)

        if not hasattr(self, callback):
            raise AssertionError('Called unknown API method: %s %s, '
                                 'expected fakes method name: %s' %
                                 (method, url, callback))

        # Note the call
        self.callstack.append((method, url, kwargs.get('body')))

        status, headers, body = getattr(self, callback)(**kwargs)
        r = utils.TestResponse({
            "status_code": status,
            "text": body,
            "headers": headers,
        })
        return r, body

    def get_instances(self, **kw):
        return (
            200,
            {},
            {
                "instances": [
                    {
                        "id": "1234",
                        "name": "test-member-1",
                        "status": "ACTIVE",
                        "ip": ["10.0.0.13"],
                        "volume": {"size": 2},
                        "flavor": {"id": "02"},
                        "region": "regionOne",
                        "datastore": {"version": "5.6", "type": "mysql"},
                        "tenant_id": "fake_tenant_id",
                    },
                    {
                        "id": "5678",
                        "name": "test-member-2",
                        "status": "ACTIVE",
                        "ip": ["10.0.0.14"],
                        "volume": {"size": 2},
                        "flavor": {"id": "2"},
                        "region": "regionOne",
                        "datastore": {"version": "5.6", "type": "mysql"},
                        "tenant_id": "fake_tenant_id",
                    },

                ]
            }
        )

    def get_instance_counts(self, **kw):
        return (200, {}, {"instances": [
            {
                "module_id": "4321",
                "module_name": "mod1",
                "min_date": "2015-05-02T11:06:16",
                "max_date": "2015-05-02T11:06:19",
                "module_md5": "9db783b92a9355f70c41806659fcb77d",
                "current": True,
                "count": 1}]})

    def get_instances_1234(self, **kw):
        r = {'instance': self.get_instances()[2]['instances'][0]}
        return (200, {}, r)

    def get_instance_create(self, **kw):
        return (200, {}, {"instance": {
                "status": "BUILD",
                "updated": "2017-12-22T20:02:32",
                "name": "test",
                "created": "2017-12-22T20:02:32",
                "networks": {
                    "name": "test-net",
                    "id": "net-id"
                },
                "id": "2468",
                "volume": {
                    "size": 1
                },
                "flavor": {
                    "id": "310"
                },
                "datastore": {
                    "version": "5.6",
                    "type": "mysql"
                }}})

    def post_instances(self, body, **kw):
        assert_has_keys(
            body['instance'],
            required=['name', 'flavorRef'],
            optional=['volume'])
        if 'volume' in body['instance']:
            assert_has_keys(body['instance']['volume'], required=['size'])
        return (202, {}, self.get_instances_1234()[2])

    def get_flavors(self, **kw):
        return (200, {}, {"flavors": [
            {
                "str_id": "1",
                "ram": 512,
                "id": 1,
                "name": "m1.tiny"},
            {
                "str_id": "10",
                "ram": 768,
                "id": 10,
                "name": "eph.rd-smaller"},
            {
                "str_id": "2",
                "ram": 2048,
                "id": 2,
                "name": "m1.small"},
            {
                "str_id": "3",
                "ram": 4096,
                "id": 3,
                "name": "m1.medium"},
            {
                "str_id": "7d0d16e5-875f-4198-b6da-90ab2d3e899e",
                "ram": 8192,
                "id": None,
                "name": "m1.uuid"},
            {
                "str_id": "02",
                "ram": 1024,
                "id": None,
                "name": "m1.leading-zero"}]})

    def get_datastores_mysql_versions_some_version_id_flavors(self, **kw):
        return self.get_flavors()

    def get_flavors_1(self, **kw):
        r = {'flavor': self.get_flavors()[2]['flavors'][0]}
        return (200, {}, r)

    def get_flavors_2(self, **kw):
        r = {'flavor': self.get_flavors()[2]['flavors'][2]}
        return (200, {}, r)

    def get_flavors_m1_tiny(self, **kw):
        r = {'flavor': self.get_flavors()[2]['flavors'][0]}
        return (200, {}, r)

    def get_flavors_eph_rd_smaller(self, **kw):
        r = {'flavor': self.get_flavors()[2]['flavors'][1]}
        return (200, {}, r)

    def get_flavors_m1_small(self, **kw):
        r = {'flavor': self.get_flavors()[2]['flavors'][2]}
        return (200, {}, r)

    def get_flavors_m1_medium(self, **kw):
        r = {'flavor': self.get_flavors()[2]['flavors'][3]}
        return (200, {}, r)

    def get_flavors_m1_uuid(self, **kw):
        r = {'flavor': self.get_flavors()[2]['flavors'][4]}
        return (200, {}, r)

    def get_flavors_02(self, **kw):
        r = {'flavor': self.get_flavors()[2]['flavors'][5]}
        return (200, {}, r)

    def get_flavors_m1_leading_zero(self, **kw):
        r = {'flavor': self.get_flavors()[2]['flavors'][5]}
        return (200, {}, r)

    def get_volume_types(self, **kw):
        return (200, {}, {"volume_types": [
            {
                "id": "1",
                "name": "vt_1",
                "description": "Volume type #1",
                "is_public": False},
            {
                "id": "10",
                "name": "volume_type_2",
                "description": "Volume type #2",
                "is_public": True}]})

    def get_datastores_mysql_versions_some_version_id_volume_types(self, **kw):
        return self.get_volume_types()

    def get_volume_types_1(self, **kw):
        r = {'volume_type': self.get_volume_types()[2]['volume_types'][0]}
        return (200, {}, r)

    def get_volume_types_2(self, **kw):
        r = {'volume_type': self.get_volume_types()[2]['volume_types'][2]}
        return (200, {}, r)

    def get_clusters(self, **kw):
        return (200, {}, {"clusters": [
            {
                "instances": [
                    {
                        "type": "member",
                        "id": "member-1",
                        "ip": ["10.0.0.3"],
                        "flavor": {"id": "02"},
                        "name": "test-clstr-member-1"
                    },
                    {
                        "type": "member",
                        "id": "member-2",
                        "ip": ["10.0.0.4"],
                        "flavor": {"id": "2"},
                        "name": "test-clstr-member-2"
                    }],
                "updated": "2015-05-02T11:06:19",
                "task": {"description": "No tasks for the cluster.", "id": 1,
                         "name": "NONE"},
                "name": "test-clstr",
                "created": "2015-05-02T10:37:04",
                "datastore": {"version": "7.1", "type": "vertica"},
                "id": "cls-1234"}]})

    def get_clusters_cls_1234(self, **kw):
        # NOTE(zhaochao): getting a cluster will load instances
        # informations while getting the list of clusters won't,
        # so we cannot just reuse the reponse of getting clusters
        # for getting a cluster.
        # The following response body is almost identical to the
        # result of get_clusters, except the additional 'status'
        # and 'volume' items, so all existing unitests accessing
        # this piece of fake response will continue to work
        # without any modification.
        return (200, {}, {'cluster': {
            "instances": [
                {
                    "type": "member",
                    "id": "member-1",
                    "ip": ["10.0.0.3"],
                    "flavor": {"id": "02"},
                    "name": "test-clstr-member-1",
                    "status": "ACTIVE",
                    "volume": {"size": 2}
                },
                {
                    "type": "member",
                    "id": "member-2",
                    "ip": ["10.0.0.4"],
                    "flavor": {"id": "2"},
                    "name": "test-clstr-member-2",
                    "status": "ACTIVE",
                    "volume": {"size": 2}
                }],
            "updated": "2015-05-02T11:06:19",
            "task": {"description": "No tasks for the cluster.", "id": 1,
                     "name": "NONE"},
            "name": "test-clstr",
            "created": "2015-05-02T10:37:04",
            "datastore": {"version": "7.1", "type": "vertica"},
            "id": "cls-1234"}})

    def get_cluster_instance_modules(self, **kw):
        return (200, {}, {
            "modules": [
                {
                    "auto_apply": False,
                    "contents": None,
                    "created": "2018-04-17 05:34:02.84",
                    "datastore": "mariadb",
                    "datastore_version": "all",
                    "id": "module-1",
                    "is_admin": False,
                    "md5": "md5-1",
                    "message": "Module.V1",
                    "name": "mymod1",
                    "removed": None,
                    "status": "OK",
                    "tenant": "7f1f041fc291455b83a0b3eb98140808",
                    "type": "ping",
                    "updated": "2018-04-17 05:34:02.84",
                    "visible": True},

                {
                    "auto_apply": False,
                    "contents": None,
                    "created": "2018-04-17 05:34:02.84",
                    "datastore": "mariadb",
                    "datastore_version": "all",
                    "id": "module-2",
                    "is_admin": False,
                    "md5": "md5-2",
                    "message": "Module.V1",
                    "name": "mymod2",
                    "removed": None,
                    "status": "OK",
                    "tenant": "7f1f041fc291455b83a0b3eb98140808",
                    "type": "ping",
                    "updated": "2018-04-17 05:34:02.84",
                    "visible": True}]})

    def delete_instances_1234(self, **kw):
        return (202, {}, None)

    def delete_clusters_cls_1234(self, **kw):
        return (202, {}, None)

    def patch_instances_1234(self, **kw):
        return (202, {}, None)

    def post_clusters(self, body, **kw):
        assert_has_keys(
            body['cluster'],
            required=['instances', 'datastore', 'name'])
        if 'instances' in body['cluster']:
            for instance in body['cluster']['instances']:
                assert_has_keys(instance, required=['volume', 'flavorRef'])
        return (202, {}, self.get_clusters_cls_1234()[2])

    def post_clusters_cls_1234(self, body, **kw):
        return (202, {}, None)

    def post_instances_1234_action(self, **kw):
        return (202, {}, None)

    def get_datastores(self, **kw):
        return (200, {}, {"datastores": [
            {
                "default_version": "v-56",
                "versions": [{"id": "v-56", "name": "5.6"}],
                "id": "d-123",
                "name": "mysql"},
            {
                "default_version": "v-71",
                "versions": [{"id": "v-71", "name": "7.1"}],
                "id": "d-456",
                "name": "vertica"
            }]})

    def get_datastores_d_123(self, **kw):
        r = {'datastore': self.get_datastores()[2]['datastores'][0]}
        return (200, {}, r)

    def get_datastores_d_123_versions(self, **kw):
        return (200, {}, {"versions": [
            {
                "datastore": "d-123",
                "id": "v-56",
                "name": "5.6"}]})

    def get_datastores_d_123_versions_v_56(self, **kw):
        r = {'version': self.get_datastores_d_123_versions()[2]['versions'][0]}
        return (200, {}, r)

    def get_configurations(self, **kw):
        return (200, {}, {"configurations": [
            {
                "datastore_name": "mysql",
                "updated": "2015-05-16T10:24:29",
                "name": "test_config",
                "created": "2015-05-16T10:24:28",
                "datastore_version_name": "5.6",
                "id": "c-123",
                "values": {"max_connections": 5},
                "datastore_version_id": "d-123", "description": ''}]})

    def get_configurations_c_123(self, **kw):
        r = {'configuration': self.get_configurations()[2]['configurations'][0]
             }
        return (200, {}, r)

    def get_datastores_d_123_versions_v_156_parameters(self, **kw):
        return (200, {}, {"configuration-parameters": [
            {
                "type": "string",
                "name": "character_set_results",
                "datastore_version_id": "d-123",
                "restart_required": "false"},
            {
                "name": "connect_timeout",
                "min": 2,
                "max": 31536000,
                "restart_required": "false",
                "type": "integer",
                "datastore_version_id": "d-123"},
            {
                "type": "string",
                "name": "character_set_client",
                "datastore_version_id": "d-123",
                "restart_required": "false"},
            {
                "name": "max_connections",
                "min": 1,
                "max": 100000,
                "restart_required": "false",
                "type": "integer",
                "datastore_version_id": "d-123"}]})

    def get_datastores_d_123_versions_v_56_parameters_max_connections(self,
                                                                      **kw):
        r = self.get_datastores_d_123_versions_v_156_parameters()[
            2]['configuration-parameters'][3]
        return (200, {}, r)

    def get_configurations_c_123_instances(self, **kw):
        return (200, {}, {"instances": [
            {
                "id": "1",
                "name": "instance-1"},
            {
                "id": "2",
                "name": "instance-2"}]})

    def delete_configurations_c_123(self, **kw):
        return (202, {}, None)

    def get_instances_1234_configuration(self, **kw):
        return (200, {}, {"instance": {"configuration": {
                "tmp_table_size": "15M",
                "innodb_log_files_in_group": "2",
                "skip-external-locking": "1",
                "max_user_connections": "98"}}})

    def put_instances_1234(self, **kw):
        return (202, {}, None)

    def patch_instances_1234_metadata_key_123(self, **kw):
        return (202, {}, None)

    def put_instances_1234_metadata_key_123(self, **kw):
        return (202, {}, None)

    def delete_instances_1234_metadata_key_123(self, **kw):
        return (202, {}, None)

    def post_instances_1234_metadata_key123(self, body, **kw):
        return (202, {}, {'metadata': {}})

    def get_instances_1234_metadata(self, **kw):
        return (200, {}, {"metadata": {}})

    def get_instances_1234_metadata_key123(self, **kw):
        return (200, {}, {"metadata": {}})

    def get_modules(self, **kw):
        return (200, {}, {"modules": [
            {
                "id": "4321",
                "name": "mod1",
                "type": "ping",
                "datastore": 'all',
                "datastore_version": 'all',
                "tenant": 'all',
                "auto_apply": 0,
                "visible": 1,
                "priority_apply": 0,
                "apply_order": 5,
                "is_admin": 0},
            {
                "id": "8765",
                "name": "mod2",
                "type": "ping",
                "datastore": 'all',
                "datastore_version": 'all',
                "tenant": 'all',
                "auto_apply": 0,
                "visible": 0,
                "priority_apply": 0,
                "apply_order": 5,
                "is_admin": 1}]})

    def get_modules_4321(self, **kw):
        r = {'module': self.get_modules()[2]['modules'][0]}
        return (200, {}, r)

    def get_modules_8765(self, **kw):
        r = {'module': self.get_modules()[2]['modules'][1]}
        return (200, {}, r)

    def post_modules(self, **kw):
        r = {'module': self.get_modules()[2]['modules'][0]}
        return (200, {}, r)

    def put_modules_4321(self, **kw):
        return (200, {}, {"module": {'name': 'mod3'}})

    def delete_modules_4321(self, **kw):
        return (200, {}, None)

    def get_instances_1234_modules(self, **kw):
        return (200, {}, {"modules": [{"module": {}}]})

    def get_modules_4321_instances(self, **kw):
        if kw.get('count_only', False):
            return self.get_instance_counts()
        return self.get_instances()

    def put_modules_4321_instances(self, **kw):
        return (202, {}, None)

    def get_instances_modules(self, **kw):
        return (200, {}, None)

    def get_instances_member_1_modules(self, **kw):
        return self.get_modules()

    def get_instances_member_2_modules(self, **kw):
        return self.get_modules()

    def post_instances_1234_modules(self, **kw):
        r = {'modules': [self.get_modules()[2]['modules'][0]]}
        return (200, {}, r)

    def delete_instances_1234_modules_4321(self, **kw):
        return (200, {}, None)

    def get_limits(self, **kw):
        return (200, {}, {"limits": [
            {
                "max_backups": 50,
                "verb": "ABSOLUTE",
                "max_volumes": 20,
                "max_instances": 5}]})

    def get_backups(self, **kw):
        return (200, {}, {"backups": [
            {
                "status": "COMPLETED",
                "updated": "2015-05-16T14:23:08",
                "description": None,
                "datastore": {"version": "5.6", "type": "mysql",
                              "version_id": "v-56"},
                "id": "bk-1234",
                "size": 0.11,
                "name": "bkp_1",
                "created": "2015-05-16T14:22:28",
                "instance_id": "1234",
                "parent_id": None,
                "locationRef": ("http://backup_srvr/database_backups/"
                                "bk-1234.xbstream.gz.enc")},
            {
                "status": "COMPLETED",
                "updated": "2015-05-16T14:22:12",
                "description": None,
                "datastore": {"version": "5.6", "type": "mysql",
                              "version_id": "v-56"},
                "id": "bk-5678",
                "size": 0.11,
                "name": "test_bkp",
                "created": "2015-05-16T14:21:27",
                "instance_id": "5678",
                "parent_id": None,
                "locationRef": ("http://backup_srvr/database_backups/"
                                "bk-5678.xbstream.gz.enc")}]})

    def get_backups_bk_1234(self, **kw):
        r = {'backup': self.get_backups()[2]['backups'][0]}
        return (200, {}, r)

    def get_backups_bkp_1(self, **kw):
        r = {'backup': self.get_backups()[2]['backups'][0]}
        return (200, {}, r)

    def get_instances_1234_backups(self, **kw):
        r = {'backups': [self.get_backups()[2]['backups'][0]]}
        return (200, {}, r)

    def delete_backups_bk_1234(self, **kw):
        return (202, {}, None)

    def post_backups(self, body, **kw):
        assert_has_keys(
            body['backup'],
            required=['name'],
            optional=['description', 'parent'])
        return (202, {}, self.get_backups_bk_1234()[2])

    def get_instances_1234_databases(self, **kw):
        return (200, {}, {"databases": [
            {"name": "db_1"},
            {"name": "db_2"},
            {"name": "performance_schema"}]})

    def delete_instances_1234_databases_db_1(self, **kw):
        return (202, {}, None)

    def post_instances_1234_databases(self, body, **kw):
        assert_has_keys(
            body,
            required=['databases'])
        for database in body['databases']:
            assert_has_keys(database, required=['name'],
                            optional=['character_set', 'collate'])
        return (202, {},
                self.get_instances_1234_databases()[2]['databases'][0])

    def get_instances_1234_users(self, **kw):
        return (200, {}, {"users": [
            {"host": "%", "name": "jacob", "databases": []},
            {"host": "%", "name": "rocky", "databases": []},
            {"host": "%", "name": "harry", "databases": [{"name": "db1"}]}]})

    def get_instances_1234_users_jacob(self, **kw):
        r = {'user': self.get_instances_1234_users()[2]['users'][0]}
        return (200, {}, r)

    def delete_instances_1234_users_jacob(self, **kw):
        return (202, {}, None)

    def post_instances_1234_users(self, body, **kw):
        assert_has_keys(
            body,
            required=['users'])
        for database in body['users']:
            assert_has_keys(database, required=['name', 'password'],
                            optional=['databases'])
        return (202, {}, self.get_instances_1234_users()[2]['users'][0])

    def get_instances_1234_users_jacob_databases(self, **kw):
        r = {'databases': [
            self.get_instances_1234_databases()[2]['databases'][0],
            self.get_instances_1234_databases()[2]['databases'][1]]}
        return (200, {}, r)

    def put_instances_1234_users_jacob(self, **kw):
        return (202, {}, None)

    def put_instances_1234_users_jacob_databases(self, **kw):
        return (202, {}, None)

    def delete_instances_1234_users_jacob_databases_db1(self, **kw):
        return (202, {}, None)

    def post_instances_1234_root(self, **kw):
        return (202, {}, {"user": {"password": "password", "name": "root"}})

    def post_clusters_cls_1234_root(self, **kw):
        return (202, {}, {"user": {"password": "password", "name": "root"}})

    def delete_instances_1234_root(self, **kw):
        return (202, {}, None)

    def get_instances_1234_root(self, **kw):
        return (200, {}, {"rootEnabled": 'True'})

    def get_instances_master_1(self, **kw):
        return (200, {}, {"instance": {"id": 'myid'}})

    def get_clusters_cls_1234_root(self, **kw):
        return (200, {}, {"rootEnabled": 'True'})

    def get_security_groups(self, **kw):
        return (200, {}, {"security_groups": [
            {
                "instance_id": "1234",
                "updated": "2015-05-16T17:29:45",
                "name": "SecGroup_1234",
                "created": "2015-05-16T17:29:45",
                "rules": [{"to_port": 3306, "cidr": "0.0.0.0/0",
                           "from_port": 3306,
                           "protocol": "tcp", "id": "1"}],
                "id": "2",
                "description": "Security Group for 1234"}]})

    def get_security_groups_2(self, **kw):
        r = {'security_group': self.get_security_groups()[
            2]['security_groups'][0]}
        return (200, {}, r)

    def delete_security_group_rules_2(self, **kw):
        return (202, {}, None)

    def post_security_group_rules(self, body, **kw):
        assert_has_keys(body['security_group_rule'], required=['cidr', 'cidr'])
        return (202, {}, {"security_group_rule": [
            {
                "from_port": 3306,
                "protocol": "tcp",
                "created": "2015-05-16T17:55:05",
                "to_port": 3306,
                "security_group_id": "2",
                "cidr": "15.0.0.0/24", "id": 3}]})

    def get_quotas(self, **kw):
        return (200, {}, {"quotas": [
            {
                "reserved": 1,
                "resource": "instances",
                "limit": 10,
                "in_use": 2
            },
            {
                "reserved": 3,
                "resource": "backups",
                "limit": 50,
                "in_use": 4
            },
            {
                "reserved": 5,
                "resource": "volumes",
                "limit": 40,
                "in_use": 6
            }]})

    def update_instances_quota(self, **kw):
        return (200, {}, {"quotas": {"instances": 51}})

    def get_logs(self, **kw):
        return (200, {}, {"logs": [
            {
                "name": "general",
                "type": "USER",
                "status": "Partial",
                "published": "128",
                "pending": "4096",
                "container": "data_logs",
                "prefix": "mysql-general",
                "metafile": "mysql-general_metafile"
            },
            {
                "name": "slow_query",
                "type": "USER",
                "status": "Ready",
                "published": "0",
                "pending": "128",
                "container": "None",
                "prefix": "None",
                "metafile": "mysql-slow_query_metafile"}]})
