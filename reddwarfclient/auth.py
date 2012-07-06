#    Copyright 2012 OpenStack LLC
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

from reddwarfclient import exceptions


class Authenticator(object):
    """
    Helper class to perform Keystone or other miscellaneous authentication.
    """

    def __init__(self, client, type, url, username, password, tenant,
                 region=None, service_type=None, service_name=None,
                 service_url=None):
        self.client = client
        self.type = type
        self.url = url
        self.username = username
        self.password = password
        self.tenant = tenant
        self.region = region
        self.service_type = service_type
        self.service_name = service_name
        self.service_url = service_url

    def _authenticate(self, url, body):
        """Authenticate and extract the service catalog."""
        # Make sure we follow redirects when trying to reach Keystone
        tmp_follow_all_redirects = self.client.follow_all_redirects
        self.client.follow_all_redirects = True

        try:
            resp, body = self.client._time_request(url, "POST", body=body)
        finally:
            self.client.follow_all_redirects = tmp_follow_all_redirects

        if resp.status == 200:  # content must always present
            try:
                return ServiceCatalog(body, region=self.region,
                                      service_type=self.service_type,
                                      service_name=self.service_name,
                                      service_url=self.service_url)
            except exceptions.AmbiguousEndpoints:
                print "Found more than one valid endpoint. Use a more "\
                      "restrictive filter"
                raise
            except KeyError:
                raise exceptions.AuthorizationFailure()
            except exceptions.EndpointNotFound:
                print "Could not find any suitable endpoint. Correct region?"
                raise

        elif resp.status == 305:
            return resp['location']
        else:
            raise exceptions.from_response(resp, body)

    def authenticate(self):
        if self.type == "keystone":
            return self._v2_auth(self.url)
        elif self.type == "rax":
            return self._rax_auth(self.url)

    def _v2_auth(self, url):
        """Authenticate against a v2.0 auth service."""
        body = {"auth": {
                    "passwordCredentials": {
                            "username": self.username,
                            "password": self.password}
                    }
               }

        if self.tenant:
            body['auth']['tenantName'] = self.tenant

        return self._authenticate(url, body)

    def _rax_auth(self, url):
        """Authenticate against the Rackspace auth service."""
        body = {'auth': {
                    'RAX-KSKEY:apiKeyCredentials': {
                            'username': self.username,
                            'apiKey': self.password,
                            'tenantName': self.tenant}
                    }
               }

        return self._authenticate(self.url, body)


class ServiceCatalog(object):
    """Helper methods for dealing with a Keystone Service Catalog."""

    def __init__(self, resource_dict, region=None, service_type=None,
                 service_name=None, service_url=None):
        self.catalog = resource_dict
        self.region = region
        self.service_type = service_type
        self.service_name = service_name
        self.service_url = service_url
        self.management_url = None
        self.public_url = None
        self._load()

    def _load(self):
        if not self.service_url:
            self.public_url = self._url_for(attr='region',
                                            filter_value=self.region,
                                            endpoint_type="publicURL")
            self.management_url = self._url_for(attr='region',
                                                filter_value=self.region,
                                                endpoint_type="adminURL")
        else:
            self.public_url = self.service_url
            self.management_url = self.service_url

    def get_token(self):
        return self.catalog['access']['token']['id']

    def get_management_url(self):
        return self.management_url

    def get_public_url(self):
        return self.public_url

    def _url_for(self, attr=None, filter_value=None,
                 endpoint_type='publicURL'):
        """
        Fetch the public URL from the Reddwarf service for a particular
        endpoint attribute. If none given, return the first.
        """
        matching_endpoints = []
        if 'endpoints' in self.catalog:
            # We have a bastardized service catalog. Treat it special. :/
            for endpoint in self.catalog['endpoints']:
                if not filter_value or endpoint[attr] == filter_value:
                    matching_endpoints.append(endpoint)
            if not matching_endpoints:
                raise exceptions.EndpointNotFound()

        # We don't always get a service catalog back ...
        if not 'serviceCatalog' in self.catalog['access']:
            raise exceptions.EndpointNotFound()

        # Full catalog ...
        catalog = self.catalog['access']['serviceCatalog']

        for service in catalog:
            if service.get("type") != self.service_type:
                continue

            if (self.service_name and self.service_type == 'reddwarf' and
                service.get('name') != self.service_name):
                continue

            endpoints = service['endpoints']
            for endpoint in endpoints:
                if not filter_value or endpoint.get(attr) == filter_value:
                    endpoint["serviceName"] = service.get("name")
                    matching_endpoints.append(endpoint)

        if not matching_endpoints:
            raise exceptions.EndpointNotFound()
        elif len(matching_endpoints) > 1:
            raise exceptions.AmbiguousEndpoints(endpoints=matching_endpoints)
        else:
            return matching_endpoints[0].get(endpoint_type, None)
