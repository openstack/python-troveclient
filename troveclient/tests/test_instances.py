from testtools import TestCase
from mock import Mock

from troveclient import instances
from troveclient import base

"""
Unit tests for instances.py
"""


class InstanceTest(TestCase):

    def setUp(self):
        super(InstanceTest, self).setUp()
        self.orig__init = instances.Instance.__init__
        instances.Instance.__init__ = Mock(return_value=None)
        self.instance = instances.Instance()
        self.instance.manager = Mock()

    def tearDown(self):
        super(InstanceTest, self).tearDown()
        instances.Instance.__init__ = self.orig__init

    def test___repr__(self):
        self.instance.name = "instance-1"
        self.assertEqual('<Instance: instance-1>', self.instance.__repr__())

    def test_list_databases(self):
        db_list = ['database1', 'database2']
        self.instance.manager.databases = Mock()
        self.instance.manager.databases.list = Mock(return_value=db_list)
        self.assertEqual(db_list, self.instance.list_databases())

    def test_delete(self):
        db_delete_mock = Mock(return_value=None)
        self.instance.manager.delete = db_delete_mock
        self.instance.delete()
        self.assertEqual(1, db_delete_mock.call_count)

    def test_restart(self):
        db_restart_mock = Mock(return_value=None)
        self.instance.manager.restart = db_restart_mock
        self.instance.id = 1
        self.instance.restart()
        self.assertEqual(1, db_restart_mock.call_count)


class InstancesTest(TestCase):

    def setUp(self):
        super(InstancesTest, self).setUp()
        self.orig__init = instances.Instances.__init__
        instances.Instances.__init__ = Mock(return_value=None)
        self.instances = instances.Instances()
        self.instances.api = Mock()
        self.instances.api.client = Mock()
        self.instances.resource_class = Mock(return_value="instance-1")

        self.orig_base_getid = base.getid
        base.getid = Mock(return_value="instance1")

    def tearDown(self):
        super(InstancesTest, self).tearDown()
        instances.Instances.__init__ = self.orig__init
        base.getid = self.orig_base_getid

    def test_create(self):
        def side_effect_func(path, body, inst):
            return path, body, inst

        self.instances._create = Mock(side_effect=side_effect_func)
        p, b, i = self.instances.create("test-name", 103, "test-volume",
                                        ['db1', 'db2'], ['u1', 'u2'])
        self.assertEqual("/instances", p)
        self.assertEqual("instance", i)
        self.assertEqual(['db1', 'db2'], b["instance"]["databases"])
        self.assertEqual(['u1', 'u2'], b["instance"]["users"])
        self.assertEqual("test-name", b["instance"]["name"])
        self.assertEqual("test-volume", b["instance"]["volume"])
        self.assertEqual(103, b["instance"]["flavorRef"])

    def test__list(self):
        self.instances.api.client.get = Mock(return_value=('resp', None))
        self.assertRaises(Exception, self.instances._list, "url", None)

        body = Mock()
        body.get = Mock(return_value=[{'href': 'http://test.net/test_file',
                                       'rel': 'next'}])
        body.__getitem__ = Mock(return_value='instance1')
        #self.instances.resource_class = Mock(return_value="instance-1")
        self.instances.api.client.get = Mock(return_value=('resp', body))
        _expected = [{'href': 'http://test.net/test_file', 'rel': 'next'}]
        self.assertEqual(_expected, self.instances._list("url", None).links)

    def test_list(self):
        def side_effect_func(path, inst, limit, marker):
            return path, inst, limit, marker

        self.instances._list = Mock(side_effect=side_effect_func)
        limit_ = "test-limit"
        marker_ = "test-marker"
        expected = ("/instances", "instances", limit_, marker_)
        self.assertEqual(expected, self.instances.list(limit_, marker_))

    def test_get(self):
        def side_effect_func(path, inst):
            return path, inst

        self.instances._get = Mock(side_effect=side_effect_func)
        self.assertEqual(('/instances/instance1', 'instance'),
                         self.instances.get(1))

    def test_delete(self):
        resp = Mock()
        resp.status = 200
        body = None
        self.instances.api.client.delete = Mock(return_value=(resp, body))
        self.instances.delete('instance1')
        resp.status = 500
        self.assertRaises(Exception, self.instances.delete, 'instance1')

    def test__action(self):
        body = Mock()
        resp = Mock()
        resp.status = 200
        self.instances.api.client.post = Mock(return_value=(resp, body))
        self.assertEqual('instance-1', self.instances._action(1, body))

        self.instances.api.client.post = Mock(return_value=(resp, None))
        self.assertEqual(None, self.instances._action(1, body))

    def _set_action_mock(self):
        def side_effect_func(instance_id, body):
            self._instance_id = instance_id
            self._body = body

        self._instance_id = None
        self._body = None
        self.instances._action = Mock(side_effect=side_effect_func)

    def test_resize_volume(self):
        self._set_action_mock()
        self.instances.resize_volume(152, 512)
        self.assertEqual(152, self._instance_id)
        self.assertEqual({"resize": {"volume": {"size": 512}}}, self._body)

    def test_resize_instance(self):
        self._set_action_mock()
        self.instances.resize_instance(4725, 103)
        self.assertEqual(4725, self._instance_id)
        self.assertEqual({"resize": {"flavorRef": 103}}, self._body)

    def test_restart(self):
        self._set_action_mock()
        self.instances.restart(253)
        self.assertEqual(253, self._instance_id)
        self.assertEqual({'restart': {}}, self._body)


class InstanceStatusTest(TestCase):

    def test_constants(self):
        self.assertEqual("ACTIVE", instances.InstanceStatus.ACTIVE)
        self.assertEqual("BLOCKED", instances.InstanceStatus.BLOCKED)
        self.assertEqual("BUILD", instances.InstanceStatus.BUILD)
        self.assertEqual("FAILED", instances.InstanceStatus.FAILED)
        self.assertEqual("REBOOT", instances.InstanceStatus.REBOOT)
        self.assertEqual("RESIZE", instances.InstanceStatus.RESIZE)
        self.assertEqual("SHUTDOWN", instances.InstanceStatus.SHUTDOWN)
