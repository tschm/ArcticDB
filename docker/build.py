#!/usr/bin/env python

import argparse
import os
import os.path as osp
import subprocess
from multiprocessing import cpu_count

parser = argparse.ArgumentParser()
parser.add_argument("--bdir", default="build")
parser.add_argument("--version", default="36")
parser.add_argument("--python-version", default=None,
                    help='If set, will be built against standard Python release rather than Medusa, '
                         'and not linked against libpython.')
parser.add_argument("--cores", default="{:d}".format(cpu_count()), type=int)
parser.add_argument("--cython-path", default=None, help='If set, will build Cython-compiled code at given path.')
parser.add_argument("--no-ssl", action='store_true', help='If set, binary will not link against ssl/sasl2')
parser.add_argument("--no-tests", action='store_true', help='If set, tests will not be built')
parser.add_argument("--dynamic-link-std-lib", action='store_true', help='If set, C++ libs will be dynamically linked')
parser.add_argument("--strip", action='store_true', help='Strip builds of all symbols')
parser.add_argument("--hide-linked-symbols", action='store_true', help='Hides linked library symbols (--exclude-libs in linker)')
parser.add_argument("--external-release", action='store_true', help='Builds the C++ code with the flags needed for an external release')
args = parser.parse_args()




if args.python_version:
    python_root_dir = "/opt/pythons/{}.0".format(args.python_version)
    base_path = osp.join(python_root_dir, "install")

    lib_path = osp.join(base_path, "lib")
    python_version = args.python_version
    include_path = osp.join(base_path, "include", "python{}m".format(python_version))
    python_lib_path = ""  # No reason to link against libpython
    python_lib_dir = ""
else:
    python_root_dir = "/default-pegasus-venv" if args.version != "medusa" else "/opt/man/releases/python-medusa/36-1"
    base_path = python_root_dir

    lib_path = osp.join(base_path, "lib")

    python_version = "3.8" if args.version == "38" else "3.6"

    # The include path in python3.8 is different - does not have "m" in the end (lol)
    include_path = osp.join(base_path, "include", "python{}{}".format(python_version, "" if python_version == "3.8" else "m"))
    python_lib_path = osp.join(lib_path, "libpython{}{}.so".format(python_version, "" if python_version == "3.8" else "m"))
    python_lib_dir = lib_path

build_dir = "/tmp/build"
dest_build_dir = "/opt/arcticc/{}".format(args.bdir)
expected_artifacts = ["arcticcxx/arcticcxx.so"]

if not osp.exists(build_dir):
    os.makedirs(build_dir, mode=0o750)
if not osp.exists(dest_build_dir):
    os.makedirs(dest_build_dir, mode=0o750)
for tgt in expected_artifacts:
    f = osp.join(dest_build_dir, osp.split(tgt)[1])
    if osp.exists(f):
        os.remove(f)


cwd = os.getcwd()
try:
    env = {
        "TERM": "linux",  # to get colors
        "PATH": "/opt/gcc/8.2.0/bin:/opt/cmake/bin:/usr/bin:/usr/local/bin:/bin:/sbin:/usr/sbin:/usr/local/sbin",
        "CXX": "/opt/gcc/8.2.0/bin/g++",
        "CC": "/opt/gcc/8.2.0/bin/gcc",
        "CMAKE_ROOT": "/opt/cmake/share/cmake-3.12",
    }
    if os.getenv("DEBUG_BUILD"):
        env["DEBUG_BUILD"] = "True"
    if os.getenv("USE_SLAB_ALLOCATOR"):
        env["USE_SLAB_ALLOCATOR"] = "True"
    if os.getenv("CMAKE_BUILD_TYPE"):
        env["CMAKE_BUILD_TYPE"] = os.getenv("CMAKE_BUILD_TYPE")

    additional_options = [
        "-DBUILD_CYTHON=YES",
        "-DBUILD_CYTHON_PATH={}".format(args.cython_path)
    ] if args.cython_path else []
    if args.no_ssl:
        additional_options += [
            '-DSSL_LINK=OFF'
        ]
    if args.no_tests:
        additional_options += [
            '-DTEST=OFF'
        ]
    if args.strip:
        additional_options += [
            '-DSTRIP_BUILDS=ON'
        ]
    if args.hide_linked_symbols:
        additional_options += [
            '-DHIDE_LINKED_SYMBOLS=ON'
        ]
    if args.external_release:
        additional_options += [
            '-DEXTERNAL_RELEASE=ON'
        ]
    if args.dynamic_link_std_lib:
        additional_options += [
            '-DSTATIC_LINK_STD_LIB=OFF'
        ]

    process_args = [
        "cmake",
        "-DPYBIND11_FINDPYTHON=ON",
        "-DPython_ROOT_DIR={}".format(python_root_dir),
        "-DPYTHON_LIBRARIES={}".format(lib_path),
        "-DPYTHON_INCLUDE_DIRS={}".format(include_path),
        "-DBUILD_PYTHON_VERSION={}".format(python_version),
        "-DPYTHON_LIBRARY_SO={}".format(python_lib_path),
    ] + additional_options + [
        "/opt/arcticc/arcticdb_link/cpp",
    ]

    os.chdir(build_dir)
    subprocess.check_call(process_args, env=env)
    subprocess.check_call(["make", "-j", "{:d}".format(args.cores), "install"], env=env)
finally:
    os.chdir(cwd)
