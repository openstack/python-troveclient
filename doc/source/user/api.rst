Using the Client Programmatically
=================================

Authentication
--------------

Authenticating is necessary to use every feature of the client.

To create the client, create an instance of the Client class.
The auth url, username, password, and project name must be specified in the
call to the constructor.

.. testcode::

    from troveclient.v1 import client
    tc = client.Client(username="testuser",
            password="PASSWORD",
            project_id="test_project",
            region_name="EAST",
            auth_url="http://api-server:5000/v2.0")

The default authentication strategy assumes a keystone compliant auth system.

Once you have an authenticated client object you can make calls with it,
for example:

.. testcode::

    flavors = tc.flavors.list()
    datastores = tc.datastores.list()

Instances
---------

The following example creates a 512 MB instance with a 1 GB volume:

.. testcode::

    from troveclient.v1 import client
    tc = client.Client(username="testuser",
            password="PASSWORD",
            project_id="test_project",
            region_name="EAST",
            auth_url="http://api-server:5000/v2.0")

    flavor_id = '1'
    volume = {'size':1}
    databases = [{"name": "my_db",
                  "character_set": "latin2",           # These two fields
                  "collate": "latin2_general_ci"}]     # are optional.
    datastore = 'mysql'
    datastore_version = '5.6-104'
    users = [{"name": "jsmith", "password": "12345",
              "databases": [{"name": "my_db"}]
             }]
    instance = client.instances.create("My Instance", flavor_id, volume,
                                       databases, users, datastore=datastore,
                                       datastore_version=datastore_version)

To retrieve the instance, use the "get" method of "instances":

.. testcode::

    updated_instance = client.instances.get(instance.id)
    print(updated_instance.name)
    print("   Status=%s Flavor=%s" %
              (updated_instance.status, updated_instance.flavor['id']))

.. testoutput::

    My Instance
       Status=BUILD Flavor=1

You can delete an instance by calling "delete" on the instance object itself,
or by using the delete method on "instances."

.. testcode::

    # Wait for the instance to be ready before we delete it.
    import time
    from troveclient.exceptions import NotFound

    while instance.status == "BUILD":
        instance.get()
        time.sleep(1)
    print("Ready in an %s state." % instance.status)
    instance.delete()
    # Delete and wait for the instance to go away.
    while True:
        try:
            instance = client.instances.get(instance.id)
            assert instance.status == "SHUTDOWN"
        except NotFound:
            break

.. testoutput::

    Ready in an ACTIVE state.


Listing Items and Pagination
--------------------------------

Lists paginate after twenty items, meaning you'll only get twenty items back
even if there are more. To see the next set of items, send a marker. The marker
is a key value (in the case of instances, the ID) which is the non-inclusive
starting point for all returned items.

The lists returned by the client always include a "next" property. This
can be used as the "marker" argument to get the next section of the list
back from the server. If no more items are available, then the next property
is None.

Pagination applies to all listed objects, like instances, datastores, etc.
The example below is for instances.

.. testcode::

    # There are currently 30 instances.

    instances = client.instances.list()
    print(len(instances))
    print(instances.next is None)

    instances2 = client.instances.list(marker=instances.next)
    print(len(instances2))
    print(instances2.next is None)

.. testoutput::

    20
    False
    10
    True

