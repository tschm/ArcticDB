import os
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


class ProtobufFiles(object):
    def __init__(
        self,
        include_dir="cpp/proto",  # -I
        python_out_dir="python",  # --python_out
        grpc_out_dir=None,  # --grpc_python_out
        sources=[],  # arguments of proto
    ):
        self.include_dir = include_dir
        self.sources = sources
        self.python_out_dir = python_out_dir
        self.grpc_out_dir = grpc_out_dir

    def compile(self):
        # import deferred here to avoid blocking installation of dependencies
        cmd = ["-mgrpc_tools.protoc"]

        cmd.append("-I{}".format(self.include_dir))

        cmd.append("--python_out={}".format(self.python_out_dir))
        if self.grpc_out_dir:
            cmd.append("--grpc_python_out={}".format(self.grpc_out_dir))

        cmd.extend(self.sources)

        cmd_shell = "{} {}".format(sys.executable, " ".join(cmd))
        print('Running "{}"'.format(cmd_shell))
        for line in subprocess.check_output(cmd_shell, shell=True, stderr=subprocess.STDOUT):
            print("ProtobufFiles: ", line)


proto_files = ProtobufFiles(sources=["cpp/proto/arcticc/pb2/*.proto"])


def compile_protos():
    print("\nProtoc compilation")
    proto_files.compile()
    if not os.path.exists("python/arcticc"):
        raise RuntimeError("Unable to locate Protobuf module during compilation.")
    else:
        open("python/arcticc/__init__.py", "a").close()
        open("python/arcticc/pb2/__init__.py", "a").close()


class CompileProto(Command):
    description = '"protoc" generate code _pb2.py from .proto files'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        compile_protos()


class CompileProtoAndBuild(build_py):
    def run(self):
        compile_protos()
        build_py.run(self)


class DevelopAndCompileProto(develop):
    def run(self):
        develop.run(self)
        compile_protos()  # compile after updating the deps
        if not os.path.islink("python/arcticdb_ext.so") and os.path.exists("python"):
            print("Creating symlink for compiled arcticdb module in python...")
            os.symlink("../arcticdb_ext.so", "python/arcticdb_ext.so")


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=""):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        p = pathlib.Path(__file__).parent.resolve().parent
        try:
            subprocess.check_output([os.path.join(p, "docker/run.sh"), "uptime"], stderr=subprocess.STDOUT)
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
        # we only realistically support these two versions
        import sys

        v_info = sys.version_info
        if v_info >= (3, 8):
            version = "38"
        elif v_info > (3, 6, 6):
            version = "36"
        else:
            version = "medusa"
        print("version is {}".format(version))

        is_jenkins = os.getenv("JENKINS_URL") is not None and os.getenv("WORKSPACE") is not None
        is_man_build = os.getenv("MB_SETUP_PY")

        so_file = "{}.so".format(ext.name)
        toolbox_so_file = "{}_toolbox.so".format(ext.name)
        so_files_built = all([osp.exists(osp.join(extdir, f)) for f in [so_file, toolbox_so_file]])

        if (is_jenkins or is_man_build) and so_files_built:
            # skip rebuild in jenkins or man_build, which run through this code multiple times
            # (first develop, then bdist_egg (twice))
            return

        cores_count = 12
        print("cores_count is ", cores_count)
        self.run_docker(version, extdir, cores_count)

        for f in [so_file, toolbox_so_file]:
            try:
                os.remove(f)
            except:
                pass

            if not osp.exists(f):
                extension_file = osp.join(extdir, f)
                if not osp.exists(extension_file):
                    # TODO: This'll need to be adaptable to Pegasus/non3.6
                    py_version = "3.8" if version == "38" else "3.6"
                    extension = osp.join(extdir, "build/lib.linux-x86_64-{}".format(py_version), f)
                else:
                    extension = osp.join(extdir, f)

                print(f"Symlinking from '{extension}' to {f}")
                os.symlink(extension, f)

    def run_docker(self, version, extdir, cores_count):
        if os.environ.get("NO_DOCKER_BUILD"):
            return

        if "--python-tag" in sys.argv:
            tag = sys.argv[sys.argv.index("--python-tag") + 1]
            python_version = tag[2] + "." + tag[3:]

            p = pathlib.Path(__file__).parent.resolve().parent
            subprocess.check_call(
                [
                    os.path.join(p, "docker/run.sh"),
                    version,
                    "external",
                    "/opt/arcticc/docker/build.py",
                    "--bdir",
                    extdir,
                    "--version",
                    "medusa",
                    "--python-version",
                    python_version,
                    "--cores",
                    "{:d}".format(cores_count),
                    "--cython-path",
                    "arcticc_cython",
                    "--no-ssl",
                    "--no-tests",
                    "--hide-linked-symbols",
                    "--external-release",
                ]
            )
        else:
            raise ValueError("Must set --python-tag")

if __name__ == "__main__":
    try:
        p = pathlib.Path(__file__).parent.resolve().parent
        os.chdir(os.path.join(p, "arcticdb_link"))
        result = setup(
            ext_modules=[CMakeExtension("arcticdb_ext")],
            package_dir={"": "python"},
            packages=find_packages(where="python", exclude=["tests", "tests.*"]),
            cmdclass=dict(
                build_ext=CMakeBuild,
                protoc=CompileProto,
                build_py=CompileProtoAndBuild,
                bdist_wheel=bdist_wheel,
                develop=DevelopAndCompileProto,
            ),
            zip_safe=False,
        )
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        raise e
