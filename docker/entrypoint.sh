#!/bin/bash

# Add local user
# Either use the LOCAL_USER_ID if passed in at runtime or
# fallback

USER_ID=${LOCAL_USER_ID:-9001}

echo "Starting with UID : $USER_ID"
useradd --shell /bin/bash -u $USER_ID -o -c "" -m user

#cat >> /etc/sudoers << EOF
#%sudo   ALL=(ALL:ALL) ALL
#EOF

export HOME=/home/user
ln -s /etc/profile /home/user/.profile

cat >> /home/user/.profile <<EOF
#source /etc/profile

function pxy(){
    http_proxy=http://svc-ahlwebproxy:69L92j5TEsFCpz@euro-webproxy.drama.man.com:8080 https_proxy=http://svc-ahlwebproxy:69L92j5TEsFCpz@euro-webproxy.drama.man.com:8080 "$@"
}

export MEDUSA_VERSION=$MEDUSA_VERSION
export MEDUSA_PYPI_URL="http://artifactory.svc.prod.ahl"
export ARTIFACTORY_PATH="artifactory/api/pypi"
export MEDUSA_DEFAULT_INDEX="\${ARTIFACTORY_PATH}/medusa"
export MEDUSA_RELEASE_INDEX="\${ARTIFACTORY_PATH}/releases-medusa"
export MEDUSA_EGG_CACHE="/etc/alternatives/medusa_egg_cache"
export TCL_LIBRARY="/opt/man/releases/python-medusa/\${MEDUSA_VERSION}/lib/tcl8.5"
export PYPI_URL="\$MEDUSA_PYPI_URL/\$MEDUSA_DEFAULT_INDEX-361/simple"

# Legacy medusa variables
export MEDUSA_DEVPI_URL="http://devpi.prod.ahl"
export MEDUSA_DEVPI_USER="ahl"
export MEDUSA_DEVPI_RELEASE_USER="release"

function regkernel()
{
    python -m ipykernel install --user --name=$1
}

# Deal with annoyances
alias vim=vi

EOF

cat >> /home/user/.vimrc <<EOF
set nocompatible
syntax on
set hidden
set wildmenu
set showcmd
set hlsearch
set ignorecase
set smartcase
set autoindent
set nostartofline
set confirm
set visualbell
set t_vb=
set number
set shiftwidth=4
set softtabstop=4
set expandtab

nnoremap <return> :noh<return><esc>

imap jj <Esc>
imap jk <Esc>

" Disable Arrow keys in Escape mode
map <up> <nop>
map <down> <nop>
map <left> <nop>
map <right> <nop>

map ; :

set t_Co=256
set background=dark
""let g:solarized_termcolors=256
""#let g:solarized_termtrans=1
""#colorscheme solarized
EOF

mkdir /home/user/bin
ln -s /default-medusa-venv/bin/python /home/user/bin/python

cat > /tmp/install_pycxx << EOF
#!/bin/bash
source ~/.profile
source /opt/man/releases/python-medusa-profile/python-medusa.sh

use_medusa_python \$MEDUSA_VERSION

mkvirtualenv pycxx
PYPI_URL="\$MEDUSA_PYPI_URL/\$MEDUSA_DEFAULT_INDEX-361/simple"
easy_install -i \$PYPI_URL ahl.pkglib

for d in \$(cat /opt/arcticc/requirements.txt) ; do
    pyinstall \$d
done
python -m ipykernel install --user --name=pycxx
EOF

chown user /tmp/install_pycxx

# run in subshell to avoid polluting the top level bash with pycxx specific stuff
chmod u+x /tmp/install_pycxx 

cat >> /home/user/bin/clion << EOF
#!/bin/bash

source /etc/profile.d/cxx_profile.sh

export PATH="/opt/gcc/8.2.0/bin:/opt/cmake/bin:/opt/clion/bin/gdb/linux/bin:$PATH"
alias cmake=/opt/cmake/bin/cmake

nohup /opt/clion/bin/clion.sh >> /tmp/clion.log 2>&1
EOF

cat >> /home/user/bin/db << EOF
#!/bin/bash
dropbear -w -g -R -p 2222 -P $HOME/.dbearPID
EOF

cat >> /home/user/bin/clion_remote << EOF
#!/bin/bash
set -e
/home/user/bin/db

if [ ! -d /tmp/clion_remote ]; then
  echo "Mount /tmp/clion_remote from docker to outside directory. Remote IDE will be downloaded to this directory and CLion will store project config data in this directory"
  exit 1
fi

# if /tmp/clion_remote exists, we expect it to be symlinked from /home/user/.cache
if [ ! -f /home/user/.cache/CLion-2021.3.2.tar.gz ]; then
    https_proxy=http://euro-webproxy.drama.man.com:8080 wget --no-check-certificate -P /home/user/.cache https://download.jetbrains.com/cpp/CLion-2021.3.2.tar.gz

    tar -xvf /home/user/.cache/CLion-2021.3.2.tar.gz -C /home/user/.cache
fi

/home/user/.cache/clion-2021.3.2/bin/remote-dev-server.sh run /opt/arcticc
EOF

chown user /home/user/bin/clion
chmod u+x /home/user/bin/clion
chown user /home/user/bin/db
chmod u+x /home/user/bin/db
chown user /home/user/bin/clion_remote
chmod u+x /home/user/bin/clion_remote

export PATH="$HOME/bin:$PATH"

if [[ -f "/tmp/authorized_keys" ]]; then
    mkdir -p /home/user/.ssh
    chown user /home/user/.ssh
    ln -s /tmp/authorized_keys /home/user/.ssh/authorized_keys
fi

if [[ -d "/etc/dropbear" ]]; then
    chown user /etc/dropbear
fi

mkdir /home/user/.pip
cat >> /home/user/.pip/pip.conf << EOF
[global]
trusted-host = pypi.org files.pythonhosted.org
EOF

if [[ -d "/tmp/clion_remote" ]]; then
  ln -s /tmp/clion_remote/cache /home/user/.cache
  ln -s /tmp/clion_remote/config /home/user/.config
fi

exec /usr/bin/gosu user "$@"
