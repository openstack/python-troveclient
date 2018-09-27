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

"""Database v1 Flavors action implementations"""

from osc_lib.command import command
from osc_lib import utils
import six

from troveclient import exceptions
from troveclient.i18n import _


def set_attributes_for_print_detail(flavor):
    info = flavor._info.copy()
    # Get rid of those ugly links
    if info.get('links'):
        del(info['links'])

    # Fallback to str_id for flavors, where necessary
    if hasattr(flavor, 'str_id'):
        info['id'] = flavor.id
        del(info['str_id'])
    return info


class ListDatabaseFlavors(command.Lister):

    _description = _("List database flavors")
    columns = ['ID', 'Name', 'RAM', 'vCPUs', 'Disk', 'Ephemeral']

    def get_parser(self, prog_name):
        parser = super(ListDatabaseFlavors, self).get_parser(prog_name)
        parser.add_argument(
            '--datastore-type',
            dest='datastore_type',
            metavar='<datastore-type>',
            help=_('Type of the datastore. For eg: mysql.')
        )
        parser.add_argument(
            '--datastore-version-id',
            dest='datastore_version_id',
            metavar='<datastore-version-id>',
            help=_('ID of the datastore version.')
        )
        return parser

    def take_action(self, parsed_args):
        db_flavors = self.app.client_manager.database.flavors
        if parsed_args.datastore_type and parsed_args.datastore_version_id:
            flavors = db_flavors.list_datastore_version_associated_flavors(
                datastore=parsed_args.datastore_type,
                version_id=parsed_args.datastore_version_id)
        elif (not parsed_args.datastore_type and not
              parsed_args.datastore_version_id):
            flavors = db_flavors.list()
        else:
            raise exceptions.MissingArgs(['datastore-type',
                                          'datastore-version-id'])

        # Fallback to str_id where necessary.
        _flavors = []
        for f in flavors:
            if not f.id and hasattr(f, 'str_id'):
                f.id = f.str_id
            _flavors.append(utils.get_item_properties(f, self.columns))

        return self.columns, _flavors


class ShowDatabaseFlavor(command.ShowOne):
    _description = _("Shows details of a database flavor")

    def get_parser(self, prog_name):
        parser = super(ShowDatabaseFlavor, self).get_parser(prog_name)
        parser.add_argument(
            'flavor',
            metavar='<flavor>',
            help=_('ID or name of the flavor'),
        )
        return parser

    def take_action(self, parsed_args):
        db_flavors = self.app.client_manager.database.flavors
        flavor = utils.find_resource(db_flavors,
                                     parsed_args.flavor)
        flavor = set_attributes_for_print_detail(flavor)
        return zip(*sorted(six.iteritems(flavor)))
