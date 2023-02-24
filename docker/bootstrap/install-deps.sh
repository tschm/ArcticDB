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
        pxy wget --quiet https://github.com/madler/zlib/archive/v1.2.11.tar.gz
        tar xvf v1.2.11.tar.gz
        pushd zlib-1.2.11
             ./configure  CXXFLAGS=-fPIC --static && make -j $(nproc) && make install
        popdrm #zlib-1.2.11

        #################### JEMALLOC ##########################
        pxy wget --quiet https://github.com/jemalloc/jemalloc/releases/download/5.1.0/jemalloc-5.1.0.tar.bz2

        tar xjvf jemalloc-5.1.0.tar.bz2
        pushd jemalloc-5.1.0
            ./configure
            make -j $(nproc) build_lib_static && make install_lib_static
        popdrm # jemalloc-5.1.00

        #################### LZ4 ##########################
        pxy wget --quiet https://github.com/lz4/lz4/archive/v1.8.2.tar.gz

        tar xvf v1.8.2.tar.gz
        pushd lz4-1.8.2
            CPPFLAGS=-fPIC make -j $(nproc) && make install
        popdrm # lz4-1.8.2
        find /usr/local -name liblz4*.so* -delete # no dynamic linking

        #################### ZSTD ##########################
        pxy wget --quiet https://github.com/facebook/zstd/archive/v1.3.5.tar.gz

        tar xvf v1.3.5.tar.gz
        pushd zstd-1.3.5
            CPPFLAGS=-fPIC make -j $(nproc) && make install
        popdrm # zstd-1.3.5
        # no dynamic linking
        find /usr/local -name libzstd*.so* -delete # no dynamic linking

        ################### OpenSSL ########################
        pxy wget --quiet https://github.com/openssl/openssl/archive/OpenSSL_1_0_2p.tar.gz
        tar xvf OpenSSL_1_0_2p.tar.gz
        pushd openssl-OpenSSL_1_0_2p
        ./config no-shared no-dso --prefix=/usr/local/ -fPIC && make -j $(nproc) && make install
        popdrm #openssl-OpenSSL_1_0_2p

        ################### Libcurl ########################
        pxy wget --quiet https://github.com/curl/curl/releases/download/curl-7_62_0/curl-7.62.0.tar.gz
        tar xvf curl-7.62.0.tar.gz
        pushd curl-7.62.0
        CFLAGS="-fPIC" ./configure && make -j $(nproc) && make install
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
    popd #src

    mkdir git

popd # /opt/deps

#################### standard with clone cmake make install  ##########################
clone_make_install https://github.com/google googletest release-1.8.0
clone_make_install https://github.com/google double-conversion v3.1.1
clone_make_install https://github.com/libevent libevent release-2.1.8-stable
clone_make_install https://github.com/google glog v0.3.5
clone_make_install https://github.com/gflags gflags v2.2.2


#################### Folly ##########################

clone_depth_1 https://github.com/facebook folly v2018.08.06.00
pushd /opt/deps/git/folly
    sed -i 's/find_package(Boost 1.51.0 MODULE/find_package(Boost 1.67.0 MODULE/g' CMake/folly-deps.cmake
    sed -i 's/target_link_libraries(GenerateFingerprintTables PRIVATE folly_deps)/target_link_libraries(GenerateFingerprintTables PRIVATE folly_deps -static-libgcc -static-libstdc++)/g' CMakeLists.txt
    # Fix some gcc8.2 errors
    echo 'SET( CMAKE_CXX_FLAGS  "${CMAKE_CXX_FLAGS} -Wno-error=class-memaccess")' >> CMakeLists.txt
popd # /opt/deps/git/folly

mkpushd /tmp/folly_build
    cmake ${MY_CMAKE_ARGS} /opt/deps/git/folly && make -j $(nproc) && make install
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

clone_depth_1 https://github.com/jupp0r prometheus-cpp v0.12.3
pushd /opt/deps/git/prometheus-cpp
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

#################### Wangle ##########################

clone_depth_1 https://github.com/facebook wangle v2018.08.06.00
mkpushd /tmp/wangle_build/
    sed -i 's/find_package(Glog REQUIRED)/find_package(GLog REQUIRED)/g' /opt/deps/git/wangle/wangle/CMakeLists.txt
    cmake /opt/deps/git/wangle/wangle
    LD_LIBRARY_PATH=/usr/local/lib/; make
    make install
popd #  /tmp/wangle_build/

#################### librdkafka  ##########################
clone_depth_1 https://github.com/edenhill librdkafka v1.5.2
cd /opt/deps/git/librdkafka
    ./configure --enable-ssl --enable-gssapi
    make -j 10
    make install
    # Just remove all .so files for rdkafka, make Cmake link to the static lib.
    rm -rf /usr/local/lib/librdkafka*.so*

#################### cppkafka  ##########################
clone_depth_1 https://github.com/mfontanini cppkafka v0.3.1

mkpushd /tmp/cppkafka_build
    sed -i 's/-Wall\"/-Wall -fPIC\"/g' /opt/deps/git/cppkafka/CMakeLists.txt
    cmake -DCPPKAFKA_BUILD_SHARED=OFF -DCPPKAFKA_RDKAFKA_STATIC_LIB=ON /opt/deps/git/cppkafka
    LD_LIBRARY_PATH=/usr/local/lib/;  make -j 10
    make install
popd # /tmp/cppkafka_build

#################### msgpack  ##########################

clone_depth_1 https://github.com/msgpack msgpack-c cpp-3.3.0
mkpushd /tmp/msgpack_build
cmake -DMSGPACK_CXX17=ON -DMSGPACK_ENABLE_SHARED=OFF  -DMSGPACK_BUILD_EXAMPLES=OFF -DMSGPACK_BUILD_TESTS=OFF /opt/deps/git/msgpack-c && make -j $(nproc) && make install
popd # /tmp/msgpack_build


rm -rf /tmp/*_build/ /tmp/mongo-cxx-driver
#rm  /opt/deps/src/*
