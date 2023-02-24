ARG IMGTAG
FROM ${IMGTAG}

ADD tls-ca-bundle.pem /etc/pki/ca-trust/source/anchors/
RUN update-ca-trust

ADD install_cmake.sh /tmp/install_cmake.sh
RUN /tmp/install_cmake.sh

ADD bootstrap /opt/bootstrap
RUN /opt/bootstrap/install-boost.sh
