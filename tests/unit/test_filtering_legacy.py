import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from datetime import datetime, timedelta


def test_fixed_string_column_filtering(lmdb_version_store):
    idx1 = np.arange(0, 5)
    strs = np.array(["zero", "one", "two", "three", "four"])
    d1 = {
        "x": np.arange(10, 15, dtype=np.int64),
        "y": np.arange(20, 25, dtype=np.int64),
        "s": strs,
        "z": np.arange(30, 35, dtype=np.int64),
    }
    df3 = pd.DataFrame(data=d1, index=idx1)
    lmdb_version_store.write("strings", df3)
    vit = lmdb_version_store.read("strings", columns=["index", "x", "s"])
    expected = pd.DataFrame({"x": np.arange(10, 15, dtype=np.int64), "s": strs}, index=idx1)
    assert_frame_equal(vit.data, expected)


def test_fixed_string_column_filtering_ts_index(lmdb_version_store):
    idx1 = [pd.Timestamp(x * 1000) for x in np.arange(0, 5)]
    strs = np.array(["zero", "one", "two", "three", "four"])
    d1 = {
        "x": np.arange(10, 15, dtype=np.int64),
        "y": np.arange(20, 25, dtype=np.int64),
        "s": strs,
        "z": np.arange(30, 35, dtype=np.int64),
    }
    df3 = pd.DataFrame(data=d1, index=idx1)
    lmdb_version_store.write("strings", df3)
    vit = lmdb_version_store.read("strings", columns=["index", "x", "s"])
    expected = pd.DataFrame({"x": np.arange(10, 15, dtype=np.int64), "s": strs}, index=idx1)
    assert_frame_equal(vit.data, expected)


def test_fixed_string_column_filtering_small_segment(lmdb_version_store_tiny_segment):
    idx1 = np.arange(0, 5)
    strs = np.array(["zero", "one", "two", "three", "four"])
    d1 = {
        "x": np.arange(10, 15, dtype=np.int64),
        "y": np.arange(20, 25, dtype=np.int64),
        "s": strs,
        "z": np.arange(30, 35, dtype=np.int64),
    }
    df3 = pd.DataFrame(data=d1, index=idx1)
    lmdb_version_store_tiny_segment.write("strings", df3)
    vit = lmdb_version_store_tiny_segment.read("strings", columns=["index", "x", "s"])
    expected = pd.DataFrame({"x": np.arange(10, 15, dtype=np.int64), "s": strs}, index=idx1)
    assert_frame_equal(vit.data, expected)


def test_multi_index_column_filtering(lmdb_version_store, sym):
    strs = np.array(["zero", "one", "two", "three", "four"] * 2)
    idx1 = np.repeat(np.arange(datetime(2020, 1, 1), datetime(2020, 1, 6), timedelta(days=1)).astype(datetime), 2)
    idx2 = np.arange(0, 10, dtype=np.int64)
    d1 = {
        "idx1": idx1,
        "idx2": idx2,
        "x": np.arange(10, 20, dtype=np.int64),
        "y": np.arange(20, 30, dtype=np.int64),
        "s": strs,
        "z": np.arange(30, 40, dtype=np.int64),
    }
    df3 = pd.DataFrame(data=d1)
    df3.set_index(["idx1", "idx2"], inplace=True)
    lmdb_version_store.write(sym, df3)
    vit = lmdb_version_store.read(sym, columns=["idx2", "x", "s"])
    expected = pd.DataFrame({"idx1": idx1, "idx2": idx2, "x": np.arange(10, 20, dtype=np.int64), "s": strs})
    expected.set_index(["idx1", "idx2"], inplace=True)
    assert_frame_equal(vit.data, expected)

    vit = lmdb_version_store.read(sym, columns=["y", "s"])
    expected = pd.DataFrame({"idx1": idx1, "idx2": idx2, "y": np.arange(20, 30, dtype=np.int64), "s": strs})
    expected.set_index(["idx1", "idx2"], inplace=True)
    assert_frame_equal(vit.data, expected)

    vit = lmdb_version_store.read(sym, columns=["idx1", "s", "z"])
    expected = pd.DataFrame({"idx1": idx1, "idx2": idx2, "s": strs, "z": np.arange(30, 40, dtype=np.int64)})
    expected.set_index(["idx1", "idx2"], inplace=True)
    assert_frame_equal(vit.data, expected)


def test_column_filtering_wrong_columns_with_index(lmdb_version_store):
    idx1 = np.arange(0, 5)
    strs = np.array(["zero", "one", "two", "three", "four"])
    d1 = {
        "x": np.arange(10, 15, dtype=np.int64),
        "y": np.arange(20, 25, dtype=np.int64),
        "s": strs,
        "z": np.arange(30, 35, dtype=np.int64),
    }
    df3 = pd.DataFrame(data=d1, index=idx1)
    lmdb_version_store.write("strings", df3)
    vit = lmdb_version_store.read("strings", columns=["wrong_col"])
    assert len(vit.data.columns) == 0


def test_column_filtering_wrong_columns_with_no_index(lmdb_version_store):
    strs = np.array(["zero", "one", "two", "three", "four"])
    d1 = {
        "x": np.arange(10, 15, dtype=np.int64),
        "y": np.arange(20, 25, dtype=np.int64),
        "s": strs,
        "z": np.arange(30, 35, dtype=np.int64),
    }
    df3 = pd.DataFrame(data=d1)
    lmdb_version_store.write("strings", df3)
    vit = lmdb_version_store.read("strings", columns=["wrong_col"])
    assert len(vit.data) == 0
