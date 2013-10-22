# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
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

from troveclient import client
from troveclient.v1.databases import Databases
from troveclient.v1.flavors import Flavors
from troveclient.v1.instances import Instances
from troveclient.v1.limits import Limits
from troveclient.v1.users import Users
from troveclient.v1.root import Root
from troveclient.v1.hosts import Hosts
from troveclient.v1.quota import Quotas
from troveclient.v1.backups import Backups
from troveclient.v1.security_groups import SecurityGroups
from troveclient.v1.security_groups import SecurityGroupRules
from troveclient.v1.storage import StorageInfo
from troveclient.v1.management import Management
from troveclient.v1.management import MgmtFlavors
from troveclient.v1.accounts import Accounts
from troveclient.v1.diagnostics import DiagnosticsInterrogator
from troveclient.v1.diagnostics import HwInfoInterrogator


class Client(object):
    """
    Top-level object to access the OpenStack Database API.

    Create an instance with your creds::

        >>> client = Client(USERNAME, PASSWORD, PROJECT_ID, AUTH_URL)

    Then call methods on its managers::

        >>> client.instances.list()
        ...

    """

    def __init__(self, username, password, project_id=None, auth_url='',
                 insecure=False, timeout=None, tenant_id=None,
                 proxy_tenant_id=None, proxy_token=None, region_name=None,
                 endpoint_type='publicURL', extensions=None,
                 service_type='database', service_name=None,
                 database_service_name=None, retries=None,
                 http_log_debug=False,
                 cacert=None):
        # self.limits = limits.LimitsManager(self)

        # extensions
        self.flavors = Flavors(self)
        self.users = Users(self)
        self.databases = Databases(self)
        self.backups = Backups(self)
        self.instances = Instances(self)
        self.limits = Limits(self)
        self.root = Root(self)
        self.security_group_rules = SecurityGroupRules(self)
        self.security_groups = SecurityGroups(self)

        #self.hosts = Hosts(self)
        #self.quota = Quotas(self)
        #self.storage = StorageInfo(self)
        #self.management = Management(self)
        #self.mgmt_flavor = MgmtFlavors(self)
        #self.accounts = Accounts(self)
        #self.diagnostics = DiagnosticsInterrogator(self)
        #self.hwinfo = HwInfoInterrogator(self)

        # Add in any extensions...
        if extensions:
            for extension in extensions:
                if extension.manager_class:
                    setattr(self, extension.name,
                            extension.manager_class(self))

        self.client = client.HTTPClient(
            username,
            password,
            project_id,
            auth_url,
            insecure=insecure,
            timeout=timeout,
            tenant_id=tenant_id,
            proxy_token=proxy_token,
            proxy_tenant_id=proxy_tenant_id,
            region_name=region_name,
            endpoint_type=endpoint_type,
            service_type=service_type,
            service_name=service_name,
            database_service_name=database_service_name,
            retries=retries,
            http_log_debug=http_log_debug,
            cacert=cacert)

    def authenticate(self):
        """
        Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`exceptions.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()

    def get_database_api_version_from_endpoint(self):
        return self.client.get_database_api_version_from_endpoint()
