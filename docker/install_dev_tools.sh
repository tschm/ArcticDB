#!/bin/bash

set -euo pipefail

source /etc/profile.d/cxx_profile.sh
source /opt/bootstrap/util.sh

# This only deals with dependencies for running interactive IDE clion from inside 
# the container.

yum install -y libXtst oracle-jdk-8u131-1.8.0_131-1.ahl libXext libXrender libXtst xhost freetype fontconfig
yum clean all 

#https://download.jetbrains.com/cpp/CLion-183.3283.6.tar.gz

mkpushd /tmp/clion
    clion_version=2021.2
    pxy wget --quiet https://download.jetbrains.com/cpp/CLion-${clion_version}.tar.gz
    tar -xvf CLion-${clion_version}.tar.gz
    pushd clion-${clion_version}
        mkdir /opt/clion
        mv ./* /opt/clion
    popd
popd

