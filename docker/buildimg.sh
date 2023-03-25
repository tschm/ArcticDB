#!/bin/bash

# Helper script to make it easier to build the various docker images for different pegasus versions

set -euo pipefail

mode=$1
version=$2
local_only=${3:-"local"}
from_latest=${4:-""}

[[ "${local_only}" == "local" ]] && echo "Local only build. Not going to push images"

function usage(){
    echo "buildimg.sh <mode> <version> where mode in {build,external}, version in {36,38,medusa}"
}

case $version in
"36")
    pegasus_version="3.6"
    pegasus_image="man-pegasus-current"
    image_prefix="pre-releases-docker.repo.prod.m/man/app/pegcxx"
    dockerfile="Dockerfile"
  ;;
"38")
    pegasus_version="3.8"
    pegasus_image="man-pegasus-next"
    image_prefix="pre-releases-docker.repo.prod.m/man/app/pegcxx"
    dockerfile="Dockerfile"
;;
"medusa")
    pegasus_version="36-1"
    pegasus_image="man-medusa-python"
    image_prefix="pre-releases-docker.repo.prod.m/man/app/36-1/medcxx-36-1"
    dockerfile="Dockerfile"
;;
"manylinux")
;;
*)
    usage
    exit 1
  ;;
esac
echo "Pegasus version $version"

function tag_img(){
    local component=$1
    local suffix=$2
    local pegasus=$3
    local prefix=${4:-$image_prefix}
    if [[ "$pegasus" =~ .*medusa.* ]]; then
      echo "$prefix:$component-${suffix}"
    else
      echo "$prefix-$pegasus:$component-${suffix}"
    fi
}

case $mode in
"build")
    echo "Creating build container"

    rm -f tls-ca-bundle.pem
    cp /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem .

    docker build . -f $dockerfile --build-arg PEG_VERSION=$pegasus_version --build-arg PEG_IMAGE=$pegasus_image -t arcticc-build-$version

    [[ "${local_only}" == "local" ]] && exit 0

    ts="$(date '+%s')"
    tag=$(tag_img build $ts $version)
    tag_latest=$(tag_img build latest $version)

    echo $tag | tee build_tag.$version.tmp
    docker tag arcticc-build-$version $tag
    docker tag arcticc-build-$version $tag_latest
    docker push $tag
    docker push $tag_latest
    ;;
"external")
    echo "Creating external container"

    source ${version}.versions
    if [[ "${from_latest}" == "from_latest" ]]; then
      build_image=$(tag_img build latest $version)
    fi
    echo "build_image=${build_image}"

    dockerfile="external.Dockerfile"
    cp /apps/research/tools/bin/withproxy .
    docker build . -f $dockerfile --build-arg IMGTAG="$build_image" -t arcticc-external

    [[ "${local_only}" == "local" ]] && exit 0

    ts="$(date '+%s')"
    tag=$(tag_img external $ts none)
    tag_latest=$(tag_img external latest none)

    echo $tag | tee external_tag.$version.tmp
    echo $tag_latest
    docker tag arcticc-external $tag
    docker tag arcticc-external $tag_latest
    docker push $tag
    docker push $tag_latest
    ;;
"manylinux")
    echo "Creating manylinux build container"

    source ${version}.versions
    dockerfile="manylinux.Dockerfile"

    cp /apps/research/tools/bin/withproxy .
    docker build . -f $dockerfile --build-arg IMGTAG="$base_image"
    ;;
*)
    usage
    exit 1
esac
