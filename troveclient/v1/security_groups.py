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
#

from troveclient import base

from troveclient.common import limit_url
from troveclient.common import Paginated
from troveclient.openstack.common.apiclient import exceptions
from troveclient.openstack.common.py3kcompat import urlutils


class SecurityGroup(base.Resource):
    """
    Security Group is a resource used to hold security group information.
    """
    def __repr__(self):
        return "<SecurityGroup: %s>" % self.name


class SecurityGroups(base.ManagerWithFind):
    """
    Manage :class:`SecurityGroup` resources.
    """
    resource_class = SecurityGroup

    def _list(self, url, response_key, limit=None, marker=None):
        resp, body = self.api.client.get(limit_url(url, limit, marker))
        if not body:
            raise Exception("Call to " + url + " did not return a body.")
        links = body.get('links', [])
        next_links = [link['href'] for link in links if link['rel'] == 'next']
        next_marker = None
        for link in next_links:
            # Extract the marker from the url.
            parsed_url = urlutils.urlparse(link)
            query_dict = dict(urlutils.parse_qsl(parsed_url.query))
            next_marker = query_dict.get('marker', None)
        instances = body[response_key]
        instances = [self.resource_class(self, res) for res in instances]
        return Paginated(instances, next_marker=next_marker, links=links)

    def list(self, limit=None, marker=None):
        """
        Get a list of all security groups.

        :rtype: list of :class:`SecurityGroup`.
        """
        return self._list("/security-groups", "security_groups", limit,
                          marker)

    def get(self, security_group):
        """
        Get a specific security group.

        :rtype: :class:`SecurityGroup`
        """
        return self._get("/security-groups/%s" % base.getid(security_group),
                         "security_group")


class SecurityGroupRule(base.Resource):
    """
    Security Group Rule is a resource used to hold security group
    rule related information.
    """
    def __repr__(self):
        return \
            "<SecurityGroupRule: ( \
    Security Group id: %d, \
    Protocol: %s, \
    From_Port: %d, \
    To_Port: %d, \
    CIDR: %s )>" % (self.group_id, self.protocol, self.from_port,
                    self.to_port, self.cidr)


class SecurityGroupRules(base.ManagerWithFind):
    """
    Manage :class:`SecurityGroupRules` resources.
    """
    resource_class = SecurityGroupRule

    def create(self, group_id, protocol, from_port, to_port, cidr):
        """
        Create a new security group rule.
        """
        body = {"security_group_rule": {
            "group_id": group_id,
            "protocol": protocol,
            "from_port": from_port,
            "to_port": to_port,
            "cidr": cidr
        }}
        return self._create("/security-group-rules", body,
                            "security_group_rule")

    def delete(self, security_group_rule):
        """
        Delete the specified security group rule.

        :param security_group_rule: The security group rule to delete
        """
        resp, body = self.api.client.delete("/security-group-rules/%s" %
                                            base.getid(security_group_rule))
        if resp.status_code in (422, 500):
            raise exceptions.from_response(resp, body)

    # Appease the abc gods
    def list(self):
        pass
