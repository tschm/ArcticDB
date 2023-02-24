ARG PEG_VERSION
ARG PEG_IMAGE
FROM releases-docker.repo.prod.m/man/base/${PEG_IMAGE}:${PEG_VERSION}

ADD install_pkg_manager.sh  /tmp/install_pkg_manager.sh

RUN /tmp/install_pkg_manager.sh

ADD install_tools.sh /tmp/install_tools.sh

RUN /tmp/install_tools.sh # gcc 8.2.0 do not put anything above since it will recompile gcc

#sudo docker push ahl.docker.dev.ahl/app/medxx:<tag>
