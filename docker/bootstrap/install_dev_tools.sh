#!/bin/bash

set -euo pipefail

source /opt/bootstrap/cxx_profile.sh

# This only deals with dependencies for running interactive IDE clion from inside 
# the container.

/opt/bootstrap/withproxy yum install -y libXtst libXext libXrender libXtst xhost freetype fontconfig wget valgrind vim less zsh xclip libasan libtsan libubsan
yum clean all

#  We put CLION in Artifactory as downloading it through the firewall is so slow.
#  To refresh it, just download it from Jetbrains and upload it in the artifactory UI
#  http://artifactory.svc.prod.ahl/ui/repos/tree/General/  "Deploy" button to the "data" repository
#  to a target path like the below, with version number updated.

pushd /opt
    clion_version=2023.1
    wget http://artifactory.svc.prod.ahl:80/artifactory/data/jetbrains/clion/clion-${clion_version}.gz
    tar -xf clion-${clion_version}.gz
    rm clion-${clion_version}.gz
popd

