ARG IMGTAG
FROM ${IMGTAG}
ARG REQUIREMENTS

ADD certificate_authorities /etc/pki/ca-trust/source/anchors/
RUN update-ca-trust

RUN rm -f /etc/yum.repos.d/*
ADD man.repo /etc/yum.repos.d/

RUN yum install -y python3-devel openssh-clients

RUN rpm -Uvh --nodeps $(repoquery --location dropbear)
RUN rpm -Uvh --nodeps $(repoquery --location libtommath)
RUN rpm -Uvh --nodeps $(repoquery --location libtomcrypt)

ENV PATH="/opt/rh/devtoolset-10/root/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:{$PATH}:/apps/research/tools/bin"
ENV VCPKG_DEFAULT_BINARY_CACHE=/"scratch/data/vcpkg_cache"

ADD withproxy /opt/bootstrap/

# CLion stuff
ADD bootstrap/.curlrc /root/
ADD bootstrap/install_dev_tools.sh /opt/bootstrap/
ADD bootstrap/cxx_profile.sh /opt/bootstrap/
RUN /opt/bootstrap/install_dev_tools.sh

# Python dependenices for testing in the container
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.6 1
RUN mkdir -p /root/venv
RUN python -m venv /root/venv
RUN \
source /root/venv/bin/activate && \
/opt/bootstrap/withproxy pip --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org install --upgrade pip && \
/opt/bootstrap/withproxy pip --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org install ${REQUIREMENTS}

# git completion
RUN curl https://raw.githubusercontent.com/git/git/master/contrib/completion/git-completion.bash -o /root/.git-completion.bash
RUN echo "source /root/.git-completion.bash" >> /root/.bashrc

ADD manylinux_entrypoint.sh /opt/bootstrap/
ENTRYPOINT /opt/bootstrap/manylinux_entrypoint.sh