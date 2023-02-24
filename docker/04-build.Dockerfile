ARG IMGTAG
FROM ${IMGTAG}
RUN yum install -y tmux tree openssh-server dropbear krb5-devel && yum clean all
RUN ln -s /usr/libexec/openssh/sftp-server /usr/libexec/sftp-server 
COPY install_dev_tools.sh /tmp/install_dev_tools.sh
ENV JAVA_HOME=/opt/ahl/releases/java/jdk1.8.0_131
RUN /tmp/install_dev_tools.sh
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
