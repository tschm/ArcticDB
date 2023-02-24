export CC=/opt/gcc/8.2.0/bin/gcc
export CXX=/opt/gcc/8.2.0/bin/g++

export PATH="/opt/gcc/8.2.0/bin:/opt/cmake/bin:$PATH"
alias cmake=/opt/cmake/bin/cmake

function pxy(){
    http_proxy=http://svc-ahlwebproxy:69L92j5TEsFCpz@euro-webproxy.drama.man.com:8080 https_proxy=http://svc-ahlwebproxy:69L92j5TEsFCpz@euro-webproxy.drama.man.com:8080 "$@"
}

