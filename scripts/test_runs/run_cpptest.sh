#!/bin/bash

set -eux

export LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-}:/opt/man/releases/python-medusa/36-1/lib:/default-pegasus-venv/lib

catchsegv cpp/tests/test_unit_arcticcxx --gtest_output=xml:gtest-cpp.xml --gtest_filter=-Server.*

python3 scripts/test_runs/gtesttojunit.py  "suitename"  "cppunit"  gtest-cpp.xml  junit-cpp.xml