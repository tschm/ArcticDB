#!/bin/bash

set -euo pipefail

version=36
port=2222

usage () {
    echo "USAGE: Pass version (36, 38, medusa or manylinux) + optional port number (defaults to 2222). "
    echo "E.g. ./start_container.sh 36 2223"
    exit 1
}

if [ $# -eq 0 ] || [ $# -gt 2 ]; then
    usage
fi

if [ $# -eq 2 ]; then
    port=$2
fi

case "$1" in
    "36")
        version=$1
        shift
        ;;
    "38")
        version=$1
        shift
        ;;
    "medusa")
        version=$1
        shift
        ;;
    "manylinux")
        version=$1
        shift
        ;;
    *)
        usage
        shift
        ;;
esac

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source ${SCRIPT_DIR}/../../${version}.versions
image="$build_image"

# Test authorized_keys exists
if [ ! -f "$HOME/.ssh/authorized_keys" ]; then
    echo "ERROR: $HOME/.ssh/authorized_keys doesn't exist (or isn't readable)."
    echo "ERROR: Add your public key to .ssh/authorized_keys or else you won't be able to connect to the container!"
    exit 1
fi

if [ ! -f "$HOME/.gitconfig" ]; then
    echo "ERROR: $HOME/.gitconfig doesn't exist. Set up your Git client on your headnode first!"
    exit 1
fi

map_src=${SCRIPT_DIR}/../../

CMD="ln -s /tmp/.gitconfig /root/.gitconfig; ln -s /tmp/.ssh /root/.ssh; dropbear -R -F -E -p $port"

# Port 17815 used as default by remotery profiling tool
docker run \
    -v $map_src:/opt/arcticdb \
    -v $HOME/.ssh:/tmp/.ssh:ro \
    -v $HOME/.gitconfig:/tmp/.gitconfig \
    -v /apps/research/tools/mongo/3.4.13_el7:/opt/mongo \
    -v /apps/research/tools/:/apps/research/tools/:ro \
    -v /etc/ahl/mongo/instances.cfg:/etc/ahl/mongo/instances.cfg \
    -v /apps/research/tools/bin/withproxy:/usr/bin/withproxy \
    -v /apps/research/tools/git/git-lfs/2.3.4/git-lfs:/usr/bin/git-lfs \
    -v /scratch/data/vscode/:/scratch/data/vscode \
    -v /scratch/data/vcpkg_cache:/scratch/data/vcpkg_cache \
    -p 17815:17815 \
    -p "${port}:${port}" \
    -it \
    --privileged $image bash -c "$CMD"
