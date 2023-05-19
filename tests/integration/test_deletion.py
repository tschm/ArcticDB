from __future__ import print_function

import sys

import numpy as np
import pandas as pd
import pytest
from arcticc.config import Defaults
from arcticc.version_store.helper import ArcticcMemConf
from arcticc.flattener import Flattener
from arcticcxx.storage import KeyType, NoDataFoundException
from pandas.testing import assert_frame_equal
import pandas.util.testing as tm
import random
from itertools import product
from arcticc.util.test import config_context
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arcticc.version_store import NativeVersionStore


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def comp_dict(d1, d2):
    assert len(d1) == len(d2)
    for k in d1:
        if isinstance(d1[k], np.ndarray):
            assert (d1[k] == d2[k]).all()
        else:
            assert d1[k] == d2[k]


SECOND = 1000000000


def get_map_timeouts():
    return [0, SECOND * 5, SECOND * 10000]


def gen_params_store_and_timeout():
    p = [["mongo_version_store", "s3_version_store"], get_map_timeouts()]
    return list(product(*p))


@pytest.mark.parametrize("lib_type, map_timeout", gen_params_store_and_timeout())
def test_delete_all(lib_type, map_timeout, sym, request):
    with config_context("VersionMap.ReloadInterval", map_timeout):
        lib = request.getfixturevalue(lib_type)
        symbol = sym
        df1 = pd.DataFrame({"x": np.arange(10, dtype=np.int64)})
        lib.write(symbol, df1)
        df2 = pd.DataFrame({"y": np.arange(10, dtype=np.int32)})
        lib.write(symbol, df2)
        df3 = pd.DataFrame({"z": np.arange(10, dtype=np.uint64)})
        lib.write(symbol, df3)
        vit = lib.read(symbol)
        assert_frame_equal(vit.data, df3)
        lib.delete(symbol)
        assert lib.has_symbol(symbol) is False
        lib.write(symbol, df2)
        vit = lib.read(symbol)
        assert_frame_equal(vit.data, df2)
        lib.write(symbol, df1)
        vit = lib.read(symbol)
        assert_frame_equal(vit.data, df1)


def test_version_missing(mongo_version_store):
    with pytest.raises(NoDataFoundException):
        mongo_version_store.read("not_there")


def test_delete_mixed(mongo_version_store, sym):
    symbol = sym
    df1 = pd.DataFrame({"x": np.arange(10, dtype=np.int64)})
    mongo_version_store.write(symbol, df1)
    df2 = pd.DataFrame({"y": np.arange(10, dtype=np.int32)})
    mongo_version_store.write(symbol, df2)
    df3 = pd.DataFrame({"z": np.arange(10, dtype=np.uint64)})
    mongo_version_store.write(symbol, df3)
    vit = mongo_version_store.read(symbol)
    assert_frame_equal(vit.data, df3)
    mongo_version_store.delete(symbol)
    assert mongo_version_store.has_symbol(symbol) is False


def tests_with_pruning_and_tombstones(lmdb_version_store_tombstone_and_pruning, sym):
    symbol = sym
    lib = lmdb_version_store_tombstone_and_pruning

    df1 = pd.DataFrame({"x": np.arange(10, dtype=np.int64)})
    lib.write(symbol, df1)
    df2 = pd.DataFrame({"y": np.arange(10, dtype=np.int32)})
    lib.write(symbol, df2)
    df3 = pd.DataFrame({"z": np.arange(10, dtype=np.uint64)})
    lib.write(symbol, df3)
    vit = lib.read(symbol)
    assert_frame_equal(vit.data, df3)
    lib.delete(symbol)
    assert lib.has_symbol(symbol) is False


@pytest.mark.parametrize("map_timeout", get_map_timeouts())
def test_with_snapshot_pruning_tombstones(lmdb_version_store_delayed_deletes_with_pruning_tombstones, map_timeout, sym):
    with config_context("VersionMap.ReloadInterval", map_timeout):
        symbol = sym
        lib = lmdb_version_store_delayed_deletes_with_pruning_tombstones

        df1 = pd.DataFrame({"x": np.arange(10, dtype=np.int64)})
        lib.write(symbol, df1)
        lib.snapshot("delete_version_snap_1")

        df2 = pd.DataFrame({"y": np.arange(10, dtype=np.int32)})
        lib.write(symbol, df2)
        lib.snapshot("delete_version_snap_2")

        df3 = pd.DataFrame({"z": np.arange(10, dtype=np.uint64)})
        lib.write(symbol, df3)
        vit = lib.read(symbol)
        assert_frame_equal(vit.data, df3)

        # pruning enabled
        assert len([ver for ver in lib.list_versions() if not ver["deleted"]]) == 1

        assert_frame_equal(lib.read(symbol, "delete_version_snap_2").data, df2)
        # with pytest.raises(NoDataFoundException):
        # This won't raise anymore as it's in delete_version_snap_2
        lib.read(symbol, 1)

        assert_frame_equal(lib.read(symbol, "delete_version_snap_1").data, df1)
        # with pytest.raises(NoDataFoundException):
        # Won't raise as in snapshot
        lib.read(symbol, 0)


@pytest.mark.parametrize("map_timeout", get_map_timeouts())
def test_normal_flow_with_snapshot_and_pruning(lmdb_version_store_tombstone_and_pruning, map_timeout, sym):
    with config_context("VersionMap.ReloadInterval", map_timeout):
        symbol = sym
        lib = lmdb_version_store_tombstone_and_pruning

        lib_tool = lmdb_version_store_tombstone_and_pruning.library_tool()
        lib.write("sym1", 1)
        lib.write("sym2", 1)

        lib.snapshot("snap1")

        lib.write("sym1", 2)
        lib.write("sym1", 3)
        lib.delete("sym1")
        with pytest.raises(NoDataFoundException):
            lib.read(symbol, 0)
        assert lib.read("sym1", as_of="snap1").data == 1

        assert len([ver for ver in lib.list_versions() if not ver["deleted"]]) == 1

        version_keys = lib_tool.find_keys(KeyType.VERSION)
        keys_for_a = [k for k in version_keys if k.id == "sym1"]
        assert len(keys_for_a) == 3 * 2  # 2 keys for the number of writes

        lib.write("sym1", 4)
        assert len([ver for ver in lib.list_versions() if not ver["deleted"]]) == 2
