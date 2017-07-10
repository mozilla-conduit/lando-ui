# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from flask import (request, session)


def set_last_local_referrer():
    """
    Sets the url of the last route that the user visited on this server.
    
    This is mainly used to implement our login flow: 
        - Most pages are initially public (i.e. you do not have to sign in).
          This means they cannot be protected with the 'oidc_auth' decorator.
        - Routes protected with the 'oidc_auth' decorator require login 
          before any code in that route is executed. 
        - Going to a protected route will immediately redirect to Auth0.
        - Upon successful login, flask-pyoidc will redirect back to the original
          route that was decorated.
    
    Considering this we need a dedicated 'signin' route which will be protected
    and when the user is redirected back to the route, it will then redirect 
    them to the last_local_referrer stored in their session.
    This referrer can of course be used for many other things.
    
    This does not activate for the IGNORED_ROUTES defined inside this method.
    """
    IGNORED_ROUTES = ['/signin', '/signout']
    full_path = request.script_root + request.path
    if full_path not in IGNORED_ROUTES:
        session['last_local_referrer'] = request.url
