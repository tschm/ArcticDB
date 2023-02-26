#!/bin/bash

set -eux

export LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-}:/opt/man/releases/python-medusa/36-1/lib:/default-pegasus-venv/lib

catchsegv tests/cpp/arcticcxx_rapidcheck_tests --gtest_output=xml:gtest-rapidcheck.xml

python3 scripts/test_runs/gtesttojunit.py  "suitename"  "cpprapidcheck"  gtest-rapidcheck.xml  junit-rapidcheck.xml