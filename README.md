# Lando UI

lando-ui is a Flask-based web application that serves as a graphical
user interface to [Lando API](https://github.com/mozilla-conduit/lando-api).
It is separate from the latter to isolate the logic of automatic landings
from its interface(s).

[![What's Deployed](https://img.shields.io/badge/whatsdeployed-prod,dev-green.svg)](https://whatsdeployed.io/s-a0C)

## Contributing

Please read the general [Conduit contribution guidelines](http://moz-conduit.readthedocs.io/en/latest/contributing.html)
before getting into the specifics of lando-ui.

### Prerequisites

* [docker](https://docs.docker.com/engine/installation/) and [docker-compose](https://docs.docker.com/compose/install/)
  (on OS X and Windows you should use the full [Docker for Mac](https://docs.docker.com/docker-for-mac/install/)
  or [Docker for Windows](https://docs.docker.com/docker-for-windows/install/) systems,
  respectively)
* `pyinvoke`
  * Because `pyinvoke` currently has no backwards-compatibility guarantees,
    it is suggested that you install exactly version 0.21.0 via `pip`:
    `pip install invoke==0.21.0` or `pip install --user invoke==0.21.0`.
  * You can use a virtualenv instead of installing it system wide, but you
    should create the virtualenv *outside* of the lando-ui source directory so
    that the linter doesn't check the virtualenv files.
  * If you are running Windows, you will need a special file in your user
    directory (typically `C:\Users\<username>\`) called `.invoke.yml`.  It
    should contain the following:

        ```yaml
        run:
          shell: C:\Windows\System32\cmd.exe
        ```

### Basic setup

As Flask [requires a real server name](https://flask.palletsprojects.com/en/1.1.x/config/#SESSION_COOKIE_DOMAIN)
to use session cookies, you will need to make an entry in your host
config or a local DNS server. On Linux and MacOS, the hosts file is
located at `/etc/hosts`; on Windows, it is located at `C:\Windows\System32\Drivers\etc\hosts`.
The format is the same on all three OSs, requiring the addition of the
following line:

    127.0.0.1           lando-ui.test

If you are using [Docker Machine](https://docs.docker.com/machine/),
you will need to replace `127.0.0.1` with the IP of your Docker Machine
host.  Note that you should use `127.0.0.1` on Windows if you use the
full Docker for Windows installation.

After updating your hosts file (no reboot is required), in a terminal
simply run `docker-compose up` in the root lando-ui directory.  On
Windows, we recommend using [Git Bash](https://git-for-windows.github.io/),
which provides a Linux-like terminal interface.

After a while, you will see within docker-compose's output a line like
this:

    lando-ui_1    |  * Running on http://0.0.0.0:7777/ (Press CTRL+C to quit)

At this point, you should be able to visit
`http://lando-ui.test:7777/` in your browser.

### Use with lando-api

lando-ui requires an instance of lando-api to talk to in order to do
anything interesting.  The default configuration sets the location of
lando-api to `http://lando-api.test:8888`, which is the default for a
local installation of lando-api.

### Running the tests

lando-ui's tests use `pytest` with `pytest-flask`, executed within a
Docker container.  The tests are located in `./tests/`.  You can run
all of them via `invoke`:

    ```bash
    invoke test
    ```

Subsets of the tests, e.g. linters, and other commands are also available.  Run
`invoke -l` to see all tasks.

### Updating Requirements

Requirements are tracked using `pip-compile`'s input format as `requirements.in`,
which generates a `requirements.txt`. You can re-compile the requirements file
using the same Python version as in the `Dockerfile` using the `build-requirements`
recipe in `docker-compose`:

    ```shell
    docker-compose run build-requirements
    ```

### Setting up Auth0

We use [Auth0](https://auth0.com/) to authenticate application users.
You will need to sign up for a personal Auth0 account to manually test
code landing workflows and protected pages.

After signing up you must create an Auth0 Application for lando-ui testing.
See the Auth0 docs for details on how to do this.

Once you have created the lando-ui Application in your Auth0 management dashboard,
go to the `Application` page and configure the following:

* `Client Type: Regular Web Application`
* `Token Endpoint Authentication Method: POST`
* `Allowed Callback URLs: http://lando-ui.test:7777/redirect_uri, http://lando-ui.test/redirect_uri`
* `Allowed Web Origins: (leave blank)`
* `Allowed Logout URLs: http://lando-ui.test:7777/signout, http://lando-ui.test/signout`
* `Allowed Origins (CORS): (leave blank)`
* Click `Show Advanced Settings` on the `Client Settings` page, then select the `OAuth`
  tab:
  * `JsonWebToken Signature Algorithm: HS256`

Create an Auth0 API (click `API` in the Auth0 left side bar)

* `Name: lando-api`
* `Identifier/URI: http://lando-api.test`
* `Signing Algorithm: RS256`
* Go to the new API's `Permissions` tab and add a permission:
  * `Name: lando`
  * `Description: Bearer has authorized Lando to land code on their behalf`

Create a `docker-compose.override.yml` file in repository's root directory with
the following:

    ```yaml
    version: '2'
    services:
      lando-ui:
        environment:
          - OIDC_DOMAIN=your personal auth0 domain with no http prefix
          - OIDC_CLIENT_ID=your Auth0 Client ID (from the Client Settings page)
          - OIDC_CLIENT_SECRET=your Auth0 Client Secret (from the Client Settings page)
          - LANDO_API_OIDC_IDENTIFIER=the identifier you gave to the API you made (e.g. http://lando-api.test)
    ```

Restart the lando-ui service with docker-compose.

To log in to your new service you must create a User account.

  1. Visit `http://lando-ui.test:7777/` in your browser.  You should  see the Lando
     front page as a signed-out or anonymous user would see it.
  1. Click the "Log in" button on the top navigation bar and you will be presented
     with the lando-ui sign-in page.
  1. On the lando-ui sign-in page click the "Sign Up" tab.
  1. Follow the sign-up instructions. (Using the "Sign Up With Google" button makes
     this task trivial.)

 You should now be able to use the lando-ui "Log in" and "Log out" buttons.

### How do I make the Land button work?

You need to change some settings in the lando-api service to make the
Land button in lando-ui function.  See the `LOCALDEV_MOCK`
environment variables in the [lando-api docker-compose.yml](https://github.com/mozilla-conduit/lando-api/blob/master/docker-compose.yml)
for details.

### Developing and testing against Conduit Suite

Sometimes it's necessary to use a more realistic infrastructure setup to test template
rendering, frontend/backend interactions, and to test with special case data such
as secure revisions.  We can achieve this by running our Lando UI project code inside
the [Conduit Suite](https://github.com/mozilla-conduit/suite) project's development
environment. Conduit Suite provides all of the collaborating services (Lando API,
Phabricator, BMO) necessary for Lando UI to function as the real service would.

1. First set up Auth0 according to the Setting up Auth0 instruction section above.

1. Next follow the [Conduit Suite] generic setup instructions.  Verify that you can
run the Suite project from in it's own project directory with `docker-compose up`.
Verify that you can use the `firefox-proxy` script in the Suite project's root
directory to access the Suite's bundled copy of Lando UI.

1. Once you have the Suite running with it's bundled copy of Lando UI you can modify
its `docker-compose` configuration to build and run lando-ui from the sources in
the project directory you have been hacking in.  Instructions are in the Conduit
Suite project README.

## Support

To chat with Lando users and developers, join them on [Matrix](https://chat.mozilla.org/#/room/#conduit:mozilla.org).
