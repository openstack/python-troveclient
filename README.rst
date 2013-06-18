Python bindings to the Trove API
==================================================

This is a client for the Trove API. There's a Python API (the
``troveclient`` module), and a command-line script (``trove``). Each
implements 100% (or less ;) ) of the Trove API.

Command-line API
----------------

To use the command line API, first log in using your user name, api key,
tenant, and appropriate auth url.

.. code-block:: bash

    $ trove-cli --username=jsmith --apikey=abcdefg --tenant=12345 --auth_url=http://trove_auth:35357/v2.0/tokens auth login

At this point you will be authenticated and given a token, which is stored
at ~/.apitoken. From there you can make other calls to the CLI.

TODO: Add docs
