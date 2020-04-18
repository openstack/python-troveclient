=========================
 Trove Client User Guide
=========================

Command-line Interface
----------------------

Installing this package allows you to use ``openstack`` command to interact
with Trove. Refer to
https://docs.openstack.org/python-openstackclient/latest
for how to install ``openstack`` command and configuration.

You can find all supported Trove commands in ``openstack.database.v1``
entry_points section in ``setup.cfg`` file of the repo.

Python API
----------

There's also a complete Python API.

Quick-start using keystone::

    >>> from troveclient import client
    >>> trove_client = client.Client('1.0', session=keystone_session, endpoint_type='public', service_type='database', region_name='RegionOne')
    >>> trove_client.datastores.list()
    [...]
    >>> trove_client.instances.list()
    [...]

.. toctree::
   :maxdepth: 2

   api
