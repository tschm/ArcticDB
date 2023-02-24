#!/bin/bash

set -euo pipefail

mv /opt/bootstrap/cxx_profile.sh /etc/profile.d/

source /etc/profile.d/cxx_profile.sh

source /opt/bootstrap/util.sh

export PATH="/opt/gcc/8.2.0/bin:/opt/cmake/bin:$PATH"
alias cmake=/opt/cmake/bin/cmake

mkpushd /opt/deps
    mkpushd src

        #################### BOOST ##########################
        # Get and install boost from source
        pxy wget --quiet https://boostorg.jfrog.io/artifactory/main/release/1.69.0/source/boost_1_69_0.tar.bz2

        tar -xjvf boost_1_69_0.tar.bz2
        pushd  boost_1_69_0
            libraries="context,contract,date_time,exception,fiber,filesystem,graph,iostreams,locale,log,math,program_options,random,regex,serialization,stacktrace,system,test,thread,timer,type_erasure,wave"
            ./bootstrap.sh --prefix=/usr/local --with-libraries=${libraries} && ./b2 stage cxxflags=-fPIC cflags=-fPIC warnings=off threading=multi link=static -j $(nproc) && ./b2 install threading=multi link=static
       popdrm # boost_1_69_0

    popd #src

popd # /opt/deps
