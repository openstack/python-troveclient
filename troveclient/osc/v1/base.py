# Copyright 2019 Catalyst Cloud Ltd.
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
from osc_lib.command import command
from osc_lib import exceptions


class TroveDeleter(command.Command):
    def delete_resources(self, ids):
        """Delete one or more resources."""
        failure_flag = False
        success_msg = "Request to delete %s %s has been accepted."
        error_msg = "Unable to delete the specified %s(s)."

        for id in ids:
            try:
                self.delete_func(id)
                print(success_msg % (self.resource, id))
            except Exception as e:
                failure_flag = True
                print(e)

        if failure_flag:
            raise exceptions.CommandError(error_msg % self.resource)
