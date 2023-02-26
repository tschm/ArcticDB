import arcticc

from ahl.mongo import NativeMongoose
from .key_fixers import *

print(arcticc)

src = NativeMongoose("mktdatad")["qchen.test"]
dst = NativeMongoose("research")["qchen.test"]

sym = "an-504"


def dump(lib):
    print(f"============================\nDumping {lib.connection_string_with_host}")
    lt = get_library_tool(lib)
    for v in lib.list_versions():
        print(v)
    for kt in (KeyType.VERSION, KeyType.TABLE_INDEX, KeyType.TABLE_DATA):
        print("========", kt, "==========")
        keys = lt.find_keys(kt)
        keys.sort(key=lambda k: k.creation_ts)
        for key in keys:
            print(key)
            if kt == KeyType.TABLE_INDEX:
                print("    ", str(key_to_df(lt, key)).replace("\n", "\n    "))


def setup():
    src.version_store.clear()
    for i in range(11):
        src.write(sym, i, prune_previous_version=True)
        # if i not in (0, 4, 49):
        #     src.delete_version(sym, i - 1)
        if i in (3, 5):
            src.snapshot(f"s{i}")
    # src.version_store._delete_tombstones(False, 0, 1000)
    dump(src)


def copy():
    dst.version_store.clear()
    args = "mongoose_copy_data.py --src qchen.test@mktdatad --dest qchen.test@research --log CR0 --native --all-snapshots --latest --force".split()
    args.append(sym)
    print("Running", args)

    import unittest.mock as mock
    from ahl.mongo.mongoose.scripts.mongoose_copy_data import main

    with mock.patch("sys.argv", args):
        main()


# setup()
# copy()
# dump(dst)


# lib = NativeMongoose("mktdatad")["mmitalidis.ICE_PRIMARY_dynamic_schema3"]
# fix_lib(lib, {"index_map": {4}})
