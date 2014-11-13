Using the Client Programmatically
=================================


.. testsetup::

    # Creates some vars we don't show in the docs.
    AUTH_URL="http://localhost:8779/v1.0/auth"

    from troveclient import Dbaas
    from troveclient import auth
    class FakeAuth(auth.Authenticator):

        def authenticate(self):
            class FakeCatalog(object):
                def __init__(self, auth):
                    self.auth = auth

                def get_public_url(self):
                    return "%s/%s" % ('http://localhost:8779/v1.0',
                                      self.auth.tenant)

                def get_token(self):
                    return self.auth.tenant

            return FakeCatalog(self)

    from troveclient import Dbaas
    OLD_INIT = Dbaas.__init__
    def new_init(*args, **kwargs):
        kwargs['auth_strategy'] = FakeAuth
        OLD_INIT(*args, **kwargs)

    # Monkey patch init so it'll work with fake auth.
    Dbaas.__init__ = new_init


    client = Dbaas("jsmith", "abcdef", tenant="12345",
                  auth_url=AUTH_URL)
    client.authenticate()

    # Delete all instances.
    instances = [1]
    while len(instances) > 0:
        instances = client.instances.list()
        for instance in instances:
            try:
                instance.delete()
            except:
                pass

    flavor_id = "1"
    for i in range(30):
        name = "Instance #%d" % i
        client.instances.create(name, flavor_id, None)



Authentication
--------------

Authenticating is necessary to use every feature of the client (except to
discover available versions).

To create the client, create an instance of the Dbaas (Database as a Service)
class. The auth url, auth user, key, and tenant ID must be specified in the
call to the constructor.

.. testcode::

    from troveclient import Dbaas
    global AUTH_URL

    client = Dbaas("jsmith", "abcdef", tenant="12345",
                  auth_url=AUTH_URL)
    client.authenticate()

The default authentication strategy assumes a Keystone compliant auth system.
For Rackspace auth, use the keyword argument "auth_strategy='rax'".


Versions
--------

You can discover the available versions by querying the versions property as
follows:


.. testcode::

    versions = client.versions.index("http://localhost:8779")


The "index" method returns a list of Version objects which have the ID as well
as a list of links, each with a URL to use to reach that particular version.

.. testcode::

    for version in versions:
        print(version.id)
        for link in version.links:
            if link['rel'] == 'self':
                print("    %s" % link['href'])

.. testoutput::

    v1.0
        http://localhost:8779/v1.0/


Instances
---------

The following example creates a 512 MB instance with a 1 GB volume:

.. testcode::

    client.authenticate()
    flavor_id = "1"
    volume = {'size':1}
    databases = [{"name": "my_db",
                  "character_set": "latin2",           # These two fields
                  "collate": "latin2_general_ci"}]     # are optional.
    users = [{"name": "jsmith", "password": "12345",
              "databases": [{"name": "my_db"}]
             }]
    instance = client.instances.create("My Instance", flavor_id, volume,
                                       databases, users)

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


Listing instances and Pagination
--------------------------------

To list all instances, use the list method of "instances":

.. testcode::

    instances = client.instances.list()


Lists paginate after twenty items, meaning you'll only get twenty items back
even if there are more. To see the next set of items, send a marker. The marker
is a key value (in the case of instances, the ID) which is the non-inclusive
starting point for all returned items.

The lists returned by the client always include a "next" property. This
can be used as the "marker" argument to get the next section of the list
back from the server. If no more items are available, then the next property
is None.

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

