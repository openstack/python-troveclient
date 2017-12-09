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

"""Database v1 Datastores action implementations"""

from osc_lib.command import command
from osc_lib import utils
import six

from troveclient import exceptions
from troveclient.i18n import _
from troveclient import utils as tc_utils


def set_attributes_for_print_detail(datastore):
    info = datastore._info.copy()
    versions = info.get('versions', [])
    versions_str = "\n".join(
        [ver['name'] + " (" + ver['id'] + ")" for ver in versions])
    info['versions (id)'] = versions_str
    info.pop('versions', None)
    info.pop('links', None)
    if hasattr(datastore, 'default_version'):
        def_ver_id = getattr(datastore, 'default_version')
        info['default_version'] = [
            ver['name'] for ver in versions if ver['id'] == def_ver_id][0]
    return info


class ListDatastores(command.Lister):

    _description = _("List available datastores")
    columns = ['ID', 'Name']

    def take_action(self, parsed_args):
        datastore_client = self.app.client_manager.database.datastores
        datastores = datastore_client.list()
        ds = [utils.get_item_properties(d, self.columns) for d in datastores]
        return self.columns, ds


class ShowDatastore(command.ShowOne):
    _description = _("Shows details of a datastore")

    def get_parser(self, prog_name):
        parser = super(ShowDatastore, self).get_parser(prog_name)
        parser.add_argument(
            'datastore',
            metavar='<datastore>',
            help=_('ID of the datastore'),
        )
        return parser

    def take_action(self, parsed_args):
        datastore_client = self.app.client_manager.database.datastores
        datastore = utils.find_resource(datastore_client,
                                        parsed_args.datastore)
        datastore = set_attributes_for_print_detail(datastore)
        return zip(*sorted(six.iteritems(datastore)))


class ListDatastoreVersions(command.Lister):

    _description = _("Lists available versions for a datastore")
    columns = ['ID', 'Name']

    def get_parser(self, prog_name):
        parser = super(ListDatastoreVersions, self).get_parser(prog_name)
        parser.add_argument(
            'datastore',
            metavar='<datastore>',
            help=_('ID or name of the datastore'),
        )
        return parser

    def take_action(self, parsed_args):
        datastore_version_client =\
            self.app.client_manager.database.datastore_versions
        versions = datastore_version_client.list(parsed_args.datastore)
        ds = [utils.get_item_properties(d, self.columns) for d in versions]
        return self.columns, ds


class ShowDatastoreVersion(command.ShowOne):
    _description = _("Shows details of a datastore version.")

    def get_parser(self, prog_name):
        parser = super(ShowDatastoreVersion, self).get_parser(prog_name)
        parser.add_argument(
            'datastore_version',
            metavar='<datastore_version>',
            help=_('ID or name of the datastore version.'),
        )
        parser.add_argument(
            '--datastore',
            metavar='<datastore>',
            default=None,
            help=_('ID or name of the datastore. Optional if the ID of'
                   'the datastore_version is provided.'),
        )
        return parser

    def take_action(self, parsed_args):
        datastore_version_client =\
            self.app.client_manager.database.datastore_versions
        if parsed_args.datastore:
            datastore_version = datastore_version_client.\
                get(parsed_args.datastore, parsed_args.datastore_version)
        elif tc_utils.is_uuid_like(parsed_args.datastore_version):
            datastore_version = datastore_version_client.\
                get_by_uuid(parsed_args.datastore_version)
        else:
            raise exceptions.NoUniqueMatch(_('The datastore name or id is'
                                             ' required to retrieve a'
                                             ' datastore version by name.'))
        if datastore_version._info.get('links'):
            del(datastore_version._info['links'])
        return zip(*sorted(six.iteritems(datastore_version._info)))
