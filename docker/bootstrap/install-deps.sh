#!/bin/bash

set -euxo pipefail

mv /opt/bootstrap/cxx_profile.sh /etc/profile.d/

source /etc/profile.d/cxx_profile.sh

source /opt/bootstrap/util.sh

export PATH="/opt/gcc/8.2.0/bin:/opt/cmake/bin:$PATH"
alias cmake=/opt/cmake/bin/cmake

pushd /opt/deps
    pushd src
        #################### ZLIB ###############################
        pxy wget --quiet https://github.com/madler/zlib/archive/v1.2.13.tar.gz
        tar xvf v1.2.13.tar.gz
        pushd zlib-1.2.13
             ./configure  CXXFLAGS=-fPIC --static && make -j $(nproc) && make install
        popdrm #zlib-1.2.13

        #################### JEMALLOC ##########################
        pxy wget --quiet https://github.com/jemalloc/jemalloc/releases/download/5.1.0/jemalloc-5.1.0.tar.bz2

        tar xjvf jemalloc-5.1.0.tar.bz2
        pushd jemalloc-5.1.0
            ./configure
            make -j $(nproc) build_lib_static && make install_lib_static
        popdrm # jemalloc-5.1.00

        #################### LZ4 ##########################
        pxy wget --quiet https://github.com/lz4/lz4/archive/v1.8.3.tar.gz

        tar xvf v1.8.3.tar.gz
        pushd lz4-1.8.3
            CPPFLAGS=-fPIC make -j $(nproc) && make install
        popdrm # lz4-1.8.3
        find /usr/local -name liblz4*.so* -delete # no dynamic linking

        #################### ZSTD ##########################
        pxy wget --quiet https://github.com/facebook/zstd/archive/v1.4.5.tar.gz

        tar xvf v1.4.5.tar.gz
        mkpushd /tmp/zstd_build
            cmake ${MY_CMAKE_ARGS} -DZSTD_BUILD_SHARED=OFF /opt/deps/src/zstd-1.4.5/build/cmake/
            CPPFLAGS=-fPIC make -j $(nproc) && make install
        popdrm # zstd-1.4.5

        ################### OpenSSL ########################
        pxy wget --quiet https://www.openssl.org/source/old/1.1.1/openssl-1.1.1l.tar.gz
        tar xvf openssl-1.1.1l.tar.gz
        pushd openssl-1.1.1l
        ./config no-shared no-dso --prefix=/usr/local/ -fPIC && make -j $(nproc) && make install
        popdrm #openssl-1.1.1l

        ################### Libcurl ########################
        pxy wget --quiet https://github.com/curl/curl/releases/download/curl-7_62_0/curl-7.62.0.tar.gz
        tar xvf curl-7.62.0.tar.gz
        pushd curl-7.62.0
        CFLAGS="-fPIC" ./configure --with-ssl && make -j $(nproc) && make install
        popdrm #curl-7.62.0.tar.gz

        ################### ProtoBuf #######################
        pxy wget --quiet https://github.com/google/protobuf/releases/download/v3.6.1/protobuf-cpp-3.6.1.tar.gz
        tar xvf protobuf-cpp-3.6.1.tar.gz
        pushd protobuf-3.6.1
        ./configure CXXFLAGS=-fPIC --prefix=/usr/local --disable-shared && make -j $(nproc) && make install
        popdrm #protobuf-3.6.1

        ################### xxHash #######################
        pxy wget --quiet https://github.com/Cyan4973/xxHash/archive/v0.6.5.tar.gz
        tar xvf v0.6.5.tar.gz
        pushd xxHash-0.6.5
        CPPFLAGS=-fPIC make && rm -f libxxhash.so* && make install
        popdrm #xxHash-0.6.5

        ################### libpcre #######################
        pxy wget --quiet https://netcologne.dl.sourceforge.net/project/pcre/pcre/8.45/pcre-8.45.tar.gz
        tar xvf pcre-8.45.tar.gz
        pushd pcre-8.45
        mkdir install
        CFLAGS=-fPIC LDFLAGS=-fPIC ./configure && CFLAGS=-fPIC LDFLAGS=-fPIC make && make install
        popdrm #pcre-8.45.tar.gz

        #################### CYRUS SASL ###############################
        pxy wget --quiet https://github.com/cyrusimap/cyrus-sasl/releases/download/cyrus-sasl-2.1.28/cyrus-sasl-2.1.28.tar.gz
        tar xvf cyrus-sasl-2.1.28.tar.gz
        pushd cyrus-sasl-2.1.28
            CFLAGS=-fPIC ./configure --enable-static --disable-shared && CFLAGS=-fPIC LDFLAGS=-fPIC make -j $(nproc) && make install
        popdrm #cyrus sasl

        #################### libsodium ################################
        pxy wget --quiet https://download.libsodium.org/libsodium/releases/libsodium-1.0.17.tar.gz
        tar xvf libsodium-1.0.17.tar.gz
        pushd libsodium-1.0.17
        CFLAGS=-fPIC LDFLAGS=-fPIC ./configure --prefix=/usr/local  --disable-pie
        CFLAGS=-fPIC LDFLAGS=-fPIC make && make install
        popdrm #libsodium
    popd #src

    mkdir git

