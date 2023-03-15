import os
import shutil
import os.path as osp
import subprocess
import sys
import pathlib
import traceback
from distutils.core import Command
from setuptools import setup
from setuptools import Extension, find_packages
from setuptools.command.build_ext import build_ext
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
from wheel.bdist_wheel import bdist_wheel


ARCHIVE = None
ARCHIVE_PATH = None

BASE_DIRECTORY=pathlib.Path(__file__).parent.resolve().parent
print("BASE_DIRECTORY: ", BASE_DIRECTORY)


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=""):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        try:
            subprocess.check_output([os.path.join(BASE_DIRECTORY, "docker/run.sh"), "uptime"], stderr=subprocess.STDOUT, cwd=BASE_DIRECTORY)
        except OSError:
            raise RuntimeError("You default docker build parameter are incorrect. See docker.run.sh")
        except subprocess.CalledProcessError as e:
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        extdir = os.path.dirname(self.get_ext_fullpath(ext.name))
        print("extdir is {}".format(extdir))
        print(ext.name)
        print(extdir)
        print(self.build_temp)

        v_info = sys.version_info
        if v_info >= (3, 8):
            version = "38"
        elif v_info > (3, 6, 6):
            version = "36"
        else:
            version = "medusa"

        print("version is {}".format(version))
        so_file = "arcticdb_ext.so"

        cores_count = 12
        print("cores_count is ", cores_count)
        self.run_docker(version, extdir, cores_count)

        try:
            os.remove(so_file)
        except:
            pass

        extension_file = osp.join(extdir, so_file)
        extension = osp.join(extdir, so_file)
        print(f"Symlinking from '{extension}' to {so_file}")
        os.symlink(extension, so_file)

        if ARCHIVE:
            print(f"Archiving extension with debug symbols to {ARCHIVE_PATH}")
            shutil.copy(so_file, ARCHIVE_PATH)
            assert os.path.isfile(os.path.join(ARCHIVE_PATH, so_file))

        if os.environ.get("NO_STRIP_SYMBOLS", "False").lower() in ('true', '1'):
            print("WARNING - Skipping symbol stripping due to NO_STRIP_SYMBOLS env var")
            return
        print("Stripping symbols")
        subprocess.check_call(["/usr/bin/strip", "-s", extension])


    def run_docker(self, version, extdir, cores_count):
        if os.environ.get("NO_DOCKER_BUILD", "False").lower() in ('true', '1'):
            print("WARNING - Skipping Docker build due to NO_DOCKER_BUILD env var")
            return

        print("Running Docker build")
        if "--python-tag" in sys.argv:
            tag = sys.argv[sys.argv.index("--python-tag") + 1]
            python_version = tag[2] + "." + tag[3:]

            subprocess.check_call(
                [
                    os.path.join(BASE_DIRECTORY, "docker/run.sh"),
                    version,
                    "external",
                    "/opt/arcticdb/docker/build.py",
                    "--bdir",
                    extdir,
                    "--version",
                    "medusa",
                    "--python-version",
                    python_version,
                    "--cores",
                    "{:d}".format(cores_count),
                    "--no-ssl",
                    "--no-tests",
                    "--hide-linked-symbols",
                ]
            )
        else:
            raise ValueError("Must set --python-tag")


# Defining the below allows us to avoid depending on the AHL setuptools extensions for builds.
# Newer versions of setuptools obviously can parse the .cfg as well, but the version we use internally is old enough
# that we rely on our own code to do the parsing.
import configparser
from distutils.command.build import build as _build
cfg = configparser.ConfigParser()
p = pathlib.Path(__file__).parent.resolve().parent
cfg.read(os.path.join(p, "arcticdb_link", "setup.cfg"))

config = {k: [_v for _v in v.split("\n") if _v] for k, v in cfg["metadata"].items()}
config = {k: (v[0] if len(v) == 1 else v) for k, v in config.items()}

from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

if "--python-tag" in sys.argv:
    tag = sys.argv[sys.argv.index("--python-tag") + 1]
    if tag not in ("cp36", "cp37", "cp38", "cp39", "cp310"):
        raise ValueError("Only supported python tags are cp36, cp37, cp38, cp39 and cp310.")

    class bdist_wheel(_bdist_wheel):
        user_options = _bdist_wheel.user_options + [
            ("archive=", None, "If set (--archive=1), will archive non-stripped binaries to `archive_path`"),
            ("archive-path=", None, "Path to archive non-stripped binaries to. "
                                    "Under this path, a new directory will be created for the version. ")
        ]

        def initialize_options(self):
            ret = _bdist_wheel.initialize_options(self)
            self.archive = False
            self.archive_path = None
            return ret

        def finalize_options(self):
            global ARCHIVE_PATH, ARCHIVE
            ret = _bdist_wheel.finalize_options(self)
            ARCHIVE = self.archive
            if ARCHIVE:
                python, abi, plat = self.get_tag()
                ARCHIVE_PATH = os.path.join(self.archive_path, config["version"], python, abi, plat)
                os.makedirs(ARCHIVE_PATH, exist_ok=True)
            return ret

        def get_tag(self):
            python, abi, plat = _bdist_wheel.get_tag(self)
            tag_suffix = "m" if int(tag.split("cp")[1]) < 38 else ""
            return tag, tag + tag_suffix, plat

        def run(self):
            print(f"self.bdist_dir=[{self.bdist_dir}]")
            if self.bdist_dir.startswith('build/') or self.bdist_dir.startswith('build\\'):  # just in case self.bdist_dir is somehow '/'...
                print(f"Removing {self.bdist_dir}")
                shutil.rmtree(self.bdist_dir, ignore_errors=True)

            return _bdist_wheel.run(self)

    class build(_build):
        def finalize_options(self):
            super(build, self).finalize_options()

            self.build_lib = self.build_lib[:-3] + tag[2:].replace("3", "3.", 1)  # cp38 -> 3.8
            shutil.rmtree(self.build_lib, ignore_errors=True)
else:
    raise ValueError("Must include --python-tag in build arguments. "
                     "Valid options are cp36, cp37, cp38, cp39, cp310.")


def readme():
    with open("arcticdb_link/README.md") as f:
        return f.read()

if __name__ == "__main__":
    result = setup(
        ext_modules=[CMakeExtension("arcticdb_ext")],
        package_dir={"": "arcticdb_link/python"},
        packages=find_packages(where="arcticdb_link/python", exclude=["tests", "tests.*"]),
        package_data={'arcticdb': ['NOTICE.txt']},
        long_description=readme(),
        cmdclass=dict(
            build_ext=CMakeBuild,
            bdist_wheel=bdist_wheel,
            build=build,
        ),
        zip_safe=False,
        **config
    )
