#!/bin/bash

set -euo pipefail

source /opt/bootstrap/cxx_profile.sh

# This only deals with dependencies for running interactive IDE clion from inside 
# the container.

yum install -y libXtst libXext libXrender libXtst xhost freetype fontconfig wget valgrind vim less zsh xclip
yum clean all

#https://download.jetbrains.com/cpp/CLion-2023.1.tar.gz

pushd /opt
    clion_version=2023.1
    curl -L https://download.jetbrains.com/cpp/CLion-${clion_version}.tar.gz -o clion.tgz
    tar -xzf clion.tgz
    rm clion.tgz
    mv clion-${clion_version} clion
popd

echo "alias clion='/opt/clion/bin/clion.sh > /dev/null 2>&1'" >> /root/.bashrc
