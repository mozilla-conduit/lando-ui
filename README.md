# lando-ui

lando-ui is a Flask-based web application that serves as a graphical
user interface to [lando-api][].  It is separate from the latter to
isolate the logic of automatic landings from its interface(s).

## Contributing

Please read the general [Conduit contribution guidelines][] before
getting into the specifics of lando-ui.

### Prerequisites

* [docker][] and [docker-compose][] (on OS X and Windows you should use
  the full [Docker for Mac][] or [Docker for Windows][] systems,
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

As Flask [requires a real server name][] to use session cookies, you
will need to make an entry in your host config or a local DNS server.
On Linux and MacOS, the hosts file is located at `/etc/hosts`; on
Windows, it is located at `C:\Windows\System32\Drivers\etc\hosts`.
The format is the same on all three OSs, requiring the addition of the
following line:

    127.0.0.1           lando-ui.test

If you are using [Docker Machine][], you will need to replace
`127.0.0.1` with the IP of your Docker Machine host.  Note that you
should use `127.0.0.1` on Windows if you use the full [Docker for Windows][]
installation.

After updating your hosts file (no reboot is required), in a terminal
simply run `docker-compose up` in the root lando-ui directory.  On
Windows, we recommend using [Git Bash][], which provides a Linux-like
terminal interface.

After a while, you will see within docker-compose's output a line like
this:

    lando-ui_1    |  * Running on http://0.0.0.0:7777/ (Press CTRL+C to quit)

At this point, you should be able to visit
`http://lando-ui.test:7777/` in your browser.

### Use with lando-api

lando-ui requires an instance of lando-api to talk to in order to
anything interesting.  The default configuration sets the location of
lando-api to `http://lando-api.test:8888`, which is the default for a
local installation of lando-api.

### Running the tests

lando-ui's tests use `pytest` with `pytest-flask`, executed within a
Docker container.  The tests are located in `./tests/`.  You can run
all of them via `invoke`:

```bash
$ invoke test
```

Subsets of the tests, e.g. linters, and other commands are also available.  Run
`invoke -l` to see all tasks.

[lando-api]: https://github.com/mozilla-conduit/lando-api
[Conduit contribution guidelines]: http://moz-conduit.readthedocs.io/en/latest/contributing.html
[docker]: https://docs.docker.com/engine/installation/
[docker-compose]: https://docs.docker.com/compose/install/
[Docker for Mac]: https://docs.docker.com/docker-for-mac/install/
[Docker for Windows]: https://docs.docker.com/docker-for-windows/install/
[requires a real server name]: http://flask.pocoo.org/docs/0.12/config/#builtin-configuration-values
[Docker Machine]: https://docs.docker.com/machine/
[Git Bash]: https://git-for-windows.github.io/
