ARG IMGTAG
FROM ${IMGTAG}

ADD bootstrap /opt/bootstrap
RUN yum install libuuid-devel pulseaudio-libs-devel cyrus-sasl-devel -y

ADD custom_cmakefiles /tmp/custom_cmakefiles

RUN /opt/bootstrap/install-deps.sh
