# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='lando-ui',
    version='0.1',
    description='The UI for Lando (Mozilla\'s automatic code lander)',
    long_description=long_description,
    url='https://github.com/mozilla-conduit/lando-ui',
    author='Mozilla',
    author_email='dev-version-control@lists.mozilla.org',
    license='MPL 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='mozilla lando development',
    packages=find_packages(exclude=['tests']),
    install_requires=['Flask==0.12.1', 'requests==2.13.0', 'click==6.7'],
    extras_require={
        'test': ['pytest', 'yapf', 'flake8', 'invoke'],
    },
    entry_points={
        'console_scripts': [
            'lando-ui-dev=landoui.app:run_dev_server',
        ],
        'flask.commands': [
            'assets = flask_assets:assets',
        ],
    },
)
