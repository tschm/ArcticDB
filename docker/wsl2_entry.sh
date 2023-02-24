#!/bin/bash

# This file assumes entrypoint.sh && install_pycxx is already captured in the image  

USER_ID=${LOCAL_USER_ID:-1000}

expected_uid=$(id -u user)
if [[ $USER_ID != $expected_uid ]]; then
    echo "UID $USER_ID does not match that when this container is captured ($expected_uid)." >&2
    exit -1
fi

HOME=/home/user
PATH="$HOME/bin:$PATH"
export PATH

. /etc/profile.d/cxx_profile.sh
if [[ -x ~/pyenvs/pycxx/bin/activate ]]
then . ~/pyenvs/pycxx/bin/activate
else . /default-pegasus-venv/bin/activate
fi

if ! mount | grep -q /opt/arcticc; then
    rm /opt/arcticc/requirements.txt
    rmdir /opt/arcticc
    ln -sT /{tmp,opt}/arcticc
fi

if [[ `id -u` -eq 0 ]]; then
	exec /usr/bin/gosu user "$@"
else
	exec $@
fi