popd # /opt/deps

clone_depth_1 https://github.com/libevent libevent release-2.1.12-stable
mkpushd /tmp/libevent_build
    LIBEVENT_ARGS="-DEVENT__LIBRARY_TYPE=STATIC"
    cmake ${MY_CMAKE_ARGS} ${LIBEVENT_ARGS} /opt/deps/git/libevent && make -j $(nproc) && make install
popd # /tmp/libevent_build

#################### standard with clone cmake make install  ##########################
clone_make_install https://github.com/google googletest release-1.12.1
clone_make_install https://github.com/google double-conversion v3.1.4
clone_make_install https://github.com/google glog v0.3.5
clone_make_install https://github.com/gflags gflags v2.2.2
clone_make_install https://github.com/fmtlib fmt 8.1.1

#################### Folly ##########################

# See https://github.com/facebook/folly/tree/v2022.10.31.00/build/fbcode_builder/manifests for
# Folly's own dependencies. Make sure that those above are compatible with the versions in the Folly
# manifests if upgrading versions.

clone_depth_1 https://github.com/facebook folly v2022.10.31.00
pushd /opt/deps/git/folly
    # Fix some gcc8.2 errors
    echo 'SET( CMAKE_CXX_FLAGS  "${CMAKE_CXX_FLAGS} -Wno-error=class-memaccess")' >> CMakeLists.txt
popd # /opt/deps/git/folly

mkpushd /tmp/folly_build
    # No exeception tracer as we link statically to libstdc++ see
    # https://github.com/facebook/folly/issues/1623
    # https://github.com/facebook/folly/commit/41a25b79899a7162484ddcd3ff0097f8d9f63aa1
    FOLLY_ARGS="-DFOLLY_NO_EXCEPTION_TRACER=ON"
    cmake ${MY_CMAKE_ARGS} ${FOLLY_ARGS} /opt/deps/git/folly && make -j $(nproc) && make install
popd # /tmp/folly_build


################### Mongo ##############################
## C driver

clone_depth_1 https://github.com/mongodb mongo-c-driver 1.12.0
mkpushd /tmp/mongo-c-driver_build
    # disable zlib since mongo will try to link but zlib.a is not compiled with fPIC. Not necessary for us since we only care about .a being produced
    MONGOC_ARGS="-DENABLE_STATIC=ON -DENABLE_ZLIB=OFF -DENABLE_AUTOMATIC_INIT_AND_CLEANUP=OFF"
    cmake ${MY_CMAKE_ARGS} ${MONGOC_ARGS} /opt/deps/git/mongo-c-driver && make -j $(nproc) && make install
popd # /tmp/mongo-c-driver_build

## Cxx driver
clone_depth_1 https://github.com/mongodb mongo-cxx-driver r3.3.1
mkpushd /tmp/mongo-cxx-driver
    MONGOCXX_ARGS="-DCMAKE_INSTALL_PREFIX=/usr/local -DBUILD_SHARED_LIBS=OFF"
    pxy cmake ${MY_CMAKE_ARGS} $MONGOCXX_ARGS /opt/deps/git/mongo-cxx-driver && pxy make -j $(nproc) && make install
popd # /tmp/mongo-c-driver_build

pushd /tmp/mongo-c-driver_build
    # disable zlib since mongo will try to link but zlib.a is not compiled with fPIC. Not necessary for us since we only care about .a being produced
    MONGOC_ARGS="-DENABLE_STATIC=OFF -DENABLE_ZLIB=OFF -DENABLE_AUTOMATIC_INIT_AND_CLEANUP=OFF"
    cmake ${MY_CMAKE_ARGS} ${MONGOC_ARGS} /opt/deps/git/mongo-c-driver && make -j $(nproc) && make install
popd # /tmp/mongo-c-driver_build

## Cxx driver
pushd /tmp/mongo-cxx-driver
    MONGOCXX_ARGS="-DCMAKE_INSTALL_PREFIX=/usr/local -DBUILD_SHARED_LIBS=ON"
    pxy cmake ${MY_CMAKE_ARGS} $MONGOCXX_ARGS /opt/deps/git/mongo-cxx-driver && pxy make -j $(nproc) && make install
