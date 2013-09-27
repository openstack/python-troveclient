from testtools import TestCase
from mock import Mock

from troveclient.v1 import security_groups

"""
Unit tests for security_groups.py
"""


class SecGroupTest(TestCase):

    def setUp(self):
        super(SecGroupTest, self).setUp()
        self.orig__init = security_groups.SecurityGroup.__init__
        security_groups.SecurityGroup.__init__ = Mock(return_value=None)
        self.security_group = security_groups.SecurityGroup()
        self.security_groups = security_groups.SecurityGroups(1)

    def tearDown(self):
        super(SecGroupTest, self).tearDown()
        security_groups.SecurityGroup.__init__ = self.orig__init

    def test___repr__(self):
        self.security_group.name = "security_group-1"
        self.assertEqual('<SecurityGroup: security_group-1>',
                         self.security_group.__repr__())

    def test_list(self):
        sec_group_list = ['secgroup1', 'secgroup2']
        self.security_groups.list = Mock(return_value=sec_group_list)
        self.assertEqual(sec_group_list, self.security_groups.list())

    def test_get(self):
        def side_effect_func(path, inst):
            return path, inst

        self.security_groups._get = Mock(side_effect=side_effect_func)
        self.security_group.id = 1
        self.assertEqual(('/security-groups/1', 'security_group'),
                         self.security_groups.get(self.security_group))


class SecGroupRuleTest(TestCase):

    def setUp(self):
        super(SecGroupRuleTest, self).setUp()
        self.orig__init = security_groups.SecurityGroupRule.__init__
        security_groups.SecurityGroupRule.__init__ = Mock(return_value=None)
        security_groups.SecurityGroupRules.__init__ = Mock(return_value=None)
        self.security_group_rule = security_groups.SecurityGroupRule()
        self.security_group_rules = security_groups.SecurityGroupRules()

    def tearDown(self):
        super(SecGroupRuleTest, self).tearDown()
        security_groups.SecurityGroupRule.__init__ = self.orig__init

    def test___repr__(self):
        self.security_group_rule.group_id = 1
        self.security_group_rule.protocol = "tcp"
        self.security_group_rule.from_port = 80
        self.security_group_rule.to_port = 80
        self.security_group_rule.cidr = "0.0.0.0//0"
        representation = \
            "<SecurityGroupRule: ( \
    Security Group id: %d, \
    Protocol: %s, \
    From_Port: %d, \
    To_Port: %d, \
    CIDR: %s )>" % (1, "tcp", 80, 80, "0.0.0.0//0")

        self.assertEqual(representation,
                         self.security_group_rule.__repr__())

    def test_create(self):
        def side_effect_func(path, body, inst):
            return path, body, inst

        self.security_group_rules._create = Mock(side_effect=side_effect_func)
        p, b, i = self.security_group_rules.create(1, "tcp",
                                                   80, 80, "0.0.0.0//0")
        self.assertEqual("/security-group-rules", p)
        self.assertEqual("security_group_rule", i)
        self.assertEqual(1, b["security_group_rule"]["group_id"])
        self.assertEqual("tcp", b["security_group_rule"]["protocol"])
        self.assertEqual(80, b["security_group_rule"]["from_port"])
        self.assertEqual(80, b["security_group_rule"]["to_port"])
        self.assertEqual("0.0.0.0//0", b["security_group_rule"]["cidr"])

    def test_delete(self):
        resp = Mock()
        resp.status = 200
        body = None
        self.security_group_rules.api = Mock()
        self.security_group_rules.api.client = Mock()
        self.security_group_rules.api.client.delete = \
            Mock(return_value=(resp, body))
        self.security_group_rules.delete(self.id)
        resp.status_code = 500
        self.assertRaises(Exception, self.security_group_rules.delete,
                          self.id)
