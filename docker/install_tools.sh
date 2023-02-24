#!/bin/bash

set -euo pipefail

function pxy(){
    http_proxy=http://svc-ahlwebproxy:69L92j5TEsFCpz@euro-webproxy.drama.man.com:8080 https_proxy=http://svc-ahlwebproxy:69L92j5TEsFCpz@euro-webproxy.drama.man.com:8080 "$@"
}

pxy curl https://ftp.gnu.org/gnu/gcc/gcc-8.2.0/gcc-8.2.0.tar.gz -o /tmp/gcc-8.2.0.tar.gz

mkdir -p /opt/gcc/8.2.0
pushd /tmp
tar xvf gcc-8.2.0.tar.gz

mkdir gcc-8.2.0-build
pushd gcc-8.2.0-build
../gcc-8.2.0/configure --enable-languages=c,c++ --disable-multilib --prefix=/opt/gcc/8.2.0
make -j$(nproc) && make install
popd # gcc-8.2.0-build

popd # /tmp

# Cleanup after building
rm -rf /tmp/gcc-8.2.0-build /tmp/gcc-8.2.0 /tmp/gcc-8.2.0-build /tmp/gcc-8.2.0.tar.gz
