#!/bin/bash

set -euo pipefail

source /opt/bootstrap/cxx_profile.sh
source /opt/bootstrap/util.sh

# This only deals with dependencies for running interactive IDE clion from inside 
# the container.

yum install -y libXtst libXext libXrender libXtst xhost freetype fontconfig wget
yum clean all 

#https://download-cdn.jetbrains.com/cpp/CLion-2022.3.3.tar.gz

mkpushd /tmp/clion
    clion_version=2022.3.3
    pxy wget https://download.jetbrains.com/cpp/CLion-${clion_version}.tar.gz
    tar -xvf CLion-${clion_version}.tar.gz
    pushd clion-${clion_version}
        mkdir /opt/clion
        mv ./* /opt/clion
    popd
popd

rm -rf /tmp/clion
