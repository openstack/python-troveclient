from testtools import TestCase
from mock import Mock

from reddwarfclient import users
from reddwarfclient import base

"""
Unit tests for users.py
"""


class UserTest(TestCase):

    def setUp(self):
        super(UserTest, self).setUp()
        self.orig__init = users.User.__init__
        users.User.__init__ = Mock(return_value=None)
        self.user = users.User()

    def tearDown(self):
        super(UserTest, self).tearDown()
        users.User.__init__ = self.orig__init

    def test___repr__(self):
        self.user.name = "user-1"
        self.assertEqual('<User: user-1>', self.user.__repr__())


class UsersTest(TestCase):

    def setUp(self):
        super(UsersTest, self).setUp()
        self.orig__init = users.Users.__init__
        users.Users.__init__ = Mock(return_value=None)
        self.users = users.Users()
        self.users.api = Mock()
        self.users.api.client = Mock()

        self.orig_base_getid = base.getid
        base.getid = Mock(return_value="instance1")

    def tearDown(self):
        super(UsersTest, self).tearDown()
        users.Users.__init__ = self.orig__init
        base.getid = self.orig_base_getid

    def _get_mock_method(self):
        self._resp = Mock()
        self._body = None
        self._url = None

        def side_effect_func(url, body=None):
            self._body = body
            self._url = url
            return (self._resp, body)

        return Mock(side_effect=side_effect_func)

    def _build_fake_user(self, name, hostname=None, password=None,
                         databases=None):
        return {'name': name,
                'password': password if password else 'password',
                'host': hostname,
                'databases': databases if databases else [],
               }

    def test_create(self):
        self.users.api.client.post = self._get_mock_method()
        self._resp.status = 200
        user = self._build_fake_user('user1')

        self.users.create(23, [user])
        self.assertEqual('/instances/23/users', self._url)
        self.assertEqual({"users": [user]}, self._body)

        # Even if host isn't supplied originally,
        # the default is supplied.
        del user['host']
        self.users.create(23, [user])
        self.assertEqual('/instances/23/users', self._url)
        user['host'] = '%'
        self.assertEqual({"users": [user]}, self._body)

        # If host is supplied, of course it's put into the body.
        user['host'] = '127.0.0.1'
        self.users.create(23, [user])
        self.assertEqual({"users": [user]}, self._body)

        # Make sure that response of 400 is recognized as an error.
        user['host'] = '%'
        self._resp.status = 400
        self.assertRaises(Exception, self.users.create, 12, [user])

    def test_delete(self):
        self.users.api.client.delete = self._get_mock_method()
        self._resp.status = 200
        self.users.delete(27, 'user1')
        # The client appends the host to remove ambiguity.
        # urllib.unquote('%40%25') == '@%'
        self.assertEqual('/instances/27/users/user1%40%25', self._url)
        self._resp.status = 400
        self.assertRaises(Exception, self.users.delete, 34, 'user1')

    def test__list(self):
        def side_effect_func(self, val):
            return val

        key = 'key'
        body = Mock()
        body.get = Mock(return_value=[{'href': 'http://test.net/test_file',
                                       'rel': 'next'}])
        body.__getitem__ = Mock(return_value=["test-value"])

        resp = Mock()
        resp.status = 200
        self.users.resource_class = Mock(side_effect=side_effect_func)
        self.users.api.client.get = Mock(return_value=(resp, body))
        self.assertEqual(["test-value"], self.users._list('url', key).items)

        self.users.api.client.get = Mock(return_value=(resp, None))
        self.assertRaises(Exception, self.users._list, 'url', None)

    def test_list(self):
        def side_effect_func(path, user, limit, marker):
            return path

        self.users._list = Mock(side_effect=side_effect_func)
        self.assertEqual('/instances/instance1/users', self.users.list(1))
