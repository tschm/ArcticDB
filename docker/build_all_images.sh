#!/bin/bash

# build the build containers
./buildimg.sh build 36 not-local
./buildimg.sh external 36 not-local from_latest

./buildimg.sh build 38 not-local

./buildimg.sh build medusa not-local
./buildimg.sh external medusa not-local from_latest

# retag in to .new files
cp 36.versions 36.versions.new
tag=`/usr/bin/grep -oP ":\K[\w-]+" build_tag.36.tmp`
sed -i "s/build_tag=.*/build_tag=${tag}/" 36.versions.new

tag=`cut -c 5- external_tag.36.tmp`
sed -i "s~external_image=.*~external_image=${tag}~" 36.versions.new

cp 38.versions 38.versions.new
tag=`/usr/bin/grep -oP ":\K[\w-]+" build_tag.38.tmp`
sed -i "s/build_tag=.*/build_tag=${tag}/" 38.versions.new

# no external image build from the peg-38 base

cp medusa.versions medusa.versions.new
tag=`/usr/bin/grep -oP ":\K[\w-]+" build_tag.medusa.tmp`
sed -i "s/build_tag=.*/build_tag=${tag}/" medusa.versions.new

tag=`cut -c 5- external_tag.medusa.tmp`
sed -i "s~external_image=.*~external_image=${tag}~" medusa.versions.new

# pull the pre-releases images so that they are available from releases
find . -name "*_tag.*.tmp" | while read -r tag_file ; do
    sudo docker pull `cat $tag_file`
    rm $tag_file
done

# Show diffs visually
find . -name "*.versions" | while read -r versions_file ; do
    git --no-pager diff --no-index $versions_file $versions_file.new
done
