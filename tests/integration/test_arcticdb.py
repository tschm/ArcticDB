import subprocess
import sys
import os
import shutil
import xml.etree.ElementTree
from typing import Set


def get_arcticdb_version():
    info = subprocess.check_output([sys.executable, "-m", "pip", "show", "arcticdb"])
    lines = info.decode().split("\n")
    version_lines = [l for l in lines if l.startswith("Version: ")]
    assert len(version_lines) == 1
    version_line = version_lines.pop()
    version = version_line[len("Version: ") :]
    return version


def clone_arcticdb(tmp_path, version):
    git_args = [
        "/apps/research/tools/bin/withproxy",
        "git",
        "clone",
        "--depth",
        "1",
        "--single-branch",
        "-b",
        f"v{version}",
        "https://github.com/man-group/ArcticDB.git",
        str(tmp_path),
    ]
    print("Running git clone")
    print(" ".join(git_args))
    subprocess.check_call(git_args)


def check_report(report, ignored_failures: Set[str]):
    print(f"test report: {report}")
    tree = xml.etree.ElementTree.parse(report)
    suite = tree.getroot()
    assert suite.tag == "testsuite"
    failures = []
    for testcase in suite:
        assert testcase.tag == "testcase"
        for results in testcase:
            test_name = f"{testcase.attrib['classname']}:{testcase.attrib['name']}"
            if results.tag == "failure" and test_name not in ignored_failures:
                failures.append(test_name)
                assert test_name in ignored_failures, f"{test_name} failed and is not ignored by IGNORED_FAILURES"
    assert failures == []


IGNORED_FAILURES = {
    "dummy_test:ignored",
    ## Test-only incompatibilities to be addressed by PR #417
    "python.tests.unit.arcticdb.version_store.test_filtering:test_filter_numeric_isnotin_unsigned",
    "python.tests.unit.arcticdb.version_store.test_normalization:test_empty_df"
    ## -- end of issues to be addressed by PR #417
}


def test_arcticdb(tmp_path):
    version = get_arcticdb_version()
    clone_arcticdb(tmp_path, version)
    working_dir = os.getcwd()

    try:
        os.chdir(os.path.join(tmp_path, "python"))
        print("Running tests from dir: " + os.getcwd())
        shutil.rmtree("./arcticdb")
        shutil.rmtree("./arcticc")
        subprocess.call(["ls", "-la", "tests/"])
        if subprocess.call(["pytest", "-vs", "--junitxml", "report.xml", "tests/"]) != 0:
            check_report(os.path.join(tmp_path, "python", "report.xml"), IGNORED_FAILURES)
    finally:
        os.chdir(working_dir)
