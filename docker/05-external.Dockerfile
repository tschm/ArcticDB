ARG IMGTAG
FROM ${IMGTAG}

ADD withproxy /usr/bin/withproxy

RUN mkdir -p /opt/pythons/

RUN withproxy curl -fsSL -o /opt/pythons/_3.6.0 https://www.python.org/ftp/python/3.6.0/Python-3.6.0.tgz
RUN withproxy curl -fsSL -o /opt/pythons/_3.7.0 https://www.python.org/ftp/python/3.7.0/Python-3.7.0.tgz
RUN withproxy curl -fsSL -o /opt/pythons/_3.8.0 https://www.python.org/ftp/python/3.8.0/Python-3.8.0.tgz
RUN withproxy curl -fsSL -o /opt/pythons/_3.9.0 https://www.python.org/ftp/python/3.9.0/Python-3.9.0.tgz
RUN withproxy curl -fsSL -o /opt/pythons/_3.10.0 https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz

RUN mkdir /opt/pythons/3.{6,7,8,9,10}.0

RUN tar -xvf /opt/pythons/_3.6.0 -C /opt/pythons/3.6.0 --strip-components=1
RUN tar -xvf /opt/pythons/_3.7.0 -C /opt/pythons/3.7.0 --strip-components=1
RUN tar -xvf /opt/pythons/_3.8.0 -C /opt/pythons/3.8.0 --strip-components=1
RUN tar -xvf /opt/pythons/_3.9.0 -C /opt/pythons/3.9.0 --strip-components=1
RUN tar -xvf /opt/pythons/_3.10.0 -C /opt/pythons/3.10.0 --strip-components=1
RUN bash -c 'mkdir /opt/pythons/3.{7,6,8,9,10}.0/install'

RUN yum install -y libffi libffi-devel bzip2-devel

RUN withproxy wget -O /tmp/openssl-1.1.1.tar.gz https://ftp.openssl.org/source/old/1.1.1/openssl-1.1.1.tar.gz
RUN tar -C /tmp -xvf /tmp/openssl-1.1.1.tar.gz
RUN mkdir /tmp/ssl11
RUN mkdir /tmp/ssl11dir
WORKDIR /tmp/openssl-1.1.1
RUN bash -c './config --prefix=/tmp/ssl11 --openssldir=/tmp/ssl11dir'
RUN bash -c 'make -j 4'
RUN bash -c 'make install'

RUN bash -c 'cd /opt/pythons/3.6.0; ./configure --prefix /opt/pythons/3.6.0/install; make -j 4; make altinstall'
RUN bash -c 'cd /opt/pythons/3.7.0; ./configure --prefix /opt/pythons/3.7.0/install; make -j 4; make altinstall'
RUN bash -c 'cd /opt/pythons/3.8.0; ./configure --prefix /opt/pythons/3.8.0/install; make -j 4; make altinstall'
RUN bash -c 'cd /opt/pythons/3.9.0; ./configure --prefix /opt/pythons/3.9.0/install; make -j 4; make altinstall'
RUN bash -c 'cd /opt/pythons/3.10.0; ./configure --with-openssl=/tmp/ssl11 --with-openssl-rpath=auto --prefix /opt/pythons/3.10.0/install; make -j 4; make altinstall'

run bash -c 'ln -s /opt/pythons/3.8.0/install/include/python3.8 /opt/pythons/3.8.0/install/include/python3.8m'
run bash -c 'ln -s /opt/pythons/3.9.0/install/include/python3.9 /opt/pythons/3.9.0/install/include/python3.9m'
run bash -c 'ln -s /opt/pythons/3.10.0/install/include/python3.10 /opt/pythons/3.10.0/install/include/python3.10m'

RUN chmod 777 -R /opt/pythons/3*

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
