export MY_CMAKE_ARGS="-DCMAKE_IGNORE_PATH=/opt/man/releases/python-medusa/27-2/lib -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_BUILD_TYPE=Release"


function mkpushd(){
    local d=$1
    mkdir $d && pushd $d
}

function popdrm(){
    local d=$(pwd)
    popd
    rm -rf $d
}

function clone_depth_1(){
    local url=$1
    local name=$2
    local tag=$3
    pxy git clone ${url}/${name}.git --branch $tag --depth 1 /opt/deps/git/${name}
}

function clone_depth_submodules_1(){
    local url=$1
    local name=$2
    local tag=$3
    pxy git clone ${url}/${name}.git --branch $tag --depth 1 --recurse-submodules /opt/deps/git/${name}
}

function clone_make_install(){
    local url=$1
    local name=$2
    local tag=$3
    clone_depth_1 $url $name $tag
    src=/opt/deps/git/${name}
    mkpushd /tmp/${name}_build
        pxy /opt/cmake/bin/cmake ${MY_CMAKE_ARGS} $src
        pxy make -j $(nproc) && make install
    popd # /tmp/${name}_build
}

