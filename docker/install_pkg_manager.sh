#!/bin/bash

set -euo pipefail


yum install -y which git make curl bzip2 wget binutils-devel
# needed by gcc below
yum install -y gmp-devel mpfr-devel libmpc-devel gcc gcc-c++ make libtool patch pkgconfig autoconf automake binutils bison flex

yum clean all
