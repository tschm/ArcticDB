#!/bin/bash

function pxy(){
    http_proxy=http://svc-ahlwebproxy:69L92j5TEsFCpz@euro-webproxy.drama.man.com:8080 https_proxy=http://svc-ahlwebproxy:69L92j5TEsFCpz@euro-webproxy.drama.man.com:8080 "$@"
}


pxy wget --quiet https://cmake.org/files/v3.14/cmake-3.14.7-Linux-x86_64.sh
mkdir /opt/cmake
bash cmake-3.14.7-Linux-x86_64.sh --prefix=/opt/cmake --skip-license
