ARG IMGTAG
FROM ${IMGTAG}

RUN rm -f /etc/yum.repos.d/*
ADD man.repo /etc/yum.repos.d/

RUN yum install -y python3-devel openssh-clients

COPY bootstrap /opt/bootstrap

RUN rpm -Uvh --nodeps $(repoquery --location dropbear)
RUN rpm -Uvh --nodeps $(repoquery --location libtommath)
RUN rpm -Uvh --nodeps $(repoquery --location libtomcrypt)

RUN bash -c "cp /opt/bootstrap/.curlrc /root"
RUN bash -c "cp /opt/bootstrap/.wgetrc /root"
RUN bash -c 'echo "export PATH=/opt/rh/devtoolset-10/root/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:\$PATH" >> /root/.bash_profile'
RUN bash -c 'echo "export VCPKG_DEFAULT_BINARY_CACHE=/scratch/data/vcpkg_cache" >> /root/.bashrc'

RUN bash /opt/bootstrap/install_dev_tools.sh

