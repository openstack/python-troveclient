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
from troveclient.v1 import flavors


class TestDatabasev1(utils.TestCommand):
    def setUp(self):
        super(TestDatabasev1, self).setUp()
        self.app.client_manager.database = mock.MagicMock()


class FakeFlavors(object):
    fake_flavors = fakes.FakeHTTPClient().get_flavors()[2]['flavors']

    def get_flavors_1(self):
        return flavors.Flavor(None, self.fake_flavors[0])
