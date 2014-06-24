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

import re
import sys

import fixtures
import mock
import six
import testtools

import troveclient.client
from troveclient import exceptions
import troveclient.shell

FAKE_V2_ENV = {'OS_USERNAME': 'user_id',
               'OS_PASSWORD': 'password',
               'OS_TENANT_ID': 'tenant_id',
               'OS_AUTH_URL': 'http://no.where/v2.0'}

FAKE_V3_ENV = {'OS_USERNAME': 'xyz',
               'OS_PASSWORD': 'password',
               'OS_PROJECT_ID': 'project_id',
               'OS_USER_DOMAIN_NAME': 'user_domain_name',
               'OS_AUTH_URL': 'http://no.where/v3'}


class ShellTest(testtools.TestCase):

    def make_env(self, exclude=None, fake_env=FAKE_V2_ENV):
        env = dict((k, v) for k, v in fake_env.items() if k != exclude)
        self.useFixture(fixtures.MonkeyPatch('os.environ', env))

    def setUp(self):
        super(ShellTest, self).setUp()
        self.useFixture(fixtures.MonkeyPatch(
                        'troveclient.client.get_client_class',
                        mock.MagicMock))

    def shell(self, argstr, exitcodes=(0,)):
        orig = sys.stdout
        orig_stderr = sys.stderr
        try:
            sys.stdout = six.StringIO()
            sys.stderr = six.StringIO()
            _shell = troveclient.shell.OpenStackTroveShell()
            _shell.main(argstr.split())
        except SystemExit:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.assertIn(exc_value.code, exitcodes)
        finally:
            stdout = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = orig
            stderr = sys.stderr.getvalue()
            sys.stderr.close()
            sys.stderr = orig_stderr
        return (stdout, stderr)

    def test_help_unknown_command(self):
        self.assertRaises(exceptions.CommandError, self.shell, 'help foofoo')

    def test_help(self):
        required = [
            '.*?^usage: ',
            '.*?^See "trove help COMMAND" for help on a specific command',
        ]
        stdout, stderr = self.shell('help')
        for r in required:
            self.assertThat(
                (stdout + stderr),
                testtools.matchers.MatchesRegex(r, re.DOTALL | re.MULTILINE))

    def test_no_username(self):
        required = ('You must provide a username'
                    ' via either --os-username or'
                    ' env[OS_USERNAME]')
        self.make_env(exclude='OS_USERNAME')
        try:
            self.shell('list')
        except exceptions.CommandError as message:
            self.assertEqual(required, message.args[0])
        else:
            self.fail('CommandError not raised')

    def test_no_auth_url(self):
        required = ('You must provide an auth url'
                    ' via either --os-auth-url or env[OS_AUTH_URL]',)
        self.make_env(exclude='OS_AUTH_URL')
        try:
            self.shell('list')
        except exceptions.CommandError as message:
            self.assertEqual(required, message.args)
        else:
            self.fail('CommandError not raised')


class ShellTestKeystoneV3(ShellTest):

    version_id = u'v3'
    links = [{u'href': u'http://no.where/v3', u'rel': u'self'}]

    def make_env(self, exclude=None, fake_env=FAKE_V3_ENV):
        if 'OS_AUTH_URL' in fake_env:
            fake_env.update({'OS_AUTH_URL': 'http://no.where/v3'})
        env = dict((k, v) for k, v in fake_env.items() if k != exclude)
        self.useFixture(fixtures.MonkeyPatch('os.environ', env))

    def test_no_project_id(self):
        required = (
            u'You must provide a tenant_name, tenant_id, '
            u'project_id or project_name (with '
            u'project_domain_name or project_domain_id) via '
            u'  --os-tenant-name (env[OS_TENANT_NAME]),'
            u'  --os-tenant-id (env[OS_TENANT_ID]),'
            u'  --os-project-id (env[OS_PROJECT_ID])'
            u'  --os-project-name (env[OS_PROJECT_NAME]),'
            u'  --os-project-domain-id '
            u'(env[OS_PROJECT_DOMAIN_ID])'
            u'  --os-project-domain-name '
            u'(env[OS_PROJECT_DOMAIN_NAME])'
        )
        self.make_env(exclude='OS_PROJECT_ID')
        try:
            self.shell('list')
        except exceptions.CommandError as message:
            self.assertEqual(required, message.args[0])
        else:
            self.fail('CommandError not raised')

    @mock.patch('sys.stdin', side_effect=mock.MagicMock)
    @mock.patch('keystoneclient._discover.get_version_data',
                return_value=[{u'status': u'stable', u'id': version_id,
                               u'links': links}])
    @mock.patch('troveclient.v1.datastores.DatastoreVersions.list',
                return_value='foobar')
    def test_datastore_version_list(self, mock_stdin, mock_discovery,
                                    mock_dataversion):
        mock_stdin.encoding = "utf-8"
        expected = '\n'.join([
            '+----+------+',
            '| ID | Name |',
            '+----+------+',
            '|    |      |',
            '|    |      |',
            '|    |      |',
            '|    |      |',
            '|    |      |',
            '|    |      |',
            '+----+------+',
            ''
        ])

        with mock.patch('troveclient.client.SessionClient') as mock_session:
            mock_stdin.encoding = "utf-8"
            ms = mock_session.return_value
            ms.get_database_api_version_from_endpoint.return_value = '1.0'
            self.make_env()
            stdout, stderr = self.shell('datastore-version-list XXX')
            self.assertEqual((stdout + stderr), expected)
