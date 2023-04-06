# man.arcticdb

This repository serves as a bridge between the external ArcticDB project published on PyPi and
Github, and Man Group's internal Python and development environments. It also offers a backwards
compatibility layer that redirects imports from the legacy `arcticc` project to the new, Github
hosted, replacement, [ArcticDB](https://github.com/man-group/arcticdb).

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

## WIP Compatibility Layer

`man.arcticdb` pulls in the `ArcticDB` wheel. A project may depend on at most one of `man.arcticdb`,
`arcticc`, or `ArcticDB`.

This repo provides an API backwards-compatibility bridge between `arcticc` and `ArcticDB` so that
Man users can pick up `ArcticDB` changes without making changes to their own code.

It redirects Python imports from `arcticc` and `arcticcxx` to their replacements in `ArcticDB`, 
`arcticdb` and `arcticdb_ext`.

The build also runs tests against the `arcticdb` wheel that Man grabs
[from PyPi](https://mangit.maninvestments.com/projects/CORE/repos/external-python/browse/external-packages.yaml).
These are:

- The ArcticDB tests themselves, to check compatibility with Man's Python package pins.
- Additional Man-specific non-regression tests (nonreg) that we cannot put in the public Github repo.
- API compatibility tests to verify compatibility with the `arcticc` API.

### TODO

- Set this repository up as a Python package.
- Set up Pegasus-next Jenkins build that installs ArcticDB and `man.arcticdb`.
- Run ArcticDB tests in Jenkins build (involves pulling the tagged sources).
- Add simple API compat tests.
- Implement the shim. Note that some code eg these [creds](https://mangit.maninvestments.com/projects/DATA/repos/arcticc/browse/arcticc/config.py#57-60)
have not survived the move and we need to do something about them to keep existing `arcticc` consumers happy.
- Extend API compat tests.
- Add nonreg tests.
- Replace `arcticc` [dependencies](https://docs.maninvestments.com/core/packages/internal/arcticc/)
in Man Group with `man.arcticdb` dependencies.

Remember to add merge checks to this repo.

