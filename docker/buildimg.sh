#!/bin/bash

# Helper script to make it easier to build and publish the dev container

set -euo pipefail

local_only=${1:-"local"}

[[ "${local_only}" == "local" ]] && echo "Local only build. Not going to push images"

function tag_img(){
    local suffix=$1
    echo "$img_prefix:${suffix}"
}

echo "Creating manylinux Man build container"

source manylinux.versions
dockerfile="manylinux.Dockerfile"

cp /apps/research/tools/bin/withproxy .
mkdir -p certificate_authorities
cp /usr/local/share/ca-certificates/man/* certificate_authorities
requirements=$(grep -Po "  .*" ../arcticdb_link/setup.cfg | grep -v '#' | grep -v ':' | awk '{ print $1 }' | tr '\n' ' ')
docker build . -f $dockerfile --build-arg IMGTAG="$github_base_image" --build-arg REQUIREMENTS="$requirements" -t arcticdb-manylinuxman

rm -rf certificate_authorities withproxy

ts="$(date '+%s')"
tag=`echo "${img_prefix}:${ts}" | sed 's/releases-/pre-releases-/'`

echo $tag | tee manylinuxman_tag.tmp
docker tag arcticdb-manylinuxman $tag

[[ "${local_only}" == "local" ]] && exit 0

docker push $tag

