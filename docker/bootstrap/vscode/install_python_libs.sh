#!/bin/bash
# To be run INSIDE THE CONTAINER!
VENV_LOCATION="/root/venv"
if [ -d "$VENV_LOCATION" ]; then
    echo "$VENV_LOCATION exists. Skipping setup"
else
    python3 -m venv "$VENV_LOCATION"
    source "$VENV_LOCATION"/bin/activate
    pip_cmd="pip --proxy http://10.193.3.6:8080/ --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org install"
    $pip_cmd --upgrade pip
    requirements=$(grep -Po "  .*" /opt/arcticdb/arcticdb_link/setup.cfg | grep -v '#' | grep -v ':' | cut -d';' -f1)
    for line in $requirements; do $pip_cmd $line; done
fi