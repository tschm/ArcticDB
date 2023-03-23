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

RUN bash -c 'cd /opt/pythons/3.6.0; ./configure --prefix /opt/pythons/3.6.0/install; make -j 4; make altinstall'
RUN bash -c 'cd /opt/pythons/3.7.0; ./configure --prefix /opt/pythons/3.7.0/install; make -j 4; make altinstall'
RUN bash -c 'cd /opt/pythons/3.8.0; ./configure --prefix /opt/pythons/3.8.0/install; make -j 4; make altinstall'
RUN bash -c 'cd /opt/pythons/3.9.0; ./configure --prefix /opt/pythons/3.9.0/install; make -j 4; make altinstall'
RUN bash -c 'cd /opt/pythons/3.10.0; ./configure --with-openssl=/usr/local --with-openssl-rpath=auto --prefix /opt/pythons/3.10.0/install; make -j 4; make altinstall'

RUN bash -c 'ln -s /opt/pythons/3.8.0/install/include/python3.8 /opt/pythons/3.8.0/install/include/python3.8m'
RUN bash -c 'ln -s /opt/pythons/3.9.0/install/include/python3.9 /opt/pythons/3.9.0/install/include/python3.9m'
RUN bash -c 'ln -s /opt/pythons/3.10.0/install/include/python3.10 /opt/pythons/3.10.0/install/include/python3.10m'

RUN chmod 777 -R /opt/pythons/3*

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
