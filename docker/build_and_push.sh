#!/bin/bash

set -e

./buildimg.sh not-local

tag=`/usr/bin/grep -oP ":\K[\w-]+" manylinuxman_tag.tmp`
sed -i "s/build_tag=.*/build_tag=${tag}/" manylinux.versions
rm manylinuxman_tag.tmp

# pull the releases image so it won't get collected
source manylinux.versions
docker pull "${build_image}"

