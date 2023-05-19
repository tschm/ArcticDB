import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal
from arcticc.toolbox import loader
from arcticc.util.test import config_context


def test_write_specific_version(lmdb_version_store):
    with config_context("VersionMap.ReloadInterval", 0):
        symbol = "test_write_specific"
        df1 = pd.DataFrame({"x": np.arange(10, dtype=np.int64)})
        version_loader = loader.VersionLoader(lmdb_version_store)
        v1 = version_loader.write_version(symbol, df1, 1)
        df3 = pd.DataFrame({"y": np.arange(10, dtype=np.int32)})
        v3 = version_loader.write_version(symbol, df3, 3)
        vit = lmdb_version_store.read(symbol, 3)
        assert_frame_equal(vit.data, df3)
        vit = lmdb_version_store.read(symbol, 1)
        assert_frame_equal(vit.data, df1)
        # Trying to rewrite already existing version should return earlier versioneditem
        assert v3 == version_loader.write_version(symbol, df3, 3)
        assert v1 == version_loader.write_version(symbol, df1, 1)


def test_write_numpy_array(lmdb_version_store):
    symbol = "test_write_numpy_arr"
    arr = np.random.rand(2, 2, 2)
    lmdb_version_store.write(symbol, arr)

    np.array_equal(arr, lmdb_version_store.read(symbol).data)


def _random_integers(size, dtype):
    # We do not generate integers outside the int64 range
    platform_int_info = np.iinfo("int_")
    iinfo = np.iinfo(dtype)
    return np.random.randint(
        max(iinfo.min, platform_int_info.min), min(iinfo.max, platform_int_info.max), size=size
    ).astype(dtype)


def test_write_ascending_sorted_dataframe(lmdb_version_store):
    symbol = "write_sorted_asc"

    num_initial_rows = 20
    dtidx = np.arange(0, num_initial_rows)
    df = pd.DataFrame(
        {
            "uint8": _random_integers(num_initial_rows, np.uint8),
            "uint32": _random_integers(num_initial_rows, np.uint32),
        },
        index=dtidx,
    )

    lmdb_version_store.write(symbol, df)
    assert df.index.is_monotonic_increasing == True
    info = lmdb_version_store.get_info(symbol)
    assert info["sorted"] == "ASCENDING"


def test_write_descending_sorted_dataframe(lmdb_version_store):
    symbol = "write_sorted_desc"

    num_initial_rows = 20
    dtidx = np.arange(0, num_initial_rows)

    df = pd.DataFrame(
        {
            "uint8": _random_integers(num_initial_rows, np.uint8),
            "uint32": _random_integers(num_initial_rows, np.uint32),
        },
        index=np.flip(dtidx, 0),
    )

    lmdb_version_store.write(symbol, df)
    assert df.index.is_monotonic_decreasing == True
    info = lmdb_version_store.get_info(symbol)
    assert info["sorted"] == "DESCENDING"


def test_write_unsorted_sorted_dataframe(lmdb_version_store):
    symbol = "write_sorted_uns"

    num_initial_rows = 20
    dtidx = np.arange(0, num_initial_rows)

    df = pd.DataFrame(
        {
            "uint8": _random_integers(num_initial_rows, np.uint8),
            "uint32": _random_integers(num_initial_rows, np.uint32),
        },
        index=np.roll(dtidx, 3),
    )

    lmdb_version_store.write(symbol, df)
    assert df.index.is_monotonic_decreasing == False
    assert df.index.is_monotonic_increasing == False
    info = lmdb_version_store.get_info(symbol)
    assert info["sorted"] == "UNSORTED"


def test_write_unknown_sorted_dataframe(lmdb_version_store):
    symbol = "write_sorted_undef"
    lmdb_version_store.write(symbol, 1)
    info = lmdb_version_store.get_info(symbol)
    assert info["sorted"] == "UNKNOWN"
