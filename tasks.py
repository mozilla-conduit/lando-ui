# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import os

from invoke import Collection, task, run

project_root = os.path.dirname(__file__)

# Name used by docker-compose to create a test-only docker environment.
project_test_name = 'testlandoui'


@task(name='remove-containers')
def remove_containers(ctx):
    """Remove all temporary containers created for testing."""
    if not ctx.config.get('keep_containers'):
        cmd = (
            'docker-compose'
            ' -f {project_root}/docker-compose.yml'
            ' -p {test_project_name}'
        ).format(
            project_root=project_root, test_project_name=project_test_name
        )

        ctx.run(cmd + ' stop', pty=True, echo=True)
        ctx.run(cmd + ' rm --force -v', pty=True, echo=True)


@task(
    name='python',
    help={
        'testargs': 'Arguments to pass to the test suite (default: \'\')',
        'keep': 'Do not remove the test container after running',
    },
    post=[remove_containers]
)
def test_python(ctx, testargs='', keep=False):
    """Run lando-ui python tests."""
    ctx.config.keep_containers = keep  # Stashed for our cleanup tasks
    run(
        'docker-compose'
        ' -f {project_root}/docker-compose.yml'
        ' -p {test_project_name}'
        ' run'
        '{rm}'
        ' lando-ui'
        ' pytest {args}'
        ''.format(
            project_root=project_root,
            test_project_name=project_test_name,
            args=testargs,
            rm=('' if keep else ' --rm')
        ),
        pty=True,
        echo=True
    )


@task(
    name='javascript',
    help={
        'testargs': 'Arguments to pass to the test suite (default: \'\')',
        'keep': 'Do not remove the test container after running',
        'no_pty': 'Execute tests without a pty.',
    }
)
def test_javascript(ctx, testargs='', keep=False, no_pty=False):
    """Test landui javascript tests."""
    run(
        'docker-compose'
        ' -f {project_root}/docker-compose.yml'
        ' -p {test_project_name}'
        ' run'
        '{rm}'
        ' yarn'
        ' test {args}'
        ''.format(
            project_root=project_root,
            test_project_name=project_test_name,
            args=testargs,
            rm=('' if keep else ' --rm')
        ),
        pty=not no_pty,
        echo=True
    )


@task(name='flake8')
def lint_flake8(ctx):
    """Run flake8."""
    run(
        'docker-compose'
        ' -f {project_root}/docker-compose.yml'
        ' run'
        ' --rm'
        ' py3-linter'
        ' flake8 ./'
        ''.format(project_root=project_root),
        pty=True,
        echo=True
    )


@task(name='yapf')
def lint_yapf(ctx):
    """Run yapf."""
    run(
        'docker-compose'
        ' -f {project_root}/docker-compose.yml'
        ' run'
        ' --rm'
        ' py3-linter'
        ' yapf'
        ' --diff --recursive'
        ' ./'
        ''.format(project_root=project_root),
        pty=True,
        echo=True
    )


@task(default=True, name='all', post=[lint_flake8, lint_yapf])
def lint_all(ctx):
    pass


@task(default=True, name='all')
def format_all(ctx):
    run(
        'docker-compose'
        ' -f {project_root}/docker-compose.yml'
        ' run'
        ' --rm'
        ' py3-linter'
        ' yapf'
        ' --in-place --recursive'
        ' ./'
        ''.format(project_root=project_root),
        echo=True
    )


@task(default=True, name="all", post=[test_python, test_javascript])
def test_all(ctx):
    pass


@task(name='version')
def version_json(ctx):
    """Print version information in JSON format."""
    version = {
        'commit': os.getenv('CIRCLE_SHA1', None),
        'version': os.getenv('CIRCLE_SHA1', None),
        'source': 'https://github.com/mozilla-conduit/lando-ui',
        'build': os.getenv('CIRCLE_BUILD_URL', None)
    }
    print(json.dumps(version))


namespace = Collection(
    Collection(
        'test',
        test_python,
        test_javascript,
        test_all,
        remove_containers,
    ),
    Collection(
        'lint',
        lint_all,
        lint_flake8,
        lint_yapf,
    ),
    Collection(
        'format',
        format_all,
    ),
    version_json,
)
