=========================
 Trove Client User Guide
=========================

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
``trove help``.

For more details, refer to :doc:`../cli/index`.

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

.. toctree::
   :maxdepth: 2

   api
