ARG IMGTAG
FROM ${IMGTAG}

RUN rm -f /etc/yum.repos.d/*
ADD man.repo /etc/yum.repos.d/

RUN yum install -y python3-devel

COPY bootstrap /opt/bootstrap

RUN rpm -Uvh --nodeps $(repoquery --location dropbear)
RUN rpm -Uvh --nodeps $(repoquery --location libtommath)
RUN rpm -Uvh --nodeps $(repoquery --location libtomcrypt)

RUN bash -c "cp /opt/bootstrap/.curlrc /root"
RUN bash -c "cp /opt/bootstrap/.wgetrc /root"

RUN bash /opt/bootstrap/install_dev_tools.sh
