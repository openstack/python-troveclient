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

"""Database v1 SSL action implementations"""

from osc_lib.command import command
from osc_lib import utils as osc_utils

from troveclient.i18n import _


def set_attributes_for_print_detail(ssl):
    info = ssl.to_dict()
    cert = info.pop('certificate', None)

    if isinstance(cert, dict):
        info.update({f"certificate.{k}": v for k, v in cert.items()})

    return info


class EnableInstanceSSL(command.ShowOne):

    _description = _("Enables ssl for an instance.")

    def get_parser(self, prog_name):
        parser = super(EnableInstanceSSL, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            help=_('ID or name of the instance or cluster.'),
        )
        parser.add_argument(
            'container_ref',
            metavar='<container_ref>',
            help=_('URL to barbican container in pkcs#12 format'))
        parser.add_argument(
            '--mode',
            metavar='<mode>',
            dest='mode',
            default='basic',
            help=_('SSL mode. Available options are: '
                   'basic (default), enforced, mtls). '
                   'Refer to documentation for details.'))
        parser.add_argument(
            '--password_ref',
            dest='password_ref',
            metavar='<password_ref>',
            default=None,
            help=_('URL to barbican key required to decrypt data from'
                   'provided pkcs#12 container (if necessary)'))

        return parser

    def take_action(self, parsed_args):
        database_client_manager = self.app.client_manager.database

        db_instances = database_client_manager.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)
        mode = parsed_args.mode

        password_ref = parsed_args.password_ref
        instances = database_client_manager.instances
        ssl_info = instances.ssl_enable(instance, mode,
                                        parsed_args.container_ref,
                                        password_ref=password_ref)
        return zip(*sorted(ssl_info.items()))


class DisableInstanceSSL(command.ShowOne):

    _description = _("Disables ssl for an instance.")

    def get_parser(self, prog_name):
        parser = super(DisableInstanceSSL, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            help=_('ID or name of the instance.'),
        )

        return parser

    def take_action(self, parsed_args):
        database_client_manager = self.app.client_manager.database

        db_instances = database_client_manager.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)

        instances = database_client_manager.instances
        ssl_info = instances.ssl_disable(instance)
        return zip(*sorted(ssl_info.items()))


class ShowInstanceSSL(command.ShowOne):

    _description = _("Gets status of the SSL and installed certificate "
                     "(if present) for an instance.")

    def get_parser(self, prog_name):
        parser = super(ShowInstanceSSL, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            help=_('ID or name of the instance.'),
        )
        parser.add_argument(
            '--include-certificate',
            dest='include_certificate',
            action='store_true',
            default=False,
            help=_('Include certificate payload in the output'))

        return parser

    def take_action(self, parsed_args):
        database_client_manager = self.app.client_manager.database

        db_instances = database_client_manager.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)

        instances = database_client_manager.instances
        ssl_info = instances.ssl_show(
            instance, include_certificate=parsed_args.include_certificate)
        ssl_info = set_attributes_for_print_detail(ssl_info)
        return zip(*sorted(ssl_info.items()))


class RollbackInstanceSSL(command.ShowOne):

    _description = _("Rolls back the last SSL configuration for an instance.")

    def get_parser(self, prog_name):
        parser = super(RollbackInstanceSSL, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar='<instance>',
            help=_('ID or name of the instance.'),
        )

        return parser

    def take_action(self, parsed_args):
        database_client_manager = self.app.client_manager.database

        db_instances = database_client_manager.instances
        instance = osc_utils.find_resource(db_instances,
                                           parsed_args.instance)

        instances = database_client_manager.instances
        ssl_info = instances.ssl_rollback(instance)
        return zip(*sorted(ssl_info.items()))
