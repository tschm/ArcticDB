#!/bin/bash

set -euo pipefail

version=36
port=2222

usage () {
    echo "USAGE: Pass version (36, 38 or medusa) + optional port number (defaults to 2222). "
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
    *)
        usage
        shift
        ;;
esac

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source ${SCRIPT_DIR}/../${version}.versions
if [ "${1:-}" == "external" ]; then
    image="$external_image"
    shift
else
    image="$external_image"
fi

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

USER_ID=$(id -u)
GROUP_ID=$(id -g)

echo "Starting with UID : $USER_ID, GID: $GROUP_ID"

ROOT_CMD="groupadd -g $GROUP_ID thegroup; \
        useradd --shell /bin/bash -u $USER_ID -g thegroup -o -c "" -m user; \
        ln -s /opt/arcticc/docker/vscode/.curlrc ~/.curlrc; \
        ln -s /opt/arcticc/docker/vscode/.wgetrc ~/.wgetrc; \
        yum install -y dropbear wget openssl-devel cyrus-sasl-devel devtoolset-10-libatomic-devel libcurl-devel python3-devel scl-utils; \
        cd /tmp; \
        yum remove git; \
        wget "http://packages.endpointdev.com/rhel/7/os/x86_64/git-2.23.0-1.ep7.x86_64.rpm" \
        wget "http://packages.endpointdev.com/rhel/7/os/x86_64/git-core-doc-2.23.0-1.ep7.noarch.rpm" \
        wget "http://packages.endpointdev.com/rhel/7/os/x86_64/perl-Git-2.23.0-1.ep7.noarch.rpm" \
        wget "http://packages.endpointdev.com/rhel/7/os/x86_64/git-core-doc-2.23.0-1.ep7.noarch.rpm" \
        yum install git-core-doc-2.23.0-1.ep7.noarch.rpm perl-Git-2.23.0-1.ep7.noarch.rpm git-core-doc-2.23.0-1.ep7.noarch.rpm git-2.23.0-1.ep7.x86_64.rpm \
        wget "http://mirror.centos.org/centos/7/sclo/x86_64/rh/Packages/d/devtoolset-10-libatomic-devel-10.2.1-11.1.el7.x86_64.rpm"; \
        yum install devtoolset-10-libatomic-devel-10.2.1-11.1.el7.x86_64.rpm; \
        chmod 777 /etc/dropbear"

USER_CMD="ln -s /tmp/.gitconfig /home/user/.gitconfig; \
        ln -s /tmp/.ssh /home/user/.ssh; \
        ln -s /opt/arcticc/docker/vscode/.curlrc /home/user/.curlrc; \
        ln -s /opt/arcticc/docker/vscode/.wgetrc /home/user/.wgetrc; \
        dropbear -w -g -R -F -E -p $port"

# Port 17815 used as default by remotery profiling tool
# sudo docker run -e LOCAL_USER_ID=$(id -u $USER) \
#     -u $(id -u):$(id -g) \
#     -v $map_src:/opt/man.arctic \
#     -v $HOME/.ssh:/tmp/.ssh:ro \
#     -v $HOME/.gitconfig:/tmp/.gitconfig \
#     -v ${SCRIPT_DIR}/.curlrc:/tmp/.curlrc \
#     -v /apps/research/tools/mongo/3.4.13_el7:/opt/mongo \
#     -v /apps/research/tools/:/apps/research/tools/:ro \
#     -v /etc/ahl/mongo/instances.cfg:/etc/ahl/mongo/instances.cfg \
#     -v /apps/research/tools/bin/withproxy:/usr/bin/withproxy \
#     -v /apps/research/tools/git/git-lfs/2.3.4/git-lfs:/usr/bin/git-lfs \
#     -v /scratch/data/vscode/:/scratch/data/vscode \
#     -p 17815:17815 \
#     -p "${port}:${port}" \
#     --entrypoint=/bin/bash \
#     --privileged $image bash -c "$CMD"


# --user 3004873:11626 \
# --privileged $image bash -c "$CMD"


# Port 17815 used as default by remotery profiling tool
DOCKER_ID="$(sudo docker run -dit \
    -v $map_src:/opt/arcticc \
    -v $HOME/.ssh:/tmp/.ssh:ro \
    -v $HOME/.gitconfig:/tmp/.gitconfig \
    -v /apps/research/tools/mongo/3.4.13_el7:/opt/mongo \
    -v /apps/research/tools/:/apps/research/tools/:ro \
    -v /etc/ahl/mongo/instances.cfg:/etc/ahl/mongo/instances.cfg \
    -v /apps/research/tools/bin/withproxy:/usr/bin/withproxy \
    -v /apps/research/tools/git/git-lfs/2.3.4/git-lfs:/usr/bin/git-lfs \
    -v /scratch/data/vscode/:/scratch/data/vscode \
    -p 17815:17815 \
    -p "${port}:${port}" \
    --privileged $image bash)"
sudo docker container exec -it ${DOCKER_ID} bash -c "$ROOT_CMD"
sudo docker container exec -u user -it ${DOCKER_ID} bash -c "$USER_CMD"