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

import os
import tempfile
import testtools

from troveclient import utils


class UtilsTest(testtools.TestCase):

    def func(self):
        pass

    def test_add_hookable_mixin(self):
        hook_type = "hook_type"
        mixin = utils.HookableMixin()
        mixin.add_hook(hook_type, self.func)
        self.assertIn(hook_type, mixin._hooks_map)
        self.assertIn(self.func, mixin._hooks_map[hook_type])

    def test_run_hookable_mixin(self):
        hook_type = "hook_type"
        mixin = utils.HookableMixin()
        mixin.add_hook(hook_type, self.func)
        mixin.run_hooks(hook_type)

    def test_environment(self):
        self.assertEqual('', utils.env())
        self.assertEqual('passing', utils.env(default='passing'))

        os.environ['test_abc'] = 'passing'
        self.assertEqual('passing', utils.env('test_abc'))
        self.assertEqual('', utils.env('test_abcd'))

    def test_encode_decode_data(self):
        text_data_str = 'This is a text string'
        try:
            text_data_bytes = bytes('This is a byte stream', 'utf-8')
        except TypeError:
            text_data_bytes = bytes('This is a byte stream')
        random_data_str = os.urandom(12)
        random_data_bytes = bytearray(os.urandom(12))
        special_char_str = '\x00\xFF\x00\xFF\xFF\x00'
        special_char_bytes = bytearray(
            [ord(item) for item in special_char_str])
        data = [text_data_str,
                text_data_bytes,
                random_data_str,
                random_data_bytes,
                special_char_str,
                special_char_bytes]

        for datum in data:
            # the deserialized data is always a bytearray
            try:
                expected_deserialized = bytearray(
                    [ord(item) for item in datum])
            except TypeError:
                expected_deserialized = bytearray(
                    [item for item in datum])
            serialized_data = utils.encode_data(datum)
            self.assertIsNotNone(serialized_data, "'%s' serialized is None" %
                                 datum)
            deserialized_data = utils.decode_data(serialized_data)
            self.assertIsNotNone(deserialized_data, "'%s' deserialized is None"
                                 % datum)
            self.assertEqual(expected_deserialized, deserialized_data,
                             "Serialize/Deserialize failed")
            # Now we write the data to a file and read it back in
            # to make sure the round-trip doesn't change anything.
            with tempfile.NamedTemporaryFile() as temp_file:
                with open(temp_file.name, 'wb') as fh_w:
                    fh_w.write(
                        bytearray([ord(item) for item in serialized_data]))
                with open(temp_file.name, 'rb') as fh_r:
                    new_serialized_data = fh_r.read()
                new_deserialized_data = utils.decode_data(
                    new_serialized_data)
                self.assertIsNotNone(new_deserialized_data,
                                     "'%s' deserialized is None" % datum)
                self.assertEqual(expected_deserialized, new_deserialized_data,
                                 "Serialize/Deserialize with files failed")