popd # /tmp/mongo-c-driver_build

################### Amazon S3 ##############################
export LD_LIBRARY_PATH=/opt/gcc/8.2.0/lib64
clone_depth_submodules_1 https://github.com/aws aws-sdk-cpp 1.9.212

pushd /opt/deps/git/aws-sdk-cpp/crt/aws-crt-cpp/crt/s2n/
git fetch origin main
git merge 69b749ffa5f92cf6517ce653c2b830de6e669227
popd

sed -i "/case '$':/d" /opt/deps/git/aws-sdk-cpp/aws-cpp-sdk-core/source/http/URI.cpp
sed -i "/case ':':/d" /opt/deps/git/aws-sdk-cpp/aws-cpp-sdk-core/source/http/URI.cpp
rm /opt/deps/git/aws-sdk-cpp/aws-cpp-sdk-core-tests/http/URITest.cpp

mkpushd /tmp/aws-sdk-cpp
    AWS_S3_ARGS="-D BUILD_ONLY=s3 -D BUILD_SHARED_LIBS=OFF -D CPP_STANDARD=17 -D OPENSSL_INCLUDE_DIR=/usr/local/include/openssl -D OPENSSL_SSL_LIBRARY=/usr/local/lib64/libssl.a -D OPENSSL_CRYPTO_LIBRARY=/usr/local/lib64/libcrypto.a -D CURL_LIB_DIR=/usr/local/share/curl -D CURL_INCLUDE_DIR=/usr/local/include/curl"
    pxy cmake ${MY_CMAKE_ARGS} $AWS_S3_ARGS /opt/deps/git/aws-sdk-cpp && pxy make -j $(nproc) && make install
popd # /tmp/aws-sdk-cpp


#################### Prometheus ##########################

# clone_depth_1 https://github.com/jupp0r prometheus-cpp v0.12.3

# We are sticked to a particular SHA from master branch because the latest release version of Prometheus is not
# containing yet the reset() function for Histograms. It will be updated again to the original 
# way when the new version will be released
pxy git clone https://github.com/jupp0r/prometheus-cpp.git --branch master /opt/deps/git/prometheus-cpp
pushd /opt/deps/git/prometheus-cpp
    git checkout 99e4d5085e4557fc9f3bea8db0c69bb1727c3d56
    git submodule init
    pxy git submodule update
popd # /opt/deps/git/prometheus-cpp

mkpushd /tmp/prometheus-cpp_build
    cmake ${MY_CMAKE_ARGS} -DUSE_THIRDPARTY_LIBRARIES=ON -DENABLE_TESTING=OFF /opt/deps/git/prometheus-cpp && make -j $(nproc) && make install
popd # /tmp/prometheus-cpp_build


#################### BitMagic ##########################

clone_depth_1 https://github.com/tlk00 BitMagic v7.2.0

mkpushd /tmp/bitmagic_build/
    mkdir /usr/local/include/bitmagic/
    cp /opt/deps/git/BitMagic/src/* /usr/local/include/bitmagic/
    cp /tmp/custom_cmakefiles/BitMagic_CmakeLists.txt /opt/deps/git/BitMagic/CmakeLists.txt
    cmake /opt/deps/git/BitMagic/
popd #  /tmp/bitmagic_build/

#################### Fizz   ##########################
# Required dep of Wangle
clone_depth_1 https://github.com/facebookincubator fizz v2022.10.31.00
mkpushd /tmp/fizz_build/
    cmake /opt/deps/git/fizz/fizz
    make -j 10
    make install
popd # /tmp/fizz_build

#################### Wangle ##########################
clone_depth_1 https://github.com/facebook wangle v2022.10.31.00
mkpushd /tmp/wangle_build/
    sed -i 's/find_package(Glog REQUIRED)/find_package(GLog REQUIRED)/g' /opt/deps/git/wangle/wangle/CMakeLists.txt
    cmake /opt/deps/git/wangle/wangle
    make -j 10
    make install
popd #  /tmp/wangle_build/

#################### librdkafka  ##########################
clone_depth_1 https://github.com/edenhill librdkafka v1.5.2
pushd /opt/deps/git/librdkafka
    ./configure --enable-ssl --enable-gssapi
    make -j 10
    make install
    # Just remove all .so files for rdkafka, make Cmake link to the static lib.
    rm -rf /usr/local/lib/librdkafka*.so*
popd  # /opt/deps/git/librdkafka

rm -rf /tmp/*_build/ /tmp/mongo-cxx-driver
rm -rf /opt/deps
