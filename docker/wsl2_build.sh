#!/bin/bash

version=${1:-current}
ver_file=$version.versions

if uname -r | grep microsoft; then
  # Workaround Windows git's checkout of symlinks:
  [[ `wc -l $ver_file | cut -d' ' -f1` -gt 1 ]] || ver_file=`cat $ver_file`
else
  prefix=sudo
fi

. $ver_file

cp ../requirements.txt .

$prefix docker build . -f wsl2.Dockerfile \
    --build-arg IMGTAG="$build_image" \
    --build-arg LOCAL_USER_ID=$UID \
    --no-cache \
    -t arcticc-wsl2-$version

rm requirements.txt # TODO: trap
