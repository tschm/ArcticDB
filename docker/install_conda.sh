#!/bin/bash

function pxy(){
    http_proxy=http://svc-ahlwebproxy:69L92j5TEsFCpz@euro-webproxy.drama.man.com:8080 https_proxy=http://svc-ahlwebproxy:69L92j5TEsFCpz@euro-webproxy.drama.man.com:8080 "$@"
}

#pxy curl https://repo.continuum.io/miniconda/Miniconda2-4.5.4-Linux-x86_64.sh -o /tmp/miniconda.sh
#chmod u+x /tmp/miniconda.sh
#/tmp/miniconda.sh -f -b -p /opt/conda

#. /opt/conda/bin/activate
source /opt/man/releases/python-medusa/27-3/bin/activate

pxy conda install -y cmake

