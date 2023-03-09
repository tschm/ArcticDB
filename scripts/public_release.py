"""
Creates a public release by building across all supported Python versions (36, 37, 38, 39 and 310 at the time of
writing). Optionally, the script will also archive the build directories and wheels to a given directory. Wheels are
the build directories zipped up, renamed to end in whl, and all binaries stripped of debug symbols.

After having built the wheels, to publish, pop into an "external" container:

NO_X11=1 INTERACTIVE=1 ./docker/run.sh external bash

Install Twine:

withproxy /opt/pythons/3.9.0/install/bin/pip3.9 install twine

Upload:

withproxy /opt/pythons/3.9.0/install/bin/twine upload --verbose -u blahblahblah -p <Personal Access Token> --repository-url https://pkgs.dev.azure.com/man-group-dev/arctic/_packaging/arctic-pub/pypi/upload dist/arctic-0.0.1-cp36-cp36m-linux_x86_64.whl --cert tls-ca-bundle.pem

To install across all python, use the many linux image:

sudo docker run -v <PATH TO ARCTIC>:/opt/arcticc -v <PATH TO ARCTIC>/docker/pip.conf:/root/.pip/pip.conf  -v /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem:/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem -v /apps/research/tools/bin/withproxy:/usr/bin/withproxy -it releases-docker.repo.prod.m/man/base/manylinux2014_x86_64:2021-11-28-06a91ec

Then install (for example 3.6):

withproxy /opt/python/cp36-cp36m/bin/pip install --index-url=https://arctic-pub:<PAT>@pkgs.dev.azure.com/man-group-dev/arctic/_packaging/arctic-pub/pypi/simple arctic
"""

import argparse
import configparser
import subprocess
import pathlib
import typing
import os
import sys


IS_WINDOWS = sys.platform == "win32"


def build(py_tag: str, version: str, archive: bool, archive_path: str, setup_path: str):
    args = ["python", setup_path, "bdist_wheel", "--python-tag", py_tag]
    # if archive:
    #     args += ["--archive=1", "--archive-path", archive_path]
    #     os.makedirs(os.path.join(archive_path, version, "archives"), exist_ok=True)
    #     os.makedirs(os.path.join(archive_path, version, "wheels"), exist_ok=True)

    print(f"Running '{args}'")
    ret = subprocess.run(args)
    ret.check_returncode()


def tag(version: str):
    if IS_WINDOWS:
        tag_name = f"external-build-windows-{version}"
    else:
        tag_name = f"external-build-linux-{version}"
    ret = subprocess.run(["git", "tag", tag_name])
    ret.check_returncode()
    ret = subprocess.run(["git", "push", "origin", tag_name])
    ret.check_returncode()


def run(py_tags: typing.List[str], version: str, tag: bool, archive: bool, archive_path: str, setup_path: str):
    for py_tag in py_tags:
        build(py_tag, version, archive=archive, archive_path=archive_path, setup_path=setup_path)

    if tag:
        tag(version)


def main():
    p = pathlib.Path(__file__).parent.resolve().parent
    os.chdir(os.path.join(p, "arcticdb_link"))

    cfg = configparser.ConfigParser()
    cfg.read("setup.cfg")

    config = {k: [_v for _v in v.split("\n") if _v] for k, v in cfg["metadata"].items()}
    config = {k: (v[0] if len(v) == 1 else v) for k, v in config.items()}

    parser = argparse.ArgumentParser(usage=__doc__)

    parser.add_argument("--py-tags", nargs="+", default=["cp36", "cp37", "cp38", "cp39", "cp310"])
    parser.add_argument(
        "--git-tag",
        required=False,
        default=False,
        action="store_true",
        help="Will tag (and push) " "Git tag. Tag set to " "external-build-PLATFORM-VERSION",
    )
    parser.add_argument("--no-archive", required=False, default=False, action="store_true")
    parser.add_argument("--archive-path", required=False, default="/data/team/data/arctic_native/external_releases/")

    opts = parser.parse_args()

    run(
        opts.py_tags,
        config["version"],
        opts.git_tag,
        not opts.no_archive,
        opts.archive_path,
        setup_path=os.path.join(p, "arcticdb_link", "setup.py"),
    )


if __name__ == "__main__":
    main()
