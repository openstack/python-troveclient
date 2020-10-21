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

import os
import random
import sys
from unittest import mock
import uuid

import fixtures
import testtools

from troveclient.tests.osc import fakes


class TestCase(testtools.TestCase):
    def setUp(self):
        testtools.TestCase.setUp(self)

        if (os.environ.get("OS_STDOUT_CAPTURE") == "True" or
                os.environ.get("OS_STDOUT_CAPTURE") == "1"):
            stdout = self.useFixture(fixtures.StringStream("stdout")).stream
            self.useFixture(fixtures.MonkeyPatch("sys.stdout", stdout))

        if (os.environ.get("OS_STDERR_CAPTURE") == "True" or
                os.environ.get("OS_STDERR_CAPTURE") == "1"):
            stderr = self.useFixture(fixtures.StringStream("stderr")).stream
            self.useFixture(fixtures.MonkeyPatch("sys.stderr", stderr))

    @classmethod
    def random_name(cls, name='', prefix=None):
        """Generate a random name that inclues a random number.

        :param str name: The name that you want to include
        :param str prefix: The prefix that you want to include

        :return: a random name. The format is
                 '<prefix>-<name>-<random number>'.
                 (e.g. 'prefixfoo-namebar-154876201')
        :rtype: string
        """
        randbits = str(random.randint(1, 0x7fffffff))
        rand_name = randbits
        if name:
            rand_name = name + '-' + rand_name
        if prefix:
            rand_name = prefix + '-' + rand_name
        return rand_name

    @classmethod
    def random_uuid(cls):
        return str(uuid.uuid4())


class TestCommand(TestCase):
    """Test cliff command classes"""

    def setUp(self):
        super(TestCommand, self).setUp()
        # Build up a fake app
        self.fake_stdout = fakes.FakeStdout()
        self.app = mock.MagicMock()
        self.app.stdout = self.fake_stdout
        self.app.stdin = sys.stdin
        self.app.stderr = sys.stderr

    def check_parser(self, cmd, args, verify_args):
        cmd_parser = cmd.get_parser('check_parser')
        try:
            parsed_args = cmd_parser.parse_args(args)
        except SystemExit:
            raise Exception("Argument parse failed")
        for av in verify_args:
            attr, value = av
            if attr:
                self.assertIn(attr, parsed_args)
                self.assertEqual(getattr(parsed_args, attr), value)
        return parsed_args
