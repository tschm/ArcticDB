# man.arcticdb

This repository serves as a bridge between the external ArcticDB project published on PyPi and
Github, and Man Group's internal Python and development environments. 

It also offers a backwards compatibility layer that redirects imports from the legacy `arcticc` project to the new, 
Github hosted, replacement, [ArcticDB](https://github.com/man-group/arcticdb).

## Developer Tooling

This repository also includes the Arctic Native team's development tooling so that the team can work
on `ArcticDB` on Man Group machines. This is in the `docker/` subdirectory and should not be of
any general interest outside of the team. The internal development workflow for `ArcticDB` is
documented below.

### Setup

```
git config push.recurseSubmodules on-demand
git submodule update --init --recursive
cd arcticdb_link
git remote set-url origin <URL with your username and token with write access>
```

### Typical workflow

See [the wiki](https://manwiki.maninvestments.com/display/AlphaTech/ArcticDB+Development+Setup).

## Compatibility Layer

`man.arcticdb` pulls in the `ArcticDB` wheel.

This repo provides an API backwards-compatibility bridge between `arcticc` and `ArcticDB` so that
Man users can pick up `ArcticDB` changes without making changes to their own code.

Currently, `ArcticDB` is used if and only if the environment variable `MAN_ARCTICDB_USE_ARCTICDB=true`.

The bridge redirects Python imports from `arcticc` and `arcticcxx` to their replacements in `ArcticDB`, 
`arcticdb` and `arcticdb_ext`.

The build also runs tests against the `arcticdb` wheel that Man grabs
[from PyPi](https://mangit.maninvestments.com/projects/CORE/repos/external-python/browse/external-packages.yaml).

These are:

- The ArcticDB tests themselves, to check compatibility with Man's Python package pins.
- Additional Man-specific non-regression tests (nonreg) that we cannot put in the public Github repo.
- API compatibility tests to verify compatibility with the `arcticc` API.

### Running compatibility tests locally

The tests for the `man.arcticdb` bridge are in `./tests`.

Run them with the usual:

```
python setup.py develop test
```

in a fresh Pegasus venv.
