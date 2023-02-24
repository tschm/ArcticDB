# Docker helpers

## Why docker ?

In order to make builds more easily reproducible, the full build environment is shipped as a docker container.
This has the benefit of making it easy for developers to start working without installing any specific libraries, and avoid having idiosyncratic problems due to locally installed libraries with unknown versions.

## Requirements

`python setup.py build` requires
`pyinstall grpcio-tools`

`python setup.py develop` has no such requirement.

## How can I build a native module ?

The simplest way to run the build is to call `python setup.py build` as usual:

```
(cxxenv273) [master !] ~/dev/arcticc $ python setup.py build
running build
running build_ext
build/lib.linux-x86_64-2.7
build/temp.linux-x86_64-2.7
Running ahl.docker.prod.ahl/app/medcxx-27-3:build-latest
Starting with UID : 113159
-- The C compiler identification is GNU 8.2.0
-- The CXX compiler identification is GNU 8.2.0
-- Check for working C compiler: /opt/gcc/8.2.0/bin/gcc
-- Check for working C compiler: /opt/gcc/8.2.0/bin/gcc -- works
-- Detecting C compiler ABI info
-- Detecting C compiler ABI info - done
-- Detecting C compile features
-- Detecting C compile features - done
-- Check for working CXX compiler: /opt/gcc/8.2.0/bin/g++
-- Check for working CXX compiler: /opt/gcc/8.2.0/bin/g++ -- works
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Found PythonInterp: /usr/bin/python (found version "2.7.5") 
-- Found PythonLibs: python2.7
-- Performing Test HAS_CPP14_FLAG
-- Performing Test HAS_CPP14_FLAG - Success
-- pybind11 v2.3.dev0
-- Looking for pthread.h
-- Looking for pthread.h - found
-- Looking for pthread_create
-- Looking for pthread_create - not found
-- Looking for pthread_create in pthreads
-- Looking for pthread_create in pthreads - not found
-- Looking for pthread_create in pthread
-- Looking for pthread_create in pthread - found
-- Found Threads: TRUE  
-- Configuring done
-- Generating done
-- Build files have been written to: /tmp/build
Scanning dependencies of target arcticcxx
Scanning dependencies of target TestMyMagicFunc
[ 25%] Building CXX object arcticc/CMakeFiles/TestMyMagicFunc.dir/test_my_magic_func.cpp.o
[ 50%] Building CXX object arcticc/CMakeFiles/arcticc.dir/python_module.cpp.o
[ 75%] Linking CXX executable TestMyMagicFunc
[ 75%] Built target TestMyMagicFunc
[100%] Linking CXX shared module arcticcxx.so
[100%] Built target arcticc
Test project /tmp/build/arcticc
    Start 1: testMyMagicFunc.MagicNumber
1/1 Test #1: testMyMagicFunc.MagicNumber ......   Passed    0.01 sec

100% tests passed, 0 tests failed out of 1

Total Test time (real) =   0.01 sec
```

This
 * spins up the build container
 * generates the build files
 * builds the targets
 * runs the unit tests
 * copies the extension to the mapped build directory

This produces the following .so file

```
(cxxenv273) [master !] ~/dev/arcticc $ tree build/
build/
├── bdist.linux-x86_64
└── lib.linux-x86_64-2.7
    └── arcticcxx.so

2 directories, 1 file
```

To simplify loading of components during python unit tests, the .so file is symlinked at the root of the directory

Now it's as easy to access as loading a module:

```
python -c 'import arcticcxx; print(arcticcxx.get_version_string())'
```

## How are the docker images built ?

### Structure

There are 3 distince images per medusa flavour that are built:
 1. Base image from the relevant base medusa package + gcc8.2 is built by docker/01-gcc.Dockerfile
 1. Download, compile and install all the tools and dependencies used by this library using docker/02-deps.Dockerfile
 1. Build an thin image from the previous one with necessary tools to run interactively and map user directory with correct permissions to make mapping of directories and export of data outside the container transparent

### 01-gcc

```
./buildimg.sh gcc 273
```

Building takes less than an hour on a 36 core box.

### 02-deps

This step downloads and builds dependencies.

Here is a list:
 * boost
 * zlib
 * jemalloc
 * lz4
 * zstd
 * openssl
 * googletest
 * double-conversion
 * libevent
 * folly (most of the dependencies above are folly's own dependencies)
 * protobuf
 * xxHash
 * glog
 * gflags
 * mongo-c-driver
 * mongo-cxx-driver

Because we aim at building a python module with everything statically linked, we favor static builds in the various configurations.
All the dependencies are installed in /usr/local (which is ok inside a container).

Building takes about 10min on a 36 core box.

You can build it using:

```
./buildimg.sh deps 273
sudo docker tag ...
```

### 03-build

This steps is meant to make it easy to start the container with directories mapped with read/write permissions as the user running the container.

It just creates an entrypoint for the container that calls gosu under the hood.
Inspired from https://denibertovic.com/posts/handling-permissions-with-docker-volumes/

This is really easy to build and should be instantaneous.

Commands to build it (after the previous step has been done)

```
./buildimg.sh build 273
```

### How can I configure versions ?

`docker/current.versions` is a symlink to the currently used version of medusa and intermediate images used to build intermediate images.
`current.versions/build_image` contains the version of the build image used when calling docker/run.sh

### Image sizes

The total image produced weights ~4GiB.

```
(/) [master !?] ~/dev/arcticc/docker $ sudo docker image list
REPOSITORY                                TAG                    IMAGE ID            CREATED             SIZE
arcticc-build-273                         latest                 e2e938932a0b        58 seconds ago      3.97GB
arcticc-deps-273                          latest                 44802335c528        9 minutes ago       3.97GB
ahl.docker.prod.ahl/app/medcxx-27-3       gcc8.2-20180810-1142   54f47819e697        4 hours ago         2.93GB
base.docker.prod.ahl/base/medusa-python   27-2                   d8a18bcad5c0        8 months ago        1.92GB
```

It's a total 2GB added on top of the initial medusa image. ~800MiB are from gcc itself, and the sum of the rest from the various dependencies installed.

```
IMAGE               CREATED             CREATED BY                                      SIZE                COMMENT
44802335c528        26 minutes ago      /bin/sh -c /opt/bootstrap/install.sh            899MB               Download and install dependencies
3bd989cb927b        35 minutes ago      /bin/sh -c #(nop) ADD dir:611c68406a3c73d2...   10.4MB              
40621a8452ce        3 hours ago         /bin/sh -c /tmp/install_cmake.sh                130MB               Install cmake
e9764a3f7bc8        3 hours ago         /bin/sh -c #(nop) ADD file:96734f830a81b43...   368B                
54f47819e697        4 hours ago         /bin/sh -c /tmp/install_tools.sh # gcc 8.2...   857MB               Install gcc
0b5f24c86f57        4 hours ago         /bin/sh -c #(nop) ADD file:ca8386a066391f3...   689B                
1b6ceb62a9fe        46 hours ago        /bin/sh -c /tmp/install_pkg_manager.sh          156MB               Install tools with yum
ac8d73d12b63        46 hours ago        /bin/sh -c #(nop) ADD file:de3ec5e01839d17...   259B       
```

