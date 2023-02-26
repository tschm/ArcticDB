from ahl.mongo.mongoose import NativeMongoose
from arcticcxx.tools import StorageMover
from man.arctic.config import NativeMongooseConfigHelper
from arcticc.pb2.lmdb_storage_pb2 import Config as LmdbConfig
from arcticc.pb_util import ARCTIC_NATIVE_PROTO_TYPE_URL
import argparse
import sys
import math
from itertools import islice

import ahl.spark.yarn
from ahl.mongo.mongoose.mongoose import PyMongoose, NativeMongoose

import signal


def signal_handler(signal, frame):
    print("exiting")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def format_bytes(num, suffix="b"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1000.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, "Yi", suffix)


def get_backup_name(library):
    return "{}_zfs_backup".format(library)


def initialize_backup_lib(
    library,
    host,
    credential_name="PSFBIAZFADAALHJI",
    credential_key="C28600030+42b4914D8E1df3ce72e/HALLFDLLFJACFPLF",
    bucket="arctic-dev-backup",
    endpoint="s3.prod.m",
):
    nm = NativeMongoose(host)
    backup_name = get_backup_name(library)
    nm.initialize_s3_library(
        library=backup_name,
        credential_name=credential_name,
        credential_key=credential_key,
        bucket=bucket,
        endpoint=endpoint,
    )

    return backup_name


def create_spark_context(executor_memory):
    sc, ss = ahl.spark.yarn.create_context(
        conf_dict={
            "spark.app.name": "arcticnative_migrator",
            "spark.driver.memory": "20g",  # tune this
            "spark.driver.maxResultSize": "50g",
            "spark.executor.memory": executor_memory,  # tune this
            "spark.executor.cores": "1",
            # Read "Understanding `spark.executor.cores` and `spark.task.cpus` when using Python on YARN" below -- this doesn    't do what you think it does
            "spark.task.cpus": "1",
            # Read "Understanding `spark.executor.cores` and `spark.task.cpus` when using Python on YARN" below -- this doesn    't do what you think it does
            "spark.dynamicAllocation.maxExecutors": "100",  # tune this (must be a string!) (omit for no limit)
            # Add any other upstream setting here -- see https://spark.apache.org/docs/2.3.3/configuration.html
            # Limit scope of AN memory leaks by preventing worker reuse across tasks, temporary fix until those are resolved
            "spark.python.worker.reuse": "false",
        }
    )
    return sc


def chunker(it, size):
    # Cribbed from https://stackoverflow.com/a/22045226
    if type(it) == dict:
        it = iter(it.items())
    else:
        it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


def chunk_keys(keys, target_chunks=1000, max_keys_per_chunk=10):
    # Determine if we should process multiple keys together. At most, we will put 10 keys per chunk.
    keys_per_chunk = min(max_keys_per_chunk, max(1, int(math.ceil(float(len(keys)) / target_chunks))))
    return list(chunker(keys, keys_per_chunk))


def do_write(chunk, host, library):
    try:
        nm = NativeMongoose(host)
        src = nm.get_library(library)
        backup_name = get_backup_name(library)
        dst = nm.get_library(backup_name)
        mover = StorageMover(src._library, dst._library)
        mover.write_keys_from_source_to_target(chunk, 1000)
    except Exception as e:
        return [str(e)]

    return []


def do_backup(library, host):
    nm = NativeMongoose(host)
    src = nm.get_library(library)
    backup_name = get_backup_name(library)
    dst = nm.get_library(backup_name)
    mover = StorageMover(src._library, dst._library)
    keys = mover.get_all_source_keys()

    chunks = chunk_keys(keys, target_chunks=1000, max_keys_per_chunk=26000)
    sc = create_spark_context("10g")
    work = sc.parallelize(chunks, numSlices=len(chunks)).flatMap(lambda chunk: do_write(chunk, host, library)).collect()
    print(work)


# TODO: till cached lib sizes change is merged
def get_library_cached_size_and_count(lib_name):
    mp = PyMongoose("research", app_name="admin")
    read_collection = mp._conn["arctic_native_config"]["arcticc_lib_metadata"]
    doc = read_collection.find_one({"library": lib_name})
    if not doc:
        return NativeMongoose("research").get_library_size_and_count(lib_name)
    return doc["size"], doc["items"]


def backup_library_to_s3(library, host):
    size, count = get_library_cached_size_and_count(library)
    backup_library = initialize_backup_lib(library, host)
    print("Backing up {} with {} objects, {} to {}".format(library, count, format_bytes(size), backup_library))

    do_backup(library, host)


def main():
    parser = argparse.ArgumentParser(usage=__doc__)

    parser.add_argument("--host", required=True, help="The environment to read from")
    parser.add_argument("--library", required=True, help="The library_name")

    opts = parser.parse_args()
    backup_library_to_s3(opts.library, opts.host)


if __name__ == "__main__":
    sys.exit(main())
