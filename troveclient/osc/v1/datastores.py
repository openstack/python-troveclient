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
        return zip(*sorted(datastore.items()))


class DeleteDatastore(command.Command):
    _description = _("Deletes a datastore")

    def get_parser(self, prog_name):
        parser = super(DeleteDatastore, self).get_parser(prog_name)
        parser.add_argument(
            'datastore',
            metavar='<datastore>',
            help=_('ID or name of the datastore'),
        )
        return parser

    def take_action(self, parsed_args):
        datastore_client = self.app.client_manager.database.datastores
        try:
            datastore_client.delete(parsed_args.datastore)
        except Exception as e:
            msg = (_("Failed to delete datastore %(datastore)s: %(e)s")
                   % {'datastore': parsed_args.datastore, 'e': e})
            raise exceptions.CommandError(msg)


class ListDatastoreVersions(command.Lister):

    _description = _("Lists available versions for a datastore")
    columns = ['ID', 'Name', "Version"]

    def get_parser(self, prog_name):
        parser = super(ListDatastoreVersions, self).get_parser(prog_name)
        parser.add_argument(
            'datastore',
            metavar='<datastore>',
            help=_('ID or name of the datastore'),
        )
        return parser

    def take_action(self, parsed_args):
        datastore_version_client = \
            self.app.client_manager.database.datastore_versions
        versions = datastore_version_client.list(parsed_args.datastore)
        ds = [utils.get_dict_properties(d.to_dict(), self.columns)
              for d in versions]
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
            del (datastore_version._info['links'])
        return zip(*sorted(datastore_version._info.items()))


class DeleteDatastoreVersion(command.Command):
    _description = _("Deletes a datastore version.")

    def get_parser(self, prog_name):
        parser = super(DeleteDatastoreVersion, self).get_parser(prog_name)
        parser.add_argument(
            'datastore_version',
            metavar='<datastore_version>',
            help=_('ID of the datastore version.'),
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.database.mgmt_ds_versions
        try:
            client.delete(parsed_args.datastore_version)
        except Exception as e:
            msg = (_("Failed to delete datastore version %(version)s: %(e)s")
                   % {'version': parsed_args.datastore_version, 'e': e})
            raise exceptions.CommandError(msg)


class CreateDatastoreVersion(command.Command):
    _description = _("Creates a datastore version.")

    def get_parser(self, prog_name):
        parser = super(CreateDatastoreVersion, self).get_parser(prog_name)
        parser.add_argument(
            'version_name',
            help=_('Datastore version name.'),
        )
        parser.add_argument(
            'datastore_name',
            help=_("Datastore name. The datastore is created automatically "
                   "if does not exist."),
        )
        parser.add_argument(
            'datastore_manager',
            help=_('Datastore manager, e.g. mysql'),
        )
        parser.add_argument(
            'image_id',
            help=_('ID of the datastore image in Glance. This can be empty '
                   'string if --image-tags is specified.'),
        )
        parser.add_argument(
            '--active',
            action='store_true',
            help=_('Enable the datastore version.'),
        )
        parser.add_argument(
            '--image-tags',
            help=_('List of image tags separated by comma, e.g. trove,mysql'),
        )
        parser.add_argument(
            '--default',
            action='store_true',
            help=_('If set the datastore version as default.'),
        )
        parser.add_argument(
            '--version-number',
            help=_("The version number for the database. If not specified, "
                   "use the version name as the default value."),
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.database.mgmt_ds_versions

        image_tags = []
        if parsed_args.image_tags:
            image_tags = parsed_args.image_tags.split(',')

        try:
            client.create(
                parsed_args.version_name,
                parsed_args.datastore_name,
                parsed_args.datastore_manager,
                parsed_args.image_id,
                image_tags=image_tags,
                active='true' if parsed_args.active else 'false',
                default='true' if parsed_args.default else 'false',
                version=parsed_args.version_number
            )
        except Exception as e:
            msg = (_("Failed to create datastore version %(version)s: %(e)s")
                   % {'version': parsed_args.version_name, 'e': e})
            raise exceptions.CommandError(msg)


class UpdateDatastoreVersion(command.Command):
    _description = _("Updates a datastore version.")

    def get_parser(self, prog_name):
        parser = super(UpdateDatastoreVersion, self).get_parser(prog_name)
        parser.add_argument(
            'datastore_version_id',
            help=_('Datastore version ID.'),
        )
        parser.add_argument(
            '--datastore-manager',
            default=None,
            help=_("Datastore manager name."),
        )
        parser.add_argument(
            '--image',
            default=None,
            help=_('ID of the datastore image in Glance.'),
        )
        parser.add_argument(
            '--image-tags',
            default=None,
            help=_('List of image tags separated by comma, e.g. trove,mysql'),
        )
        parser.add_argument(
            '--version-name',
            help=_('New datastore version name.'),
        )

        enable_group = parser.add_mutually_exclusive_group()
        enable_group.add_argument('--enable', dest='enable',
                                  default=None,
                                  action='store_const',
                                  const='true')
        enable_group.add_argument('--disable', dest='enable',
                                  default=None,
                                  action='store_const',
                                  const='false')

        default_group = parser.add_mutually_exclusive_group()
        default_group.add_argument('--default', dest='default',
                                   default=None,
                                   action='store_const',
                                   const='true')
        default_group.add_argument('--non-default', dest='default',
                                   default=None,
                                   action='store_const',
                                   const='false')

        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.database.mgmt_ds_versions

        image_tags = None
        if parsed_args.image_tags is not None:
            image_tags = parsed_args.image_tags.split(',')

        try:
            client.edit(
                parsed_args.datastore_version_id,
                datastore_manager=parsed_args.datastore_manager,
                image=parsed_args.image,
                image_tags=image_tags,
                active=parsed_args.enable, default=parsed_args.default,
                name=parsed_args.version_name
            )
        except Exception as e:
            msg = (_("Failed to update datastore version %(version)s: %(e)s")
                   % {'version': parsed_args.datastore_version_id, 'e': e})
            raise exceptions.CommandError(msg)
