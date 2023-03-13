#!/bin/bash

set -euo pipefail

version=36
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
esac

map_src=${PWD}

source docker/${version}.versions

if [ "${1:-}" == "external" ]; then
    image="$external_image"
    shift
else
    image="$build_image"
fi

echo "Running $image"

# Activate interactive mode in tty only
if [[ $- == *i* ]] || [[ "${INTERACTIVE:-0}" == "1" ]]
then 
if [ -z ${NO_X11+x} ];
then 
    xhost +
    interactive_args="-e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix --privileged"
else
    interactive_args=""
fi

jbprefix="${JETBRAINS_LOCAL:-$HOME/.jetbrains_local}"
jblocal="$jbprefix/`basename ${map_src}`"
if [[ ! -d "$jblocal" ]]; then
    mkdir -p "$jblocal/cache";
    mkdir -p "$jblocal/config";
    chmod -R 777 "$jblocal";
fi

if [ -z ${ARCTIC_DEV_SSH_PORT:-} ];
then 
    interactive="-it"
  else
    interactive="-it \
    -v $HOME/.dropbear:/etc/dropbear:rw \
    -v $HOME/.ssh/authorized_keys:/tmp/authorized_keys:ro \
    -v $jblocal:/tmp/clion_remote:rw \
    -p ${ARCTIC_DEV_SSH_PORT}:${ARCTIC_DEV_SSH_PORT}"
fi

# this is used for X11 forwarding inside the container using unix socket sharing
else
interactive="--rm"
interactive_args=""
fi

if [[ ! -v DEBUG_BUILD ]]; then
    env_vars=""
else
    env_vars="-e DEBUG_BUILD=$DEBUG_BUILD"
fi

if [[ ! -v USE_SLAB_ALLOCATOR ]]; then
    env_vars="$env_vars"
else
    env_vars="-e USE_SLAB_ALLOCATOR=$USE_SLAB_ALLOCATOR $env_vars"
fi

if [[ ! -v CMAKE_BUILD_TYPE ]]; then
    env_vars="$env_vars"
else
    env_vars="-e CMAKE_BUILD_TYPE=$CMAKE_BUILD_TYPE $env_vars"
fi

echo "$env_vars"
echo "$interactive"

IN_MB=${MB_SETUP_PY:-}
if [[ -z ${IN_MB} ]]; then
  sudo docker run -e LOCAL_USER_ID=$(id -u $USER) $interactive_args $env_vars -v $map_src:/opt/arcticdb \
      -v /apps/research/tools/mongo/3.4.13_el7:/opt/mongo \
      -v /apps/research/tools/:/apps/research/tools/:ro \
      --privileged $interactive $image "$@"
else
  echo -n '$MB_SETUP_PY environment variable is set so assuming we are running via man.build - and so already inside '
  echo 'Arctic docker container. As a result we will not attempt to relaunch the docker container...'

  for s in $env_vars
  do
    if [[ "$s" != "-e" ]]; then
      export ${s}
    fi
  done

  exec "$@"
fi

