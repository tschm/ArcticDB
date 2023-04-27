#!/bin/bash

set -euo pipefail

# Create pegasus-current and pegasus-next venvs
pegasus pegasus-current -d current > /dev/null 2>&1
pegasus pegasus-next -d next > /dev/null 2>&1

mkdir -p /root/.config/pip
cat >> /root/.config/pip/pip.conf << EOF
[global]
trusted-host = repo.prod.m
index-url = https://repo.prod.m/artifactory/api/pypi/external-pypi/simple/
EOF

# -j8 by default
cd /opt/arcticdb/arcticdb_link/cpp
ln -fs ../../docker/custom_cmakefiles/CMakeUserPresets_clion.json CMakeUserPresets.json

# Mount the default build directory as a tmpfs to speed up builds
mkdir -p /opt/arcticdb/arcticdb_link/cpp/out
mount -t tmpfs -o size=10G tmpfs /opt/arcticdb/arcticdb_link/cpp/out

# Symlink to the .so from the python directory to facilitate running the Python tests
cd /opt/arcticdb/arcticdb_link/python
ln -fs ../cpp/out/linux-debug-build/arcticdb/arcticdb_ext.cpython-36m-x86_64-linux-gnu.so .
ln -fs ../cpp/out/linux-debug-build/arcticdb/arcticdb_ext.cpython-38-x86_64-linux-gnu.so .

# This is where CLion looks by default for a Python venv, removes a few clicks
cd /opt/arcticdb
ln -fs /root/pyenvs/dev venv
cd /opt/arcticdb/arcticdb_link

# Activating the venv results in the interactive shell being falsely labelled as venv, and deactivate does not fix this
/root/pyenvs/dev/bin/python setup.py protoc --build-lib python > /dev/null 2>&1

cd /opt/arcticdb

# Fails to upload to nuget. We should investigate and reinstate at some point.
#export VCPKG_BINARY_SOURCES=nugetconfig,/opt/arcticdb/docker/nuget.config,readwrite
#export VCPKG_USE_NUGET_CACHE=1

/bin/bash
