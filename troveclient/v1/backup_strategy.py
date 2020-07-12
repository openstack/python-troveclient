# Copyright 2020 Catalyst Cloud
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
from troveclient import base
from troveclient import common


class BackupStrategy(base.Resource):
    def __repr__(self):
        return "<BackupStrategy: %s[%s]>" % (self.project_id, self.instance_id)


class BackupStrategiesManager(base.ManagerWithFind):
    resource_class = BackupStrategy

    def list(self, instance_id=None, project_id=None):
        query_strings = {}
        if instance_id:
            query_strings["instance_id"] = instance_id
        if project_id:
            query_strings["project_id"] = project_id

        url = common.append_query_strings('/backup_strategies',
                                          **query_strings)

        return self._list(url, "backup_strategies")

    def create(self, instance_id=None, swift_container=None):
        backup_strategy = {}
        if instance_id:
            backup_strategy['instance_id'] = instance_id
        if swift_container:
            backup_strategy['swift_container'] = swift_container
        body = {"backup_strategy": backup_strategy}

        return self._create("/backup_strategies", body, "backup_strategy")

    def delete(self, instance_id=None, project_id=None):
        url = "/backup_strategies"
        query_strings = {}
        if instance_id:
            query_strings["instance_id"] = instance_id
        if project_id:
            query_strings["project_id"] = project_id

        url = common.append_query_strings('/backup_strategies',
                                          **query_strings)

        resp, body = self._delete(url)
        common.check_for_exceptions(resp, body, url)
