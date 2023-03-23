#!/bin/bash
source scl_source enable devtoolset-10
if [[ $@ == *"Unix Makefiles"* ]]; then
  /opt/arcticc/venv/bin/cmake -DPython_ROOT_DIR="/usr/lib64" -DPython_EXECUTABLE="/usr/bin/python3" "$@"
else
  python -mgrpc_tools.protoc -Iarcticdb_link/cpp/proto --python_out=arcticdb_link/python/ arcticdb_link/cpp/proto/arcticc/pb2/*.proto
  /opt/arcticc/venv/bin/cmake "$@"
fi
