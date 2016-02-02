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

import fixtures
from keystoneclient import adapter
import logging
import mock
import requests
import testtools

from troveclient import client as other_client
from troveclient import exceptions
from troveclient.openstack.common.apiclient import client
from troveclient import service_catalog
import troveclient.v1.client


class ClientTest(testtools.TestCase):

    def test_get_client_class_v1(self):
        version_map = other_client.get_version_map()
        output = client.BaseClient.get_class('database',
                                             '1.0', version_map)
        self.assertEqual(troveclient.v1.client.Client, output)

    def test_get_client_class_unknown(self):
        version_map = other_client.get_version_map()
        self.assertRaises(exceptions.UnsupportedVersion,
                          client.BaseClient.get_class, 'database',
                          '0', version_map)

    def test_client_with_auth_system_without_auth_plugin(self):
        self.assertRaisesRegexp(
            exceptions.AuthSystemNotFound, "AuthSystemNotFound: 'something'",
            other_client.HTTPClient, user='user', password='password',
            projectid='project', timeout=2, auth_url="http://www.blah.com",
            auth_system='something')

    def test_client_with_auth_system_without_endpoint(self):
        auth_plugin = mock.Mock()
        auth_plugin.get_auth_url = mock.Mock(return_value=None)
        self.assertRaises(
            exceptions.EndpointNotFound,
            other_client.HTTPClient, user='user', password='password',
            projectid='project', timeout=2, auth_plugin=auth_plugin,
            auth_url=None, auth_system='something')

    def test_client_with_timeout(self):
        instance = other_client.HTTPClient(user='user',
                                           password='password',
                                           projectid='project',
                                           timeout=2,
                                           auth_url="http://www.blah.com",
                                           insecure=True)
        self.assertEqual(2, instance.timeout)
        mock_request = mock.Mock()
        mock_request.return_value = requests.Response()
        mock_request.return_value.status_code = 200
        mock_request.return_value.headers = {
            'x-server-management-url': 'blah.com',
            'x-auth-token': 'blah',
        }
        with mock.patch('requests.request', mock_request):
            instance.authenticate()
            requests.request.assert_called_with(
                mock.ANY, mock.ANY, timeout=2, headers=mock.ANY,
                verify=mock.ANY)

    def test_client_unauthorized(self):
        instance = other_client.HTTPClient(user='user',
                                           password='password',
                                           projectid='project',
                                           timeout=2,
                                           auth_url="http://www.blah.com",
                                           cacert=mock.Mock())
        instance.auth_token = 'foobar'
        instance.management_url = 'http://example.com'
        instance.get_service_url = mock.Mock(return_value='http://example.com')
        instance.version = 'v2.0'
        mock_request = mock.Mock()
        mock_request.side_effect = other_client.exceptions.Unauthorized(401)
        with mock.patch('requests.request', mock_request):
            self.assertRaises(
                exceptions.Unauthorized, instance.get, '/instances')

    def test_client_bad_request(self):
        instance = other_client.HTTPClient(user='user',
                                           password='password',
                                           projectid='project',
                                           timeout=2,
                                           auth_url="http://www.blah.com")
        instance.auth_token = 'foobar'
        instance.management_url = 'http://example.com'
        instance.get_service_url = mock.Mock(return_value='http://example.com')
        instance.version = 'v2.0'
        mock_request = mock.Mock()
        mock_request.side_effect = other_client.exceptions.BadRequest()
        with mock.patch('requests.request', mock_request):
            self.assertRaises(
                exceptions.BadRequest, instance.get, '/instances')

    def test_client_with_client_exception(self):
        instance = other_client.HTTPClient(user='user',
                                           password='password',
                                           projectid='project',
                                           timeout=2,
                                           auth_url="http://www.blah.com",
                                           retries=2)
        instance.auth_token = 'foobar'
        instance.management_url = 'http://example.com'
        instance.get_service_url = mock.Mock(return_value='http://example.com')
        instance.version = 'v2.0'
        mock_request = mock.Mock()
        mock_request.side_effect = other_client.exceptions.ClientException()
        type(mock_request.side_effect).code = mock.PropertyMock(
            side_effect=[501, 111])
        with mock.patch('requests.request', mock_request):
            self.assertRaises(
                exceptions.ClientException, instance.get, '/instances')

    def test_client_connection_error(self):
        instance = other_client.HTTPClient(user='user',
                                           password='password',
                                           projectid='project',
                                           timeout=2,
                                           auth_url="http://www.blah.com",
                                           retries=2)
        instance.auth_token = 'foobar'
        instance.management_url = 'http://example.com'
        instance.get_service_url = mock.Mock(return_value='http://example.com')
        instance.version = 'v2.0'
        mock_request = mock.Mock()
        mock_request.side_effect = requests.exceptions.ConnectionError(
            'connection refused')
        with mock.patch('requests.request', mock_request):
            self.assertRaisesRegexp(
                exceptions.ClientException,
                'Unable to establish connection: connection refused',
                instance.get, '/instances')

    @mock.patch.object(other_client.HTTPClient, 'request',
                       return_value=(200, "{'versions':[]}"))
    def _check_version_url(self, management_url, version_url, mock_request):
        projectid = '25e469aa1848471b875e68cde6531bc5'
        instance = other_client.HTTPClient(user='user',
                                           password='password',
                                           projectid=projectid,
                                           auth_url="http://www.blah.com")
        instance.auth_token = 'foobar'
        instance.management_url = management_url % projectid
        mock_get_service_url = mock.Mock(return_value=instance.management_url)
        instance.get_service_url = mock_get_service_url
        instance.version = 'v2.0'

        # If passing None as the part of url, a client accesses the url which
        # doesn't include "v2/<projectid>" for getting API version info.
        instance.get('')
        mock_request.assert_called_once_with(instance.management_url, 'GET',
                                             headers=mock.ANY)
        mock_request.reset_mock()

        # Otherwise, a client accesses the url which includes "v2/<projectid>".
        instance.get('/instances')
        url = instance.management_url + '/instances'
        mock_request.assert_called_once_with(url, 'GET', headers=mock.ANY)

    def test_client_version_url(self):
        self._check_version_url('http://foo.com/v1/%s', 'http://foo.com/')

    def test_client_version_url_with_tenant_name(self):
        self._check_version_url('http://foo.com/trove/v1/%s',
                                'http://foo.com/trove/')

    def test_log_req(self):
        logger = self.useFixture(
            fixtures.FakeLogger(
                name='troveclient.client',
                format="%(message)s",
                level=logging.DEBUG,
                nuke_handlers=True
            )
        )
        cs = other_client.HTTPClient(user='user',
                                     password='password',
                                     projectid=None,
                                     auth_url="http://www.blah.com",
                                     http_log_debug=True)
        cs.http_log_req(('/foo', 'GET'), {'headers': {}})
        cs.http_log_req(('/foo', 'GET'),
                        {'headers': {'X-Auth-Token': 'totally_bogus'}})
        cs.http_log_req(
            ('/foo', 'GET'),
            {'headers': {},
             'data': '{"auth": {"passwordCredentials": '
             '{"password": "password"}}}'})

        output = logger.output.split('\n')

        self.assertIn("REQ: curl -i /foo -X GET", output)
        self.assertIn(
            "REQ: curl -i /foo -X GET -H "
            '"X-Auth-Token: totally_bogus"',
            output)
        self.assertIn(
            "REQ: curl -i /foo -X GET -d "
            '\'{"auth": {"passwordCredentials": {"password":'
            ' "password"}}}\'',
            output)

    @mock.patch.object(service_catalog, 'ServiceCatalog')
    def test_client_auth_token(self, mock_service_catalog):
        auth_url = 'http://www.blah.com'
        proxy_token = 'foobar'
        proxy_tenant_id = 'user'
        mock_service_catalog.return_value.get_token = mock.Mock(
            return_value=proxy_token)
        instance = other_client.HTTPClient(proxy_token=proxy_token,
                                           proxy_tenant_id=proxy_tenant_id,
                                           user=None,
                                           password=None,
                                           tenant_id=proxy_tenant_id,
                                           projectid=None,
                                           timeout=2,
                                           auth_url=auth_url)
        instance.management_url = 'http://example.com'
        instance.get_service_url = mock.Mock(return_value='http://example.com')
        instance.version = 'v2.0'
        mock_request = mock.Mock()
        mock_request.return_value = requests.Response()
        mock_request.return_value.status_code = 200
        mock_request.return_value.headers = {
            'x-server-management-url': 'blah.com',
            'x-auth-token': 'blah',
        }

        with mock.patch('requests.request', mock_request):
            instance.authenticate()
            mock_request.assert_called_with(
                'GET', auth_url + '/tokens/foobar?belongsTo=user',
                headers={'User-Agent': 'python-troveclient',
                         'Accept': 'application/json',
                         'X-Auth-Token': proxy_token},
                timeout=2, verify=True)

    @mock.patch.object(service_catalog, 'ServiceCatalog', side_effect=KeyError)
    def test_client_auth_token_authorization_failure(self,
                                                     mock_service_catalog):
        auth_url = 'http://www.blah.com'
        proxy_token = 'foobar'
        proxy_tenant_id = 'user'
        mock_service_catalog.return_value.get_token = mock.Mock(
            return_value=proxy_token)
        instance = other_client.HTTPClient(proxy_token=proxy_token,
                                           proxy_tenant_id=proxy_tenant_id,
                                           user=None,
                                           password=None,
                                           tenant_id=proxy_tenant_id,
                                           projectid=None,
                                           timeout=2,
                                           auth_url=auth_url)
        instance.management_url = 'http://example.com'
        instance.get_service_url = mock.Mock(return_value='http://example.com')
        instance.version = 'v2.0'
        mock_request = mock.Mock()
        mock_request.return_value = requests.Response()
        mock_request.return_value.status_code = 200
        mock_request.return_value.headers = {
            'x-server-management-url': 'blah.com',
            'x-auth-token': 'blah',
        }

        with mock.patch('requests.request', mock_request):
            self.assertRaises(exceptions.AuthorizationFailure,
                              instance.authenticate)

    @mock.patch.object(service_catalog, 'ServiceCatalog',
                       side_effect=other_client.exceptions.EndpointNotFound)
    def test_client_auth_token_endpoint_not_found(self, mock_service_catalog):
        auth_url = 'http://www.blah.com'
        proxy_token = 'foobar'
        proxy_tenant_id = 'user'
        mock_service_catalog.return_value.get_token = mock.Mock(
            return_value=proxy_token)
        instance = other_client.HTTPClient(proxy_token=proxy_token,
                                           proxy_tenant_id=proxy_tenant_id,
                                           user=None,
                                           password=None,
                                           tenant_id=proxy_tenant_id,
                                           projectid=None,
                                           timeout=2,
                                           auth_url=auth_url)
        instance.management_url = 'http://example.com'
        instance.get_service_url = mock.Mock(return_value='http://example.com')
        instance.version = 'v2.0'
        mock_request = mock.Mock()
        mock_request.return_value = requests.Response()
        mock_request.return_value.status_code = 200
        mock_request.return_value.headers = {
            'x-server-management-url': 'blah.com',
            'x-auth-token': 'blah',
        }

        with mock.patch('requests.request', mock_request):
            self.assertRaises(exceptions.EndpointNotFound,
                              instance.authenticate)

    @mock.patch.object(service_catalog, 'ServiceCatalog')
    def test_client_auth_token_v1_auth_failure(self, mock_service_catalog):
        auth_url = 'http://www.blah.com'
        proxy_token = 'foobar'
        proxy_tenant_id = 'user'
        mock_service_catalog.return_value.get_token = mock.Mock(
            return_value=proxy_token)
        instance = other_client.HTTPClient(proxy_token=proxy_token,
                                           proxy_tenant_id=proxy_tenant_id,
                                           user=None,
                                           password=None,
                                           tenant_id=proxy_tenant_id,
                                           projectid=None,
                                           timeout=2,
                                           auth_url=auth_url)
        instance.management_url = 'http://example.com'
        instance.get_service_url = mock.Mock(return_value='http://example.com')
        instance.version = 'v1.0'
        mock_request = mock.Mock()
        mock_request.return_value = requests.Response()
        mock_request.return_value.status_code = 200
        mock_request.return_value.headers = {
            'x-server-management-url': 'blah.com',
            'x-auth-token': 'blah',
        }

        with mock.patch('requests.request', mock_request):
            self.assertRaises(exceptions.NoTokenLookupException,
                              instance.authenticate)

    @mock.patch.object(service_catalog, 'ServiceCatalog')
    def test_client_auth_token_v1_auth(self, mock_service_catalog):
        auth_url = 'http://www.blah.com'
        proxy_token = 'foobar'
        mock_service_catalog.return_value.get_token = mock.Mock(
            return_value=proxy_token)
        instance = other_client.HTTPClient(user='user',
                                                password='password',
                                                projectid='projectid',
                                                timeout=2,
                                                auth_url=auth_url)
        instance.management_url = 'http://example.com'
        instance.get_service_url = mock.Mock(return_value='http://example.com')
        instance.version = 'v1.0'
        mock_request = mock.Mock()
        mock_request.return_value = requests.Response()
        mock_request.return_value.status_code = 200
        mock_request.return_value.headers = {
            'x-server-management-url': 'blah.com',
        }
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json',
                   'User-Agent': 'python-troveclient'}
        with mock.patch('requests.request', mock_request):
            instance.authenticate()
            called_args, called_kwargs = mock_request.call_args
            self.assertEqual(('POST', 'http://www.blah.com/v2.0/tokens'),
                             called_args)
            self.assertDictEqual(headers, called_kwargs['headers'])

    def test_client_get(self):
        auth_url = 'http://www.blah.com'
        instance = other_client.HTTPClient(user='user',
                                                password='password',
                                                projectid='project_id',
                                                timeout=2,
                                                auth_url=auth_url)
        instance._cs_request = mock.Mock()

        instance.get('clusters')
        instance._cs_request.assert_called_with('clusters', 'GET')

    def test_client_patch(self):
        auth_url = 'http://www.blah.com'
        body = mock.Mock()
        instance = other_client.HTTPClient(user='user',
                                                password='password',
                                                projectid='project_id',
                                                timeout=2,
                                                auth_url=auth_url)
        instance._cs_request = mock.Mock()

        instance.patch('instances/dummy-instance-id', body=body)
        instance._cs_request.assert_called_with(
            'instances/dummy-instance-id', 'PATCH', body=body)

    def test_client_post(self):
        auth_url = 'http://www.blah.com'
        body = {"add_shard": {}}
        instance = other_client.HTTPClient(user='user',
                                                password='password',
                                                projectid='project_id',
                                                timeout=2,
                                                auth_url=auth_url)
        instance._cs_request = mock.Mock()

        instance.post('clusters/dummy-cluster-id', body=body)
        instance._cs_request.assert_called_with(
            'clusters/dummy-cluster-id', 'POST', body=body)

    def test_client_put(self):
        auth_url = 'http://www.blah.com'
        body = {"user": {"password": "new_password"}}
        instance = other_client.HTTPClient(user='user',
                                                password='password',
                                                projectid='project_id',
                                                timeout=2,
                                                auth_url=auth_url)
        instance._cs_request = mock.Mock()

        instance.put('instances/dummy-instance-id/user/dummy-user', body=body)
        instance._cs_request.assert_called_with(
            'instances/dummy-instance-id/user/dummy-user', 'PUT', body=body)

    def test_client_delete(self):
        auth_url = 'http://www.blah.com'
        instance = other_client.HTTPClient(user='user',
                                                password='password',
                                                projectid='project_id',
                                                timeout=2,
                                                auth_url=auth_url)
        instance._cs_request = mock.Mock()

        instance.delete('/backups/dummy-backup-id')
        instance._cs_request.assert_called_with('/backups/dummy-backup-id',
                                                'DELETE')

    @mock.patch.object(adapter.LegacyJsonAdapter, 'request')
    def test_database_service_name(self, m_request):
        m_request.return_value = (mock.MagicMock(status_code=200), None)

        client = other_client.SessionClient(session=mock.MagicMock(),
                                            auth=mock.MagicMock())
        client.request("http://no.where", 'GET')
        self.assertIsNone(client.database_service_name)

        client = other_client.SessionClient(session=mock.MagicMock(),
                                            auth=mock.MagicMock(),
                                            database_service_name='myservice')
        client.request("http://no.where", 'GET')
        self.assertEqual('myservice', client.database_service_name)

    @mock.patch.object(adapter.LegacyJsonAdapter, 'request')
    @mock.patch.object(adapter.LegacyJsonAdapter, 'get_endpoint',
                       return_value=None)
    def test_error_sessionclient(self, m_end_point, m_request):
        m_request.return_value = (mock.MagicMock(status_code=200), None)

        self.assertRaises(exceptions.EndpointNotFound,
                          other_client.SessionClient,
                          session=mock.MagicMock(),
                          auth=mock.MagicMock())

    def test_construct_http_client(self):
        mock_request = mock.Mock()
        mock_request.return_value = requests.Response()
        mock_request.return_value.status_code = 200
        mock_request.return_value.headers = {
            'x-server-management-url': 'blah.com',
            'x-auth-token': 'blah',
        }
        with mock.patch('requests.request', mock_request):
            self.assertIsInstance(other_client._construct_http_client(),
                                  other_client.HTTPClient)
            self.assertIsInstance(
                other_client._construct_http_client(session=mock.Mock(),
                                                    auth=mock.Mock()),
                other_client.SessionClient)
