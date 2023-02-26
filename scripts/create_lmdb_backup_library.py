from ahl.mongo.mongoose import NativeMongoose
from arcticcxx.tools import StorageMover
from man.arctic.config import NativeMongooseConfigHelper
from arcticc.pb2.lmdb_storage_pb2 import Config as LmdbConfig
from arcticc.pb_util import ARCTIC_NATIVE_PROTO_TYPE_URL
import argparse
import sys

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


def initialize_backup_lib(library, host, path, dry_run):
    nm = NativeMongoose(host)
    backup_name = get_backup_name(library)
    if not dry_run:
        nm.initialize_lmdb_library(library=backup_name, path=path)

    return backup_name


def set_lmdb_map_size(library, host, map_size):
    config_helper = NativeMongooseConfigHelper(host)
    config_reader = config_helper.get_config_reader()
    cfg, open_mode = config_reader.get_lib_config_and_open_mode(library)
    storage_id = cfg.lib_desc.storage_ids[0]
    lmdb_config = LmdbConfig()
    storage_cfg = cfg.storage_by_id[storage_id].config
    storage_cfg.Unpack(lmdb_config)
    lmdb_config.map_size = map_size
    cfg.storage_by_id[storage_id].config.Pack(lmdb_config, type_url_prefix=ARCTIC_NATIVE_PROTO_TYPE_URL)
    config_writer = config_helper.get_config_writer()
    config_writer.modify_storage_config(library, cfg)


def adjust_map_size(size, library, host, dry_run=False):
    default_map_size = (4 << 30) * 100
    headroom = size / 5

    if size + headroom > default_map_size:
        new_map_size = size + headroom
        print("Adjusting LMDB map size to {}".format(format_bytes(new_map_size)))
        if not dry_run:
            set_lmdb_map_size(library, host, int(new_map_size))
    else:
        print("Using default map size")


def do_backup(library, host):
    nm = NativeMongoose(host)
    src = nm.get_library(library)
    backup_name = get_backup_name(library)
    dst = nm.get_library(backup_name)
    mover = StorageMover(src._library, dst._library)
    mover.go(200)


# TODO: till cached lib sizes change is merged
def get_library_cached_size_and_count(lib_name):
    mp = PyMongoose("research", app_name="admin")
    read_collection = mp._conn["arctic_native_config"]["arcticc_lib_metadata"]
    doc = read_collection.find_one({"library": lib_name})
    if not doc:
        return NativeMongoose("research").get_library_size_and_count(lib_name)
    return doc["size"], doc["items"]


def backup_library_to_lmdb(library, host, path, dry_run=True):
    size, count = get_library_cached_size_and_count(library)
    backup_library = initialize_backup_lib(library, host, path, dry_run)
    print("Backing up {} with {} objects, {} to {}".format(library, count, format_bytes(size), backup_library))
    adjust_map_size(size, backup_library, host, dry_run)

    if not dry_run:
        do_backup(library, host)


def main():
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("--dry-run", required=False, default=False, action="store_true")

    parser.add_argument("--host", required=True, help="The environment to read from")
    parser.add_argument("--library", required=True, help="The library_name")
    parser.add_argument("--path", required=False, default="/slowman/arcticnative")

    opts = parser.parse_args()
    backup_library_to_lmdb(opts.library, opts.host, opts.path, opts.dry_run)


if __name__ == "__main__":
    sys.exit(main())
