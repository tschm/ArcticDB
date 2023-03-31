#!/bin/bash

set -euo pipefail

# -j20 by default
cd /opt/arcticdb/arcticdb_link/cpp
ln -fs ../../docker/custom_cmakefiles/CMakeUserPresets_clion.json CMakeUserPresets.json

# Mount the default build directory as a tmpfs to speed up builds
mkdir -p /opt/arcticdb/arcticdb_link/cpp/out
mount -t tmpfs -o size=10G tmpfs /opt/arcticdb/arcticdb_link/cpp/out

# Symlink to the .so from the python directory to facilitate running the Python tests
cd /opt/arcticdb/arcticdb_link/python
ln -fs ../cpp/out/linux-debug-build/arcticdb/arcticdb_ext.cpython-36m-x86_64-linux-gnu.so arcticdb_ext.so

# This is where CLion looks by default for a Python venv, removes a few clicks
cd /opt/arcticdb
ln -fs /root/venv venv

cd /opt/arcticdb/arcticdb_link
# Activating the venv results in the interactive shell being falsely labelled as venv, and deactivate does not fix this
/root/venv/bin/python setup.py protoc -p python > /dev/null

cd /opt/arcticdb

/bin/bash