#!/bin/bash

set -euo pipefail

version=36
docker_command="sudo docker"
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
        docker_command="docker"
        shift
        ;;
esac

map_src=${PWD}

source docker/${version}.versions

image="$build_image"
echo "Running $image"

# Activate interactive mode in tty only
env_vars=""
interactive="--rm"
interactive_args=""
if [[ $- == *i* ]] || [[ "${INTERACTIVE:-0}" == "1" ]]
then 
    if [ -z ${NO_X11+x} ];
    then 
        xhost +
        interactive_args="-e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix --privileged"
    else
        interactive_args=""
    fi
    if [ "$version" == "manylinux" ]; then
        interactive_args="$interactive_args -v /apps/research/tools/etc/gitconfig:/usr/local/etc/gitconfig"
        interactive_args="$interactive_args -v ${HOME}/.gitconfig:/root/.gitconfig"
        interactive_args="$interactive_args -v ${HOME}/.ssh:/root/.ssh"
        interactive_args="$interactive_args -v ${HOME}/.cache/JetBrains:/root/.cache/JetBrains"
        interactive_args="$interactive_args -v ${HOME}/.config/JetBrains:/root/.config/JetBrains"
        interactive_args="$interactive_args -v ${HOME}/.local/share/JetBrains:/root/.local/share/JetBrains"
        interactive_args="$interactive_args -v ${HOME}/.ideavimrc:/root/.ideavimrc"
        interactive_args="$interactive_args -v ${HOME}/.arcticdbzshrc:/root/.zshrc"
        interactive_args="$interactive_args -v ${HOME}/.arcticdbvimrc:/root/.vimrc"
        interactive_args="$interactive_args -v /run/user/$(id -u)/.vault-token:/root/.vault-token"
        interactive_args="$interactive_args -v /etc/ahl/mongo/instances.cfg:/etc/ahl/mongo/instances.cfg"
        interactive_args="$interactive_args -v /scratch/data/vcpkg_cache:/scratch/data/vcpkg_cache"
        env_vars="$env_vars -e VAULT_ADDR=https://vault.gb.prod.m"
    fi
    interactive="-it"
fi

if [[ -v DEBUG_BUILD ]]; then
    env_vars="-e DEBUG_BUILD=$DEBUG_BUILD"
fi

if [[ -v USE_SLAB_ALLOCATOR ]]; then
    env_vars="-e USE_SLAB_ALLOCATOR=$USE_SLAB_ALLOCATOR $env_vars"
fi

if [[ -v CMAKE_BUILD_TYPE ]]; then
    env_vars="-e CMAKE_BUILD_TYPE=$CMAKE_BUILD_TYPE $env_vars"
fi

IN_MB=${MB_SETUP_PY:-}
if [[ -z ${IN_MB} ]]; then
  ${docker_command} run -e LOCAL_USER_ID=$(id -u $USER) $interactive_args $env_vars \
      -v $map_src:/opt/arcticdb \
      -v /apps/research/tools/mongo/3.4.13_el7:/opt/mongo \
      -v /apps/research/tools/:/apps/research/tools/:ro \
      -v /scratch/data/vcpkg_cache:/scratch/data/vcpkg_cache \
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

