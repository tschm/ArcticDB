# Docker

## Structure

Due to Docker [layers](https://docs.docker.com/storage/storagedriver/#images-and-layers) builds
only do work for the changed layer of the `Dockerfile` downwards, so if possible update later layers
in preference to earlier ones. In particular, `install_dev_tools.sh` takes a long time as it has to download CLion through our file-scanning man-in-the-middle proxy.

## Dev Process

To iterate on the docker image locally:
 * Set `img_prefix=arcticdb-manylinuxman` and `build_tag=latest` in `manylinux.versions`
 * Make changes to the Dockerfile, entrypoint script, etc
 * From the `docker` directory, run `./buildimg.sh`
 * Run the built image from the `man.arcticdb` root directory as usual with `INTERACTIVE=1 docker/run.sh manylinux`

## Release Process

This describes how to push a new build of the dev container to Artifactory, so that it can be used
by other developers.

Log in to Docker:

`docker login -u ahldev -p <HIGHLY SECURE PASSWORD REDACTED> pre-releases-docker.repo.prod.m`

Build and push to pre-releases:

```
./build_and_push.sh
# Now commit and push the new manylinux.versions file
```

The relationship between releases-docker and pre-releases-docker is a bit confusing. releases-docker
is a read-only mirror of pre-releases-docker, but only images that have been pulled _at least once_ are
visible through releases-docker.

