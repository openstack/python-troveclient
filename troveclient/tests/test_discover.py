# Copyright 2012 OpenStack Foundation
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

import inspect
import types
from unittest import mock

import pkg_resources
import testtools

import troveclient.shell


class DiscoverTest(testtools.TestCase):

    def test_discover_via_entry_points(self):

        def mock_iter_entry_points(group):
            if group == 'troveclient.extension':
                fake_ep = mock.Mock()
                fake_ep.name = 'foo'
                fake_ep.module = types.ModuleType('foo')
                fake_ep.load.return_value = fake_ep.module
                return [fake_ep]

        @mock.patch.object(pkg_resources, 'iter_entry_points',
                           mock_iter_entry_points)
        def test():
            shell = troveclient.shell.OpenStackTroveShell()
            for name, module in shell._discover_via_entry_points():
                self.assertEqual('foo', name)
                self.assertTrue(inspect.ismodule(module))

        test()

    def test_discover_extensions(self):

        def mock_discover_via_python_path(self):
            yield 'foo', types.ModuleType('foo')

        def mock_discover_via_contrib_path(self, version):
            yield 'bar', types.ModuleType('bar')

        def mock_discover_via_entry_points(self):
            yield 'baz', types.ModuleType('baz')

        @mock.patch.object(troveclient.shell.OpenStackTroveShell,
                           '_discover_via_python_path',
                           mock_discover_via_python_path)
        @mock.patch.object(troveclient.shell.OpenStackTroveShell,
                           '_discover_via_contrib_path',
                           mock_discover_via_contrib_path)
        @mock.patch.object(troveclient.shell.OpenStackTroveShell,
                           '_discover_via_entry_points',
                           mock_discover_via_entry_points)
        def test():
            shell = troveclient.shell.OpenStackTroveShell()
            extensions = shell._discover_extensions('1.0')
            self.assertEqual(3, len(extensions))
            names = sorted(['foo', 'bar', 'baz'])
            sorted_extensions = sorted(extensions, key=lambda ext: ext.name)
            for i in range(len(names)):
                ext = sorted_extensions[i]
                name = names[i]
                self.assertEqual(name, ext.name)
                self.assertTrue(inspect.ismodule(ext.module))

        test()
