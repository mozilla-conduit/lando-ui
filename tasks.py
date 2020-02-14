# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os

from invoke import Collection, task, run

# The 'pty' setting is nice, as it provides colour output, but it doesn't work
# on Windows.
USE_PTY = os.name != "nt"


@task(
    name="python",
    help={
        "testargs": "Arguments to pass to the test suite (default: '')",
        "keep": "Do not remove the test container after running",
    },
)
def test_python(ctx, testargs="", keep=False):
    """Run lando-ui python tests."""
    ctx.config.keep_containers = keep  # Stashed for our cleanup tasks
    run(
        "docker-compose run {rm} lando-ui pytest {args}"
        "".format(args=testargs, rm=("" if keep else " --rm")),
        pty=USE_PTY,
        echo=True,
    )


@task(name="flake8")
def lint_flake8(ctx):
    """Run flake8."""
    run("docker-compose run --rm py3-linter flake8 .", pty=USE_PTY, echo=True)


@task(name="black")
def lint_black(ctx):
    """Run black."""
    run(
        f"docker-compose run --rm py3-linter black --diff .",  # noqa
        pty=USE_PTY,
        echo=True,
    )


@task(default=True, name="all", post=[lint_flake8, lint_black])
def lint_all(ctx):
    pass


@task(default=True, name="all")
def format_all(ctx):
    run("docker-compose run --rm py3-linter black", echo=True)


@task(default=True, name="all", post=[test_python])
def test_all(ctx):
    pass


namespace = Collection(
    Collection("test", test_python, test_all,),
    Collection("lint", lint_all, lint_flake8, lint_black,),
    Collection("format", format_all,),
)
