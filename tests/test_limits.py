from testtools import TestCase
from mock import Mock
from reddwarfclient import limits

"""
This class tests the calling code for the Limits API
"""


class LimitsTest(TestCase):

    def setUp(self):
        super(LimitsTest, self).setUp()
        self.limits = limits.Limits(Mock())
        self.limits.api.client = Mock()

    def tearDown(self):
        super(LimitsTest, self).tearDown()

    def test_index(self):
        RESPONSE_KEY = "limits"

        resp = Mock()
        resp.status = 200
        body = {RESPONSE_KEY: {'rate': [
            {'limit': [
                {
                    "next-available": "2013-02-26T00:00:13Z",
                    "remaining": 100,
                    "unit": "MINUTE",
                    "value": 100,
                    "verb": "POST"
                },
                {
                    "next-available": "2013-02-26T00:00:13Z",
                    "remaining": 100,
                    "unit": "MINUTE",
                    "value": 100,
                    "verb": "PUT"
                },
                {
                    "next-available": "2013-02-26T00:00:13Z",
                    "remaining": 100,
                    "unit": "MINUTE",
                    "value": 100,
                    "verb": "DELETE"
                },
                {
                    "next-available": "2013-02-26T00:00:13Z",
                    "remaining": 99,
                    "unit": "MINUTE",
                    "value": 100,
                    "verb": "GET"
                }
                       ]
            }]}}
        response = (resp, body)

        mock_get = Mock(return_value=response)
        self.limits.api.client.get = mock_get
        self.assertIsNotNone(self.limits.index())
        mock_get.assert_called_once_with("/limits")

    def test_index_errors(self):
        status_list = [400, 401, 403, 404, 408, 409, 413, 500, 501]
        for status_code in status_list:
            self._check_error_response(status_code)

    def _check_error_response(self, status_code):
        RESPONSE_KEY = "limits"

        resp = Mock()
        resp.status = status_code
        body = {RESPONSE_KEY: {'rate': [
            {'limit': []
            }]}}
        response = (resp, body)

        mock_get = Mock(return_value=response)
        self.limits.api.client.get = mock_get
        self.assertRaises(Exception, self.limits.index)
