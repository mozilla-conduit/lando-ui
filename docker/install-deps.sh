#!/bin/sh
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -euxo pipefail

apk add --update --no-cache \
    gcc \
    git \
    libc-dev \
    musl-dev \
    linux-headers \
    pcre \
    pcre-dev \
    openssl-dev \
    libffi-dev

for file in "$@"; do
    pip install --no-cache -r "$file"
done
