#!/bin/bash

# Helper script to make it easier to build the various docker images for different pegasus versions

set -euo pipefail

mode=$1
version=$2
local_only=${3:-"local"}

[[ "${local_only}" == "local" ]] && echo "Local only build. Not going to push images"

function usage(){
    echo "buildimg.sh <mode> <version> where mode in {gcc,boost,deps,build}, version in {36,38,medusa}"
}

case $version in
"36")
    pegasus_version="3.6"
    pegasus_image="man-pegasus-current"
    image_prefix="pre-releases-docker.repo.prod.m/man/app/pegcxx"
  ;;
"38")
    pegasus_version="3.8"
    pegasus_image="man-pegasus-next"
    image_prefix="pre-releases-docker.repo.prod.m/man/app/pegcxx"
;;
"medusa")
    pegasus_version="36-1"
    pegasus_image="man-medusa-python"
    image_prefix="pre-releases-docker.repo.prod.m/man/app/36-1/medcxx-36-1"
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

echo "Versions $(cat ${version}.versions)"
source ${version}.versions

case $mode in
"gcc")
    echo "Creating gcc container"
    dockerfile="01-gcc.Dockerfile"
    sudo docker build . -f $dockerfile --build-arg PEG_VERSION=$pegasus_version --build-arg PEG_IMAGE=$pegasus_image -t arcticc-gcc-$version

    [[ "${local_only}" == "local" ]] && exit 0
    ts="$(date '+%s')"
    tag=$(tag_img gcc8.2 $ts $version)
    tag_latest=$(tag_img gcc8.2 latest $version)

    sudo docker tag arcticc-gcc-$version $tag
    sudo docker tag arcticc-gcc-$version $tag_latest
    sudo docker push $tag
    sudo docker push $tag_latest
    ;;
"boost")
    echo "Creating boost container"

    rm -f tls-ca-bundle.pem
    cp /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem .

    tag="arctic-boost-${version}"
    dockerfile="02-boost.Dockerfile"
    sudo docker build . -f $dockerfile --build-arg IMGTAG=$gcc_image -t arcticc-boost-$version

    [[ "${local_only}" == "local" ]] && exit 0

    ts="$(date '+%s')"
    tag=$(tag_img boost $ts $version)
    tag_latest=$(tag_img boost latest $version)

    sudo docker tag arcticc-boost-$version $tag
    sudo docker tag arcticc-boost-$version $tag_latest
    sudo docker push $tag
    sudo docker push $tag_latest
    ;;
"deps")
    echo "Creating deps container"
    tag="arctic-deps-${version}"
    dockerfile="03-deps.Dockerfile"
    sudo docker build . -f $dockerfile --build-arg IMGTAG="$boost_image" -t arcticc-deps-$version

    [[ "${local_only}" == "local" ]] && exit 0

    ts="$(date '+%s')"
    tag=$(tag_img deps $ts $version)
    tag_latest=$(tag_img deps latest $version)

    sudo docker tag arcticc-deps-$version $tag
    sudo docker tag arcticc-deps-$version $tag_latest
    sudo docker push $tag
    sudo docker push $tag_latest
    ;;
"build")
    echo "Creating build container"
    dockerfile="04-build.Dockerfile"
    sudo docker build . -f $dockerfile --build-arg IMGTAG="$deps_image" -t arcticc-build-$version

    [[ "${local_only}" == "local" ]] && exit 0

    ts="$(date '+%s')"
    tag=$(tag_img build $ts $version)
    tag_latest=$(tag_img build latest $version)

    sudo docker tag arcticc-build-$version $tag
    sudo docker tag arcticc-build-$version $tag_latest
    sudo docker push $tag
    sudo docker push $tag_latest
    ;;
"external")
    echo "Creating external container"
    dockerfile="05-external.Dockerfile"
    cp /apps/research/tools/bin/withproxy .
    sudo docker build . -f $dockerfile --build-arg IMGTAG="$build_image" -t arcticc-external

    [[ "${local_only}" == "local" ]] && exit 0

    ts="$(date '+%s')"
    tag=$(tag_img external $ts none)
    tag_latest=$(tag_img external latest none)

    echo $tag
    echo $tag_latest
    sudo docker tag arcticc-external $tag
    sudo docker tag arcticc-external $tag_latest
    sudo docker push $tag
    sudo docker push $tag_latest
    ;;
*)
    usage
    exit 1
esac

