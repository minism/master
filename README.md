# Synopsis

A basic web service that provides a JSON API for listing and registering IP/PORT entries, intended to be used as a master server for privately hosted networked games.

Servers are kept alive with a heartbeat request once a minute, otherwise they are removed from the list.

This can deploy to heroku out of the box.

# Security

``MASTER_KEY`` is a shared-secret key that you must generate and set in django settings.py.  It should also be baked into your game client.

**POST** and **PUT** method request bodies must always contain a field ``signature``, which is an HMAC SHA1 Hex Digest of the ``uuid`` field also sent with the request, using ``MASTER_KEY`` as the key.



# Routes

``GET /``

Returns a JSON array of alive game servers.


``POST / (Content-Type: application/json)``

Register a new game server.  Request body should be: 

    {
        "name": Name of server,
        "port": Port of server,
        "uuid": A 36-character-max UUID that you generate,
        "signature": The HMAC-SHA1 hex digest of MASTER_KEY+uuid,
    }
    
``PUT / (Content-Type: application/json)``

Update the heartbeat for a game server.  Request body should be: 

    {
        "uuid": The UUID of the game server,
        "signature": The HMAC-SHA1 hex digest of MASTER_KEY+uuid,
    }

# Deploying

*Need python, pip, and git*

Install [Heroku toolbelt](https://toolbelt.herokuapp.com/)

Get repo

    git clone git@github.com:minism/master
    cd master

Create app

    heroku create <app_name>

Push code

    git push heroku master

Create database

    heroku run ./manage.py syncdb --noinput
    
Configure shared secret key

    heroku config:add MASTER_KEY=<key>
    
Done!

    heroku open

# Additional configuration

You can set the heartbeat timeout with:

    heroku config:add HEARTBEAT_TIMEOUT=<seconds>