from testtools import TestCase
from mock import Mock
from troveclient import limits


class LimitsTest(TestCase):
    """
    This class tests the calling code for the Limits API
    """

    def setUp(self):
        super(LimitsTest, self).setUp()
        self.limits = limits.Limits(Mock())
        self.limits.api.client = Mock()

    def tearDown(self):
        super(LimitsTest, self).tearDown()

    def test_list(self):
        resp = Mock()
        resp.status = 200
        body = {"limits":
                [
                    {'maxTotalInstances': 55,
                     'verb': 'ABSOLUTE',
                     'maxTotalVolumes': 100},
                    {'regex': '.*',
                     'nextAvailable': '2011-07-21T18:17:06Z',
                     'uri': '*',
                     'value': 10,
                     'verb': 'POST',
                     'remaining': 2, 'unit': 'MINUTE'},
                    {'regex': '.*',
                     'nextAvailable': '2011-07-21T18:17:06Z',
                     'uri': '*',
                     'value': 10,
                     'verb': 'PUT',
                     'remaining': 2,
                     'unit': 'MINUTE'},
                    {'regex': '.*',
                     'nextAvailable': '2011-07-21T18:17:06Z',
                     'uri': '*',
                     'value': 10,
                     'verb': 'DELETE',
                     'remaining': 2,
                     'unit': 'MINUTE'},
                    {'regex': '.*',
                     'nextAvailable': '2011-07-21T18:17:06Z',
                     'uri': '*',
                     'value': 10,
                     'verb': 'GET',
                     'remaining': 2, 'unit': 'MINUTE'}]}
        response = (resp, body)

        mock_get = Mock(return_value=response)
        self.limits.api.client.get = mock_get
        self.assertIsNotNone(self.limits.list())
        mock_get.assert_called_once_with("/limits")

    def test_list_errors(self):
        status_list = [400, 401, 403, 404, 408, 409, 413, 500, 501]
        for status_code in status_list:
            self._check_error_response(status_code)

    def _check_error_response(self, status_code):
        RESPONSE_KEY = "limits"

        resp = Mock()
        resp.status = status_code
        body = {RESPONSE_KEY: {
            'absolute': {},
            'rate': [
            {'limit': []
             }]}}
        response = (resp, body)

        mock_get = Mock(return_value=response)
        self.limits.api.client.get = mock_get
        self.assertRaises(Exception, self.limits.list)
