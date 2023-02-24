# Docker helpers

## Why docker ?

In order to make builds more easily reproducible, the full build environment is shipped as a docker container.
This has the benefit of making it easy for developers to start working without installing any
specific libraries, and avoid having idiosyncratic problems due to locally installed libraries with unknown versions.

## Requirements

`python setup.py build` requires
`pyinstall grpcio-tools`

`python setup.py develop` has no such requirement.

## How can I build a native module ?

The simplest way to run the build is to call `python setup.py build` as usual.
This
 * spins up the build container
 * generates the build files
 * builds the targets
 * runs the unit tests
 * copies the extension to the mapped build directory

and produces the following .so file

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

There is a distinct image for each Python version:

- pegasus-current (36)
- pegasus-next (38)
- medusa (36-1)

Due to Docker [layers](https://docs.docker.com/storage/storagedriver/#images-and-layers) builds
only do work for the changed layer of the `Dockerfile` downwards, so if possible update later layers
in preference to earlier ones.

Build with:

```
# last arg specifies the Python version, choices are <36,38,medusa>
./buildimg.sh build 36

# to push to pre-releases Docker repo
./buildimg.sh build 36 not-local

# pull your image from pre-releases to make it available from releases
sudo docker pull releases-docker.repo.prod.m/man/app/pegcxx-36:build-A_NEW_TAG  # fails
sudo docker pull pre-releases-docker.repo.prod.m/man/app/pegcxx-36:build-A_NEW_TAG
sudo docker pull releases-docker.repo.prod.m/man/app/pegcxx-36:build-A_NEW_TAG  # succeeds

# You can build for all Python versions at once with:
./build_all_images.sh
rename ".new" "" *.new
```

The releationship between releases-docker and pre-releases-docker is a bit confusing. releases-docker
is a read-only mirror of pre-releases-docker, but only images that have been pulled _at least once_ are
visible through releases-docker.

### How can I configure versions ?

`docker/{36,38,medusa}.versions` specify the build container tag to use for each Python flavour,
both in Jenkins and through `docker/run.sh` for development within the container. Updating it
is transparent to Jenkins, but you will need to notify other developers on the team to update their
local containers if you merge an update.

