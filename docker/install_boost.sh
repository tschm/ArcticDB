#!/bin/bash

mkdir /tmp/boost_bootstrap
pushd /tmp/boost_bootstrap

git init .

git submodule add https://github.com/Orphis/boost-cmake.git
