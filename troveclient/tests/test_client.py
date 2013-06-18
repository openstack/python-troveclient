import contextlib
import os
import logging
import httplib2
import time

from testtools import TestCase
from mock import Mock

from troveclient import client
from troveclient import exceptions
from troveclient import utils

"""
Unit tests for client.py
"""


class ClientTest(TestCase):

    def test_log_to_streamhandler(self):
        client.log_to_streamhandler()
        self.assertTrue(client._logger.level == logging.DEBUG)


class TroveHTTPClientTest(TestCase):

    def setUp(self):
        super(TroveHTTPClientTest, self).setUp()
        self.orig__init = client.TroveHTTPClient.__init__
        client.TroveHTTPClient.__init__ = Mock(return_value=None)
        self.hc = client.TroveHTTPClient()
        self.hc.auth_token = "test-auth-token"
        self.hc.service_url = "test-service-url/"
        self.hc.tenant = "test-tenant"

        self.__debug_lines = list()

        self.orig_client__logger = client._logger
        client._logger = Mock()

        self.orig_time = time.time
        self.orig_htttp_request = httplib2.Http.request

    def tearDown(self):
        super(TroveHTTPClientTest, self).tearDown()
        client.TroveHTTPClient.__init__ = self.orig__init
        client._logger = self.orig_client__logger
        time.time = self.orig_time
        httplib2.Http.request = self.orig_htttp_request

    def side_effect_func_for_moc_debug(self, s, *args):
        self.__debug_lines.append(s)

    def test___init__(self):
        client.TroveHTTPClient.__init__ = self.orig__init

        user = "test-user"
        password = "test-password"
        tenant = "test-tenant"
        auth_url = "http://test-auth-url/"
        service_name = None

        # when there is no auth_strategy provided
        self.assertRaises(ValueError, client.TroveHTTPClient, user,
                          password, tenant, auth_url, service_name)

        hc = client.TroveHTTPClient(user, password, tenant, auth_url,
                                       service_name, auth_strategy="fake")
        self.assertEqual("http://test-auth-url", hc.auth_url)

        #  auth_url is none
        hc = client.TroveHTTPClient(user, password, tenant, None,
                                       service_name, auth_strategy="fake")
        self.assertEqual(None, hc.auth_url)

    def test_get_timings(self):
        self.hc.times = ["item1", "item2"]
        self.assertEqual(2, len(self.hc.get_timings()))
        self.assertEqual("item1", self.hc.get_timings()[0])
        self.assertEqual("item2", self.hc.get_timings()[1])

    def test_http_log(self):
        self.hc.simple_log = Mock(return_value=None)
        self.hc.pretty_log = Mock(return_value=None)

        client.RDC_PP = False
        self.hc.http_log(None, None, None, None)
        self.assertEqual(1, self.hc.simple_log.call_count)

        client.RDC_PP = True
        self.hc.http_log(None, None, None, None)
        self.assertEqual(1, self.hc.pretty_log.call_count)

    def test_simple_log(self):
        client._logger.isEnabledFor = Mock(return_value=False)
        self.hc.simple_log(None, None, None, None)
        self.assertEqual(0, len(self.__debug_lines))

        client._logger.isEnabledFor = Mock(return_value=True)
        se = self.side_effect_func_for_moc_debug
        client._logger.debug = Mock(side_effect=se)
        self.hc.simple_log(['item1', 'GET', 'item3', 'POST', 'item5'],
                           {'headers': {'e1': 'e1-v', 'e2': 'e2-v'},
                            'body': 'body'}, None, None)
        self.assertEqual(3, len(self.__debug_lines))
        self.assertTrue(self.__debug_lines[0].startswith('REQ: curl -i'))
        self.assertTrue(self.__debug_lines[1].startswith('REQ BODY:'))
        self.assertTrue(self.__debug_lines[2].startswith('RESP:'))

    def test_pretty_log(self):
        client._logger.isEnabledFor = Mock(return_value=False)
        self.hc.pretty_log(None, None, None, None)
        self.assertEqual(0, len(self.__debug_lines))

        client._logger.isEnabledFor = Mock(return_value=True)
        se = self.side_effect_func_for_moc_debug
        client._logger.debug = Mock(side_effect=se)
        self.hc.pretty_log(['item1', 'GET', 'item3', 'POST', 'item5'],
                           {'headers': {'e1': 'e1-v', 'e2': 'e2-v'},
                            'body': 'body'}, None, None)
        self.assertEqual(5, len(self.__debug_lines))
        self.assertTrue(self.__debug_lines[0].startswith('REQUEST:'))
        self.assertTrue(self.__debug_lines[1].startswith('curl -i'))
        self.assertTrue(self.__debug_lines[2].startswith('BODY:'))
        self.assertTrue(self.__debug_lines[3].startswith('RESPONSE HEADERS:'))
        self.assertTrue(self.__debug_lines[4].startswith('RESPONSE BODY'))

        # no body case
        self.__debug_lines = list()
        self.hc.pretty_log(['item1', 'GET', 'item3', 'POST', 'item5'],
                           {'headers': {'e1': 'e1-v', 'e2': 'e2-v'}},
                           None, None)
        self.assertEqual(4, len(self.__debug_lines))
        self.assertTrue(self.__debug_lines[0].startswith('REQUEST:'))
        self.assertTrue(self.__debug_lines[1].startswith('curl -i'))
        self.assertTrue(self.__debug_lines[2].startswith('RESPONSE HEADERS:'))
        self.assertTrue(self.__debug_lines[3].startswith('RESPONSE BODY'))

    def test_request(self):
        self.hc.USER_AGENT = "user-agent"
        resp = Mock()
        body = Mock()
        resp.status = 200
        httplib2.Http.request = Mock(return_value=(resp, body))
        self.hc.morph_response_body = Mock(return_value=body)
        r, b = self.hc.request()
        self.assertEqual(resp, r)
        self.assertEqual(body, b)
        self.assertEqual((resp, body), self.hc.last_response)

        httplib2.Http.request = Mock(return_value=(resp, None))
        r, b = self.hc.request()
        self.assertEqual(resp, r)
        self.assertEqual(None, b)

        status_list = [400, 401, 403, 404, 408, 409, 413, 500, 501]
        for status in status_list:
            resp.status = status
            self.assertRaises(Exception, self.hc.request)

        exception = exceptions.ResponseFormatError
        self.hc.morph_response_body = Mock(side_effect=exception)
        self.assertRaises(Exception, self.hc.request)

    def test_raise_error_from_status(self):
        resp = Mock()
        resp.status = 200
        self.hc.raise_error_from_status(resp, Mock())

        status_list = [400, 401, 403, 404, 408, 409, 413, 500, 501]
        for status in status_list:
            resp.status = status
            self.assertRaises(Exception,
                              self.hc.raise_error_from_status, resp, Mock())

    def test_morph_request(self):
        kwargs = dict()
        kwargs['headers'] = dict()
        kwargs['body'] = ['body', {'item1': 'value1'}]
        self.hc.morph_request(kwargs)
        expected = {'body': '["body", {"item1": "value1"}]',
                    'headers': {'Content-Type': 'application/json',
                                'Accept': 'application/json'}}
        self.assertEqual(expected, kwargs)

    def test_morph_response_body(self):
        body_string = '["body", {"item1": "value1"}]'
        expected = ['body', {'item1': 'value1'}]
        self.assertEqual(expected, self.hc.morph_response_body(body_string))
        body_string = '["body", {"item1": }]'
        self.assertRaises(exceptions.ResponseFormatError,
                          self.hc.morph_response_body, body_string)

    def test__time_request(self):
        self.__time = 0

        def side_effect_func():
            self.__time = self.__time + 1
            return self.__time

        time.time = Mock(side_effect=side_effect_func)
        self.hc.request = Mock(return_value=("mock-response", "mock-body"))
        self.hc.times = list()
        resp, body = self.hc._time_request("test-url", "Get")
        self.assertEqual(("mock-response", "mock-body"), (resp, body))
        self.assertEqual([('Get test-url', 1, 2)], self.hc.times)

    def mock_time_request_func(self):
        def side_effect_func(url, method, **kwargs):
            return url, method
        self.hc._time_request = Mock(side_effect=side_effect_func)

    def test__cs_request(self):
        self.mock_time_request_func()
        resp, body = self.hc._cs_request("test-url", "GET")
        self.assertEqual(('test-service-url/test-url', 'GET'), (resp, body))

        self.hc.authenticate = Mock(side_effect=ValueError)
        self.hc.auth_token = None
        self.hc.service_url = None
        self.assertRaises(ValueError, self.hc._cs_request, "test-url", "GET")

        self.hc.authenticate = Mock(return_value=None)
        self.hc.service_url = "test-service-url/"

        def side_effect_func_time_req(url, method, **kwargs):
            raise exceptions.Unauthorized(None)

        self.hc._time_request = Mock(side_effect=side_effect_func_time_req)
        self.assertRaises(exceptions.Unauthorized,
                          self.hc._cs_request, "test-url", "GET")

    def test_get(self):
        self.mock_time_request_func()
        resp, body = self.hc.get("test-url")
        self.assertEqual(("test-service-url/test-url", "GET"), (resp, body))

    def test_post(self):
        self.mock_time_request_func()
        resp, body = self.hc.post("test-url")
        self.assertEqual(("test-service-url/test-url", "POST"), (resp, body))

    def test_put(self):
        self.mock_time_request_func()
        resp, body = self.hc.put("test-url")
        self.assertEqual(("test-service-url/test-url", "PUT"), (resp, body))

    def test_delete(self):
        self.mock_time_request_func()
        resp, body = self.hc.delete("test-url")
        self.assertEqual(("test-service-url/test-url", "DELETE"), (resp, body))

    def test_authenticate(self):
        self.hc.authenticator = Mock()
        catalog = Mock()
        catalog.get_public_url = Mock(return_value="public-url")
        catalog.get_management_url = Mock(return_value="mng-url")
        catalog.get_token = Mock(return_value="test-token")

        self.__auth_calls = []

        def side_effect_func(token, url):
            self.__auth_calls = [token, url]

        self.hc.authenticate_with_token = Mock(side_effect=side_effect_func)
        self.hc.authenticator.authenticate = Mock(return_value=catalog)
        self.hc.endpoint_type = "publicURL"
        self.hc.authenticate()
        self.assertEqual(["test-token", None],
                         self.__auth_calls)

        self.__auth_calls = []
        self.hc.service_url = None
        self.hc.authenticate()
        self.assertEqual(["test-token", "public-url"], self.__auth_calls)

        self.__auth_calls = []
        self.hc.endpoint_type = "adminURL"
        self.hc.authenticate()
        self.assertEqual(["test-token", "mng-url"], self.__auth_calls)

    def test_authenticate_with_token(self):
        self.hc.service_url = None
        self.assertRaises(exceptions.ServiceUrlNotGiven,
                          self.hc.authenticate_with_token, "token", None)
        self.hc.authenticate_with_token("token", "test-url")
        self.assertEqual("test-url", self.hc.service_url)
        self.assertEqual("token", self.hc.auth_token)


class DbaasTest(TestCase):

    def setUp(self):
        super(DbaasTest, self).setUp()
        self.orig__init = client.TroveHTTPClient.__init__
        client.TroveHTTPClient.__init__ = Mock(return_value=None)
        self.dbaas = client.Dbaas("user", "api-key")

    def tearDown(self):
        super(DbaasTest, self).tearDown()
        client.TroveHTTPClient.__init__ = self.orig__init

    def test___init__(self):
        client.TroveHTTPClient.__init__ = Mock(return_value=None)
        self.assertNotEqual(None, self.dbaas.mgmt)

    def test_set_management_url(self):
        self.dbaas.set_management_url("test-management-url")
        self.assertEqual("test-management-url",
                         self.dbaas.client.management_url)

    def test_get_timings(self):
        __timings = {'start': 1, 'end': 2}
        self.dbaas.client.get_timings = Mock(return_value=__timings)
        self.assertEqual(__timings, self.dbaas.get_timings())

    def test_authenticate(self):
        mock_auth = Mock(return_value=None)
        self.dbaas.client.authenticate = mock_auth
        self.dbaas.authenticate()
        self.assertEqual(1, mock_auth.call_count)
