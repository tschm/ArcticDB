import pytest
import subprocess
import sys
import os
import shutil


def get_arcticdb_version():
    info = subprocess.check_output([sys.executable, "-m", "pip", "show", "arcticdb"])
    lines = info.decode().split("\n")
    version_lines = [l for l in lines if l.startswith("Version: ")]
    assert len(version_lines) == 1
    version_line = version_lines.pop()
    version = version_line[len("Version: ") :]
    return version


def clone_arcticdb(tmp_path, version):
    version = "master"  # TODO removeme - working off master till 1.0.2 release done
    git_args = [
        "/apps/research/tools/bin/withproxy",
        "git",
        "clone",
        "--depth",
        "1",
        "--single-branch",
        "-b",
        version,
        "https://github.com/man-group/ArcticDB.git",
        str(tmp_path),
    ]
    print("Running git clone")
    print(" ".join(git_args))
    subprocess.check_call(git_args)


def run_arcticdb_tests(tmp_path) -> int:
    version = get_arcticdb_version()
    clone_arcticdb(tmp_path, version)
    working_dir = os.getcwd()
    try:
        os.chdir(os.path.join(tmp_path, "python"))
        shutil.rmtree("./arcticdb")  # make sure we are testing with the installed one
        subprocess.call(["ls", "-la", "tests/"])
        # TODO relax to run all tests
        tests = os.path.join("tests", "integration", "arcticdb", "test_arctic.py")
        return pytest.main(["-vs", tests])
    finally:
        os.chdir(working_dir)


def test_arcticdb(tmp_path):
    assert run_arcticdb_tests(tmp_path) == 0
