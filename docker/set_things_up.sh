#!/bin/bash

bash /tmp/install_pycxx
sleep 2
. /home/user/pyenvs/pycxx/bin/activate
. /opt/arcticc/aliases.sh
clion /opt/arcticc/ &
read prompt
cd /tmp/build/
make -j 20 && make install && restore_symlinks
