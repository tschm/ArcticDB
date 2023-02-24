#!/bin/bash

function pxy(){
    http_proxy=http://svc-ahlwebproxy:69L92j5TEsFCpz@euro-webproxy.drama.man.com:8080 https_proxy=http://svc-ahlwebproxy:69L92j5TEsFCpz@euro-webproxy.drama.man.com:8080 "$@"
}

pxy curl https://ftp.gnu.org/gnu/gcc/gcc-8.2.0/gcc-8.2.0.tar.gz -o /tmp/gcc-8.2.0.tar.gz

