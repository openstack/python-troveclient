Python bindings to the OpenStack Trove API
==========================================

.. image:: https://img.shields.io/pypi/v/python-troveclient.svg
    :target: https://pypi.python.org/pypi/python-troveclient/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/dm/python-troveclient.svg
    :target: https://pypi.python.org/pypi/python-troveclient/
    :alt: Downloads

This is a client for the OpenStack Trove API. There's a Python API (the
``troveclient`` module), and a command-line script (``trove``). Each
implements 100% of the OpenStack Trove API.

See the `OpenStack CLI guide`_ for information on how to use the ``trove``
command-line tool. You may also want to look at the
`OpenStack API documentation`_.

.. _OpenStack CLI Guide: http://docs.openstack.org/user-guide/cli.html
.. _OpenStack API documentation: http://docs.openstack.org/api/quick-start/content/

python-troveclient is licensed under the Apache License like the rest of OpenStack.

* License: Apache License, Version 2.0
* `PyPi`_ - package installation
* `Online Documentation`_
* `Blueprints`_ - feature specifications
* `Bugs`_ - issue tracking
* `Git Source`_
* `Github`_
* `Specs`_
* `How to Contribute`_

.. _PyPi: https://pypi.python.org/pypi/python-troveclient
.. _Online Documentation: http://docs.openstack.org/developer/python-troveclient
.. _Blueprints: https://blueprints.launchpad.net/python-troveclient
.. _Bugs: https://bugs.launchpad.net/python-troveclient
.. _Git Source: https://git.openstack.org/cgit/openstack/python-troveclient
.. _Github: https://github.com/openstack/python-troveclient
.. _How to Contribute: http://docs.openstack.org/infra/manual/developers.html
.. _Specs: http://specs.openstack.org/openstack/trove-specs/

.. contents:: Contents:
   :local:

Command-line API
----------------

Installing this package gets you a shell command, ``trove``, that you
can use to interact with any OpenStack cloud.

You'll need to provide your OpenStack username and password. You can do this
with the ``--os-username``, ``--os-password`` and  ``--os-tenant-name``
params, but it's easier to just set them as environment variables::

    export OS_USERNAME=openstack
    export OS_PASSWORD=yadayada
    export OS_TENANT_NAME=myproject

You will also need to define the authentication url with ``--os-auth-url`` and
the version of the API with ``--os-database-api-version`` (default is version
1.0).  Or set them as an environment variables as well::

    export OS_AUTH_URL=http://example.com:5000/v2.0/
    export OS_AUTH_URL=1.0

If you are using Keystone, you need to set the OS_AUTH_URL to the keystone
endpoint::

        export OS_AUTH_URL=http://example.com:5000/v2.0/

Since Keystone can return multiple regions in the Service Catalog, you
can specify the one you want with ``--os-region-name`` (or
``export OS_REGION_NAME``). It defaults to the first in the list returned.

Argument ``--profile`` is available only when the osprofiler lib is installed.

