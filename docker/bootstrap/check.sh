#!/bin/bash

source /etc/profile.d/cxx_profile.sh
source /opt/bootstrap/util.sh


################ CHECK BOOTSTRAPPING ##################
## Actually build and run checks to assert the presence of the things allegedly installed

mkpushd /tmp/boostrap_build_boost
pxy cmake /opt/bootstrap && make -j $(nproc)
boost-check/bootstrap
gtest-check/unit_tests
popd # /tmp/boostrap_build

