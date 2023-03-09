# Workflow

## Setup

```
git config push.recurseSubmodules on-demand
git submodule update --init --recursive
```

```
cd arcticdb_link
git remote set-url origin <URL with your username and token with write access>
```

## Typical workflow

Checkout a new branch for `arcticdb`:

```
cd arcticdb_link
git checkout -b my-branch
cd ..
```

Work and commit as usual:

```
# Spin up dev container
INTERACTIVE=1 docker/run.sh 36 /bin/bash

# Make changes and commit in arcticdb_link/
```

When done, push from the parent `man.arcticdb` directory:

```
git add arcticdb_link
git commit -m "Testing changes"
git push
```

Due to the `recurseSubmodules on-demand` option we set earlier, this will push the submodule first
and then the parent (pointing at the new submodule HEAD).

You will be able to see your build in [Jenkins](https://manbuild-ci.res.m/job/manbuilds/job/pegasus/job/current/job/DATA/job/man.arcticdb/).

