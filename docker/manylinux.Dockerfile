FROM releases-docker.repo.prod.m/man/base/manylinux2014_x86_64:2021-11-28-06a91ec
RUN yum update -y &&    \
    yum install -y wget && \
    bash -c 'http_proxy=http://10.193.3.6:8080 wget http://mirror.centos.org/centos/7/sclo/x86_64/rh/Packages/d/devtoolset-10-libatomic-devel-10.2.1-11.1.el7.x86_64.rpm' && \
    yum install -y devtoolset-10-libatomic-devel-10.2.1-11.1.el7.x86_64.rpm && \
    yum install -y zip openssl-devel cyrus-sasl-devel libcurl-devel &&     \
    rpm -Uvh --nodeps $(repoquery --location mono-{core,web,devel,data,wcf,winfx}) &&     \
    yum clean all