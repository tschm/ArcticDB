import pandas as pd
from arcticdb.util.test import assert_frame_equal
import pytest
from itertools import product
from tests.util.date import DateRange
import datetime
from arcticc.util.test import random_floats
from arcticcxx.exceptions import ArcticNativeCxxException


def test_update_single_dates(lmdb_version_store_dynamic_schema):
    lib = lmdb_version_store_dynamic_schema
    df1 = pd.DataFrame(index=[pd.Timestamp(2022, 1, 3)], data=2220103.0, columns=["a"])
    df2 = pd.DataFrame(index=[pd.Timestamp(2021, 12, 22)], data=211222.0, columns=["a"])
    df3 = pd.DataFrame(index=[pd.Timestamp(2021, 12, 29)], data=2211229.0, columns=["a"])
    sym = "data6"
    lib.update(sym, df1, upsert=True)
    lib.update(sym, df2, upsert=True)
    lib.update(sym, df3, upsert=True)

    expected = df2.append(df3).append(df1)
    assert_frame_equal(lib.read(sym).data, expected)


def test_update_long_strides(lmdb_version_store):
    lib = lmdb_version_store
    symbol = "test_update_long_strides"

    write_df = pd.DataFrame({"A": 7 * [1]}, index=pd.date_range("2023-02-01", periods=7))
    assert write_df.index.values.strides[0] == 8
    lib.write(symbol, write_df)

    update_df = write_df[write_df.index.isin([pd.Timestamp(2023, 2, 1), pd.Timestamp(2023, 2, 6)])].copy()
    update_df["A"] = 999
    assert update_df.index.values.strides[0] == 40

    lib.update(symbol, update_df)

    expected = pd.DataFrame(
        {"A": [999, 999, 1]}, index=[pd.Timestamp(2023, 2, 1), pd.Timestamp(2023, 2, 6), pd.Timestamp(2023, 2, 7)]
    )
    received = lib.read(symbol).data
    pd.testing.assert_frame_equal(expected, received)


def gen_params():
    p = [
        list(range(2, 4)),
        list(range(-1, 1)),
        list(range(-1, 1)),
        list(range(17, 19)),
        list(range(7, 8)),
        list(range(5, 6)),
    ]
    return list(product(*p))


def test_update_with_snapshot(lmdb_version_store, lib_name):
    symbol = "sym"
    idx = pd.date_range("1970-01-01", periods=100, freq="D")
    df = pd.DataFrame({"a": range(len(idx))}, index=idx)
    original_df = df.copy(deep=True)
    lmdb_version_store.write(symbol, df)

    lmdb_version_store.snapshot("my_snap")

    idx2 = pd.date_range("1970-01-12", periods=10, freq="D")
    df2 = pd.DataFrame({"a": range(1000, 1000 + len(idx2))}, index=idx2)
    lmdb_version_store.update(symbol, df2)

    assert_frame_equal(lmdb_version_store.read(symbol, as_of=0).data.astype("int64"), original_df)
    assert_frame_equal(lmdb_version_store.read(symbol, as_of="my_snap").data.astype("int64"), original_df)

    df.update(df2)

    vit = lmdb_version_store.read(symbol)
    assert_frame_equal(vit.data.astype("float"), df)
    assert_frame_equal(lmdb_version_store.read(symbol, as_of=1).data.astype("float"), df)
    assert_frame_equal(lmdb_version_store.read(symbol, as_of="my_snap").data.astype("int64"), original_df)

    lmdb_version_store.delete(symbol)
    assert lmdb_version_store.list_versions() == []

    assert_frame_equal(lmdb_version_store.read(symbol, as_of="my_snap").data.astype("int64"), original_df)


def generate_dataframe(columns, dt, num_days, num_rows_per_day):
    df = pd.DataFrame()
    for _ in range(num_days):
        index = pd.Index([dt + datetime.timedelta(seconds=s) for s in range(num_rows_per_day)])
        vals = {c: random_floats(num_rows_per_day) for c in columns}
        new_df = pd.DataFrame(data=vals, index=index)
        df = df.append(new_df)
        dt = dt + datetime.timedelta(days=1)

    return df


def test_update_with_daterange(lmdb_version_store):
    lib = lmdb_version_store

    def get_frame_for_date_range(start, end):
        df = pd.DataFrame(index=pd.date_range(start, end, freq="D"))
        df["value"] = df.index.day
        return df

    df1 = get_frame_for_date_range("2020-01-01", "2021-01-01")
    lib.write("test", df1)

    df2 = get_frame_for_date_range("2020-06-01", "2021-06-01")
    date_range = DateRange("2020-01-01", "2022-01-01")
    lib.update("test", df2, date_range=date_range)
    stored_df = lib.read("test").data
    assert stored_df.index.min() == df2.index.min()
    assert stored_df.index.max() == df2.index.max()


def test_update_pickled_data(lmdb_version_store):
    symbol = "test_update_pickled_data"
    idx = pd.date_range("2000-01-01", periods=3)
    df = pd.DataFrame({"a": [[1, 2], [3, 4], [5, 6]]}, index=idx)
    lmdb_version_store.write(symbol, df, pickle_on_failure=True)
    assert lmdb_version_store.is_symbol_pickled(symbol)
    df2 = pd.DataFrame({"a": [1000]}, index=idx[1:2])
    with pytest.raises(ArcticNativeCxxException):
        lmdb_version_store.update(symbol, df2)