You'll find complete documentation on the shell by running
``trove help``::

    usage: trove [--version] [--debug] [--os-auth-system <auth-system>]
             [--service-type <service-type>] [--service-name <service-name>]
             [--bypass-url <bypass-url>]
             [--database-service-name <database-service-name>]
             [--endpoint-type <endpoint-type>]
             [--os-database-api-version <database-api-ver>]
             [--retries <retries>] [--json] [--profile HMAC_KEY] [--insecure]
             [--os-cacert <ca-certificate>] [--os-cert <certificate>]
             [--os-key <key>] [--timeout <seconds>]
             [--os-auth-url OS_AUTH_URL] [--os-domain-id OS_DOMAIN_ID]
             [--os-domain-name OS_DOMAIN_NAME] [--os-project-id OS_PROJECT_ID]
             [--os-project-name OS_PROJECT_NAME]
             [--os-project-domain-id OS_PROJECT_DOMAIN_ID]
             [--os-project-domain-name OS_PROJECT_DOMAIN_NAME]
             [--os-trust-id OS_TRUST_ID] [--os-user-id OS_USER_ID]
             [--os-username OS_USERNAME]
             [--os-user-domain-id OS_USER_DOMAIN_ID]
             [--os-user-domain-name OS_USER_DOMAIN_NAME]
             [--os-password OS_PASSWORD] [--os-tenant-name <auth-tenant-name>]
             [--os-tenant-id <tenant-id>] [--os-auth-token OS_AUTH_TOKEN]
             [--os-region-name <region-name>]
             <subcommand> ...

    Command-line interface to the OpenStack Trove API.

    Positional arguments:
    <subcommand>
    backup-copy                   Creates a backup from another backup.
    backup-create                 Creates a backup of an instance.
    backup-delete                 Deletes a backup.
    backup-list                   Lists available backups.
    backup-list-instance          Lists available backups for an instance.
    backup-show                   Shows details of a backup.
    cluster-create                Creates a new cluster.
    cluster-delete                Deletes a cluster.
    cluster-grow                  Adds more instances to a cluster.
    cluster-instances             Lists all instances of a cluster.
    cluster-list                  Lists all the clusters.
    cluster-show                  Shows details of a cluster.
    cluster-shrink                Drops instances from a cluster.
    configuration-attach          Attaches a configuration group to an
                                  instance.
    configuration-create          Creates a configuration group.
    configuration-default         Shows the default configuration of an
                                  instance.
    configuration-delete          Deletes a configuration group.
    configuration-detach          Detaches a configuration group from an
                                  instance.
    configuration-instances       Lists all instances associated with a
                                  configuration group.
    configuration-list            Lists all configuration groups.
    configuration-parameter-list  Lists available parameters for a
                                  configuration group.
    configuration-parameter-show  Shows details of a configuration parameter.
    configuration-patch           Patches a configuration group.
    configuration-show            Shows details of a configuration group.
    configuration-update          Updates a configuration group.
    create                        Creates a new instance.
    database-create               Creates a database on an instance.
    database-delete               Deletes a database from an instance.
    database-list                 Lists available databases on an instance.
    datastore-list                Lists available datastores.
    datastore-show                Shows details of a datastore.
    datastore-version-list        Lists available versions for a datastore.
    datastore-version-show        Shows details of a datastore version.
    delete                        Deletes an instance.
    detach-replica                Detaches a replica instance from its
                                  replication source.
    eject-replica-source          Ejects a replica source from its set.
    flavor-list                   Lists available flavors.
    flavor-show                   Shows details of a flavor.
    limit-list                    Lists the limits for a tenant.
    list                          Lists all the instances.
    log-disable                   Instructs Trove guest to stop collecting log
                                  details.
    log-discard                   Instructs Trove guest to discard the
                                  container of the published log.
    log-enable                    Instructs Trove guest to start collecting
                                  log details.
    log-list                      Lists the log files available for instance.
    log-publish                   Instructs Trove guest to publish latest log
                                  entries on instance.
    log-save                      Save log file for instance.
    log-show                      Instructs Trove guest to show details of
                                  log.
    log-tail                      Display log entries for instance.
    metadata-create               Creates metadata in the database for
                                  instance <id>.
    metadata-delete               Deletes metadata for instance <id>.
    metadata-edit                 Replaces metadata value with a new one, this
                                  is non-destructive.
    metadata-list                 Shows all metadata for instance <id>.
    metadata-show                 Shows metadata entry for key <key> and
                                  instance <id>.
    metadata-update               Updates metadata, this is destructive.
    promote-to-replica-source     Promotes a replica to be the new replica
                                  source of its set.
    resize-instance               Resizes an instance with a new flavor.
    resize-volume                 Resizes the volume size of an instance.
    restart                       Restarts an instance.
    root-disable                  Disables root for an instance.
    root-enable                   Enables root for an instance and resets if
                                  already exists.
    root-show                     Gets status if root was ever enabled for an
                                  instance or cluster.
    secgroup-add-rule             Creates a security group rule.
    secgroup-delete-rule          Deletes a security group rule.
    secgroup-list                 Lists all security groups.
    secgroup-list-rules           Lists all rules for a security group.
    secgroup-show                 Shows details of a security group.
    show                          Shows details of an instance.
    update                        Updates an instance: Edits name,
                                  configuration, or replica source.
    user-create                   Creates a user on an instance.
    user-delete                   Deletes a user from an instance.
    user-grant-access             Grants access to a database(s) for a user.
    user-list                     Lists the users for an instance.
    user-revoke-access            Revokes access to a database for a user.
    user-show                     Shows details of a user of an instance.
    user-show-access              Shows access details of a user of an
                                  instance.
    user-update-attributes        Updates a user's attributes on an instance.
    bash-completion               Prints arguments for bash_completion.
    help                          Displays help about this program or one of
                                  its subcommands.

    Optional arguments:
    --version                       Show program's version number and exit.
    --debug                         Print debugging output.
    --os-auth-system <auth-system>  Defaults to env[OS_AUTH_SYSTEM].
    --service-type <service-type>   Defaults to database for most actions.
    --service-name <service-name>   Defaults to env[TROVE_SERVICE_NAME].
    --bypass-url <bypass-url>       Defaults to env[TROVE_BYPASS_URL].
    --database-service-name <database-service-name>
                                  Defaults to
                                  env[TROVE_DATABASE_SERVICE_NAME].
    --endpoint-type <endpoint-type>
                                  Defaults to env[TROVE_ENDPOINT_TYPE] or
                                  publicURL.
    --os-database-api-version <database-api-ver>
                                  Accepts 1, defaults to
                                  env[OS_DATABASE_API_VERSION].
    --retries <retries>             Number of retries.
    --json, --os-json-output        Output JSON instead of prettyprint. Defaults
                                  to env[OS_JSON_OUTPUT].
    --profile HMAC_KEY              HMAC key used to encrypt context data when
                                  profiling the performance of an operation.
                                  This key should be set to one of the HMAC
                                  keys configured in Trove (they are found in
                                  api-paste.ini, typically in /etc/trove).
                                  Without the key, profiling will not be
                                  triggered even if it is enabled on the
                                  server side. Defaults to
                                  env[OS_PROFILE_HMACKEY].
    --insecure                      Explicitly allow client to perform
                                  "insecure" TLS (https) requests. The
                                  server's certificate will not be verified
                                  against any certificate authorities. This
                                  option should be used with caution.
    --os-cacert <ca-certificate>    Specify a CA bundle file to use in verifying
                                  a TLS (https) server certificate. Defaults
                                  to env[OS_CACERT].
    --os-cert <certificate>         Defaults to env[OS_CERT].
    --os-key <key>                  Defaults to env[OS_KEY].
    --timeout <seconds>             Set request timeout (in seconds).
    --os-auth-url OS_AUTH_URL       Authentication URL
    --os-domain-id OS_DOMAIN_ID     Domain ID to scope to
    --os-domain-name OS_DOMAIN_NAME
                                  Domain name to scope to
    --os-project-id OS_PROJECT_ID   Project ID to scope to
    --os-project-name OS_PROJECT_NAME
                                  Project name to scope to
    --os-project-domain-id OS_PROJECT_DOMAIN_ID
                                  Domain ID containing project
    --os-project-domain-name OS_PROJECT_DOMAIN_NAME
                                  Domain name containing project
    --os-trust-id OS_TRUST_ID       Trust ID
    --os-user-id OS_USER_ID         User ID
    --os-username OS_USERNAME, --os-user_name OS_USERNAME
                                  Username
    --os-user-domain-id OS_USER_DOMAIN_ID
                                  User's domain id
    --os-user-domain-name OS_USER_DOMAIN_NAME
                                  User's domain name
    --os-password OS_PASSWORD       User's password
    --os-tenant-name <auth-tenant-name>
                                  Tenant to request authorization on. Defaults
                                  to env[OS_TENANT_NAME].
    --os-tenant-id <tenant-id>      Tenant to request authorization on. Defaults
                                  to env[OS_TENANT_ID].
    --os-auth-token OS_AUTH_TOKEN   Defaults to env[OS_AUTH_TOKEN]
    --os-region-name <region-name>  Specify the region to use. Defaults to
                                  env[OS_REGION_NAME].

    See "trove help COMMAND" for help on a specific command.


Python API
----------

There's also a complete Python API.

Quick-start using keystone::

    # use v2.0 auth with http://example.com:5000/v2.0/
    >>> from troveclient.v1 import client
    >>> nt = client.Client(USERNAME, PASSWORD, TENANT_NAME, AUTH_URL)
    >>> nt.datastores.list()
    [...]
    >>> nt.flavors.list()
    [...]
    >>> nt.instances.list()
    [...]

* Documentation: http://docs.openstack.org/developer/python-troveclient/
