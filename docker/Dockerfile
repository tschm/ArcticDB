ARG PEG_VERSION
ARG PEG_IMAGE
FROM releases-docker.repo.prod.m/man/base/${PEG_IMAGE}:${PEG_VERSION}

# GCC
ADD install_pkg_manager.sh  /tmp/install_pkg_manager.sh
RUN /tmp/install_pkg_manager.sh
ADD install_tools.sh /tmp/install_tools.sh
RUN /tmp/install_tools.sh

# Boost
ADD tls-ca-bundle.pem /etc/pki/ca-trust/source/anchors/
RUN update-ca-trust

ADD install_cmake.sh /tmp/install_cmake.sh
RUN /tmp/install_cmake.sh

ADD bootstrap /opt/bootstrap
RUN /opt/bootstrap/install-boost.sh

# Deps
ADD bootstrap /opt/bootstrap
RUN yum install libuuid-devel cyrus-sasl-devel -y && yum clean all
ADD custom_cmakefiles /tmp/custom_cmakefiles
RUN /opt/bootstrap/install-deps.sh

# Dev Tools
RUN yum install -y tmux tree openssh-server dropbear krb5-devel pulseaudio-libs-devel && yum clean all
RUN ln -s /usr/libexec/openssh/sftp-server /usr/libexec/sftp-server
COPY install_dev_tools.sh /tmp/install_dev_tools.sh
ENV JAVA_HOME=/opt/ahl/releases/java/jdk1.8.0_131
RUN /tmp/install_dev_tools.sh

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
