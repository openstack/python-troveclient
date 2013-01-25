from testtools import TestCase
from mock import Mock

from reddwarfclient import management
from reddwarfclient import base

"""
Unit tests for management.py
"""


class RootHistoryTest(TestCase):

    def setUp(self):
        super(RootHistoryTest, self).setUp()
        self.orig__init = management.RootHistory.__init__
        management.RootHistory.__init__ = Mock(return_value=None)

    def tearDown(self):
        super(RootHistoryTest, self).tearDown()
        management.RootHistory.__init__ = self.orig__init

    def test___repr__(self):
        root_history = management.RootHistory()
        root_history.id = "1"
        root_history.created = "ct"
        root_history.user = "tu"
        self.assertEqual('<Root History: Instance 1 enabled at ct by tu>',
                         root_history.__repr__())


class ManagementTest(TestCase):

    def setUp(self):
        super(ManagementTest, self).setUp()
        self.orig__init = management.Management.__init__
        management.Management.__init__ = Mock(return_value=None)
        self.management = management.Management()
        self.management.api = Mock()
        self.management.api.client = Mock()

        self.orig_hist__init = management.RootHistory.__init__
        self.orig_base_getid = base.getid
        base.getid = Mock(return_value="instance1")

    def tearDown(self):
        super(ManagementTest, self).tearDown()
        management.Management.__init__ = self.orig__init
        management.RootHistory.__init__ = self.orig_hist__init
        base.getid = self.orig_base_getid

    def test__list(self):
        self.management.api.client.get = Mock(return_value=('resp', None))
        self.assertRaises(Exception, self.management._list, "url", None)

        body = Mock()
        body.get = Mock(return_value=[{'href': 'http://test.net/test_file',
                                       'rel': 'next'}])
        body.__getitem__ = Mock(return_value='instance1')
        self.management.resource_class = Mock(return_value="instance-1")
        self.management.api.client.get = Mock(return_value=('resp', body))
        _expected = [{'href': 'http://test.net/test_file', 'rel': 'next'}]
        self.assertEqual(_expected, self.management._list("url", None).links)

    def test_show(self):
        def side_effect_func(path, instance):
            return path, instance
        self.management._get = Mock(side_effect=side_effect_func)
        p, i = self.management.show(1)
        self.assertEqual(('/mgmt/instances/instance1', 'instance'), (p, i))

    def test_index(self):
        def side_effect_func(url, name, limit, marker):
            return url

        self.management._list = Mock(side_effect=side_effect_func)
        self.assertEqual('/mgmt/instances?deleted=true',
                         self.management.index(deleted=True))
        self.assertEqual('/mgmt/instances?deleted=false',
                         self.management.index(deleted=False))

    def test_root_enabled_history(self):
        self.management.api.client.get = Mock(return_value=('resp', None))
        self.assertRaises(Exception,
                          self.management.root_enabled_history, "instance")
        body = {'root_history': 'rh'}
        self.management.api.client.get = Mock(return_value=('resp', body))
        management.RootHistory.__init__ = Mock(return_value=None)
        rh = self.management.root_enabled_history("instance")
        self.assertTrue(isinstance(rh, management.RootHistory))

    def test__action(self):
        resp = Mock()
        self.management.api.client.post = Mock(return_value=(resp, 'body'))
        resp.status = 200
        self.management._action(1, 'body')
        self.assertEqual(1, self.management.api.client.post.call_count)
        resp.status = 400
        self.assertRaises(ValueError, self.management._action, 1, 'body')
        self.assertEqual(2, self.management.api.client.post.call_count)

    def _mock_action(self):
        self.body_ = ""

        def side_effect_func(instance_id, body):
            self.body_ = body
        self.management._action = Mock(side_effect=side_effect_func)

    def test_stop(self):
        self._mock_action()
        self.management.stop(1)
        self.assertEqual(1, self.management._action.call_count)
        self.assertEqual({'stop': {}}, self.body_)

    def test_reboot(self):
        self._mock_action()
        self.management.reboot(1)
        self.assertEqual(1, self.management._action.call_count)
        self.assertEqual({'reboot': {}}, self.body_)

    def test_migrate(self):
        self._mock_action()
        self.management.migrate(1)
        self.assertEqual(1, self.management._action.call_count)
        self.assertEqual({'migrate': {}}, self.body_)

    def test_update(self):
        self._mock_action()
        self.management.update(1)
        self.assertEqual(1, self.management._action.call_count)
        self.assertEqual({'update': {}}, self.body_)
