Python bindings to the Reddwarf API
==================================================

This is a client for the Reddwarf API. There's a Python API (the
``reddwarfclient`` module), and a command-line script (``reddwarf``). Each
implements 100% (or less ;) ) of the Reddwarf API.

Command-line API
----------------

To use the command line API, first log in using your user name, api key,
tenant, and appropriate auth url.

.. code-block:: bash

    $ reddwarf-cli --username=jsmith --apikey=abcdefg --tenant=12345 --auth_url=http://reddwarf_auth:35357/v2.0/tokens auth login

At this point you will be authenticated and given a token, which is stored
at ~/.apitoken. From there you can make other calls to the CLI.

TODO: Add docs
