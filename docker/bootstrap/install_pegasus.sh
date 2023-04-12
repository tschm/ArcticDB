#!/bin/bash

set -euo pipefail

curl -qkfsSL "https://repo.prod.m/artifactory/man/pegasus-cli/master/pegasus.sh" > /usr/local/bin/pegasus
chmod +x /usr/local/bin/pegasus

PYTHON_VERSION=3.6
curl -qkfsSL "https://repo.prod.m/artifactory/man/pegasus-cli/master/pegasusenv${PYTHON_VERSION}.tar.lz" > /usr/local/bin/pegasusenv${PYTHON_VERSION}.tar.lz

PYTHON_VERSION=3.8
curl -qkfsSL "https://repo.prod.m/artifactory/man/pegasus-cli/master/pegasusenv${PYTHON_VERSION}.tar.lz" > /usr/local/bin/pegasusenv${PYTHON_VERSION}.tar.lz
