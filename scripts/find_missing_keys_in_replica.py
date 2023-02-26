import argparse
import sys

sys.path.append("/opt/arcticc")

from ahl.mongo.mongoose import NativeMongoose
from arcticcxx.tools import StorageMover


def get_backup_name(library):
    return "{}_s3_backup".format(library)


def get_library_cached_size_and_count(lib_name):
    from ahl.mongo.mongoose.mongoose import PyMongoose, NativeMongoose

    mp = PyMongoose("research", app_name="admin")
    read_collection = mp._conn["arctic_native_config"]["arcticc_lib_metadata"]
    metadata = read_collection.find_one({"library": lib_name})
    return metadata["size"], metadata["items"]


def find_missing_keys(host, library, backup):
    nm = NativeMongoose(host)
    src = nm.get_library(library)
    _, count = get_library_cached_size_and_count(library)
    print("Comparing library {} with {} objects to {}".format(library, count, backup))
    dst = nm.get_library(backup)
    mover = StorageMover(src._library, dst._library)
    return mover.get_keys_in_source_only()


def main():
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("--host", required=True, help="The environment to read from")
    parser.add_argument("--library", required=True, help="The library name")
    parser.add_argument("--backup", required=False, default=None, help="The backup  library name")

    opts = parser.parse_args()
    backup = opts.backup if opts.backup is not None else get_backup_name(opts.library)

    missing = find_missing_keys(opts.host, opts.library, backup)
    for key in missing:
        print(key)


if __name__ == "__main__":
    sys.exit(main())
