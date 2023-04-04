# Docker

## Structure

Due to Docker [layers](https://docs.docker.com/storage/storagedriver/#images-and-layers) builds
only do work for the changed layer of the `Dockerfile` downwards, so if possible update later layers
in preference to earlier ones.

## Release Process

This describes how to push a new build of the dev container to Artifactory, so that it can be used
by other developers.

Log in to Docker:

`docker login -u ahldev -p <HIGHLY SECURE PASSWORD REDACTED> pre-releases-docker.repo.prod.m`

Build and push to pre-releases:

```
./build_and_push.sh
rename ".new" "" *.new  # Create new manylinux.versions file
# Now commit and push the new manylinux.versions file
```

The relationship between releases-docker and pre-releases-docker is a bit confusing. releases-docker
is a read-only mirror of pre-releases-docker, but only images that have been pulled _at least once_ are
visible through releases-docker.

