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

import json

from troveclient.apiclient import exceptions
from troveclient.tests import utils as test_utils


class ExceptionsTestCase(test_utils.TestCase):

    def _test_from_response(self, body):
        data = {
            'status_code': 503,
            'headers': {
                'Content-Type': 'application/json',
                'x-compute-request-id': (
                    'req-65d6443c-5910-4eb4-b48a-e69849c26836'),
            },
            'text': json.dumps(body)
        }
        response = test_utils.TestResponse(data)
        fake_url = 'http://localhost:8779/v1.0/fake/instances'
        error = exceptions.from_response(response, 'GET', fake_url)
        self.assertIsInstance(error, exceptions.ServiceUnavailable)

    def test_from_response_webob_pre_1_6_0(self):
        # Tests error responses before webob 1.6.0 where the error details
        # are nested in the response body.
        body = {
            'serviceUnavailable': {
                'message': 'Fake message.',
                'code': 503
            }
        }
        self._test_from_response(body)

    def test_from_response_webob_post_1_6_0(self):
        # Tests error responses from webob 1.6.0 where the error details
        # are in the response body.
        body = {'message': 'Fake message.', 'code': 503}
        self._test_from_response(body)
