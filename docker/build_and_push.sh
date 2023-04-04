#!/bin/bash

set -e

./buildimg.sh not-local

# retag in to .new files
cp manylinux.versions manylinux.versions.new
tag=`/usr/bin/grep -oP ":\K[\w-]+" manylinuxman_tag.tmp`
sed -i "s/build_tag=.*/build_tag=${tag}/" manylinux.versions.new

# pull the pre-releases image so it is available from releases
docker pull `cat manylinuxman_tag.tmp`
rm manylinuxman_tag.tmp

# Show diff visually
git --no-pager diff --no-index manylinux.versions manylinux.versions.new

