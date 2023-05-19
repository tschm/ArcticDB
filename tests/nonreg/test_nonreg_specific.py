import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from arcticc.pb2.descriptors_pb2 import TypeDescriptor
import datetime
from random import sample

from tests.util.date import DateRange


from man.arctic.library_util import get_native_lib as man_core_get_native_lib


def get_native_lib(l="arcticc.nonreg", h="research"):
    return man_core_get_native_lib(h, l)


def test_update_float_int(dynamic_schema_store):
    symbol = "test_update_float_int"
    data1 = pd.DataFrame({"a": [np.float64(1.0)]}, index=[datetime.datetime(2019, 4, 9, 10, 5, 2, 1)])
    data2 = pd.DataFrame({"a": [np.int64(2)]}, index=[datetime.datetime(2019, 4, 8, 10, 5, 2, 1)])
    expected = data1.append(data2)
    expected.sort_index(inplace=True)

    dynamic_schema_store.write(symbol, data1)
    dynamic_schema_store.update(symbol, data2, dynamic_schema=True)
    result = dynamic_schema_store.read(symbol, dynamic_schema=True).data
    result.sort_index(inplace=True)

    assert_frame_equal(expected, result)


def test_update_int_float(dynamic_schema_store):
    symbol = "test_update_int_float"
    data1 = pd.DataFrame({"a": [np.int64(2)]}, index=[datetime.datetime(2019, 4, 9, 10, 5, 2, 1)])
    data2 = pd.DataFrame({"a": [np.float64(1.0)]}, index=[datetime.datetime(2019, 4, 8, 10, 5, 2, 1)])
    expected = data1.append(data2)
    expected.sort_index(inplace=True)

    dynamic_schema_store.write(symbol, data1)
    dynamic_schema_store.update(symbol, data2, dynamic_schema=True)
    result = dynamic_schema_store.read(symbol, dynamic_schema=True).data
    result.sort_index(inplace=True)

    assert_frame_equal(expected, result)


def test_update_nan_int(dynamic_schema_store):
    symbol = "test_update_nan_int"
    data1 = pd.DataFrame({"a": [np.nan]}, index=[datetime.datetime(2019, 4, 9, 10, 5, 2, 1)])
    data2 = pd.DataFrame({"a": [np.int64(2)]}, index=[datetime.datetime(2019, 4, 8, 10, 5, 2, 1)])
    expected = data1.append(data2)
    expected.sort_index(inplace=True)

    dynamic_schema_store.write(symbol, data1)
    dynamic_schema_store.update(symbol, data2, dynamic_schema=True)
    result = dynamic_schema_store.read(symbol, dynamic_schema=True).data
    result.sort_index(inplace=True)

    assert_frame_equal(expected, result)


def test_update_int_nan(dynamic_schema_store):
    symbol = "test_update_int_nan"
    data1 = pd.DataFrame({"a": [np.int64(2)]}, index=[datetime.datetime(2019, 4, 9, 10, 5, 2, 1)])
    data2 = pd.DataFrame({"a": [np.nan]}, index=[datetime.datetime(2019, 4, 8, 10, 5, 2, 1)])
    expected = data1.append(data2)
    expected.sort_index(inplace=True)

    dynamic_schema_store.write(symbol, data1)
    dynamic_schema_store.update(symbol, data2, dynamic_schema=True)
    result = dynamic_schema_store.read(symbol, dynamic_schema=True).data
    result.sort_index(inplace=True)

    assert_frame_equal(expected, result)


def test_append_dynamic_to_fixed_width_strings(dynamic_schema_store):
    symbol = "test_append_dynamic_to_fixed_width_strings"

    fixed_width_strings_index = pd.date_range("2000-1-1", periods=3)
    fixed_width_strings_data = pd.DataFrame({"a": ["hello", "bonjour", "gutentag"]}, index=fixed_width_strings_index)
    dynamic_schema_store.write(symbol, fixed_width_strings_data, dynamic_strings=False)

    info = dynamic_schema_store.get_info(symbol)
    assert TypeDescriptor.ValueType.Name(info["dtype"][0].value_type) == "UTF8_STRING"

    dynamic_strings_index = pd.date_range("2000-1-4", periods=3)
    dynamic_strings_data = pd.DataFrame({"a": ["nihao", "konichiwa", "annyeonghaseyo"]}, index=dynamic_strings_index)
    dynamic_schema_store.append(symbol, dynamic_strings_data, dynamic_strings=True)

    info = dynamic_schema_store.get_info(symbol)
    assert TypeDescriptor.ValueType.Name(info["dtype"][0].value_type) == "DYNAMIC_STRING"

    expected_df = fixed_width_strings_data.append(dynamic_strings_data)
    read_df = dynamic_schema_store.read(symbol).data
    assert_frame_equal(expected_df, read_df)


def test_append_fixed_width_to_dynamic_strings(dynamic_schema_store):
    symbol = "test_append_fixed_width_to_dynamic_strings"

    dynamic_strings_index = pd.date_range("2000-1-1", periods=3)
    dynamic_strings_data = pd.DataFrame({"a": ["hello", "bonjour", "gutentag"]}, index=dynamic_strings_index)
    dynamic_schema_store.write(symbol, dynamic_strings_data, dynamic_strings=True)

    info = dynamic_schema_store.get_info(symbol)
    assert TypeDescriptor.ValueType.Name(info["dtype"][0].value_type) == "DYNAMIC_STRING"

    fixed_width_strings_index = pd.date_range("2000-1-4", periods=3)
    fixed_width_strings_data = pd.DataFrame(
        {"a": ["nihao", "konichiwa", "annyeonghaseyo"]}, index=fixed_width_strings_index
    )
    dynamic_schema_store.append(symbol, fixed_width_strings_data, dynamic_strings=False)

    info = dynamic_schema_store.get_info(symbol)
    assert TypeDescriptor.ValueType.Name(info["dtype"][0].value_type) == "DYNAMIC_STRING"

    expected_df = dynamic_strings_data.append(fixed_width_strings_data)
    read_df = dynamic_schema_store.read(symbol).data
    assert_frame_equal(expected_df, read_df)


def test_update_dynamic_to_fixed_width_strings(dynamic_schema_store):
    symbol = "test_update_dynamic_to_fixed_width_strings"

    fixed_width_strings_index = pd.date_range("2000-1-1", periods=3)
    fixed_width_strings_data = pd.DataFrame({"a": ["hello", "bonjour", "gutentag"]}, index=fixed_width_strings_index)
    dynamic_schema_store.write(symbol, fixed_width_strings_data, dynamic_strings=False)

    info = dynamic_schema_store.get_info(symbol)
    assert TypeDescriptor.ValueType.Name(info["dtype"][0].value_type) == "UTF8_STRING"

    dynamic_strings_index = pd.date_range("2000-1-2", periods=1)
    dynamic_strings_data = pd.DataFrame({"a": ["annyeonghaseyo"]}, index=dynamic_strings_index)
    dynamic_schema_store.update(symbol, dynamic_strings_data, dynamic_strings=True)

    info = dynamic_schema_store.get_info(symbol)
    assert TypeDescriptor.ValueType.Name(info["dtype"][0].value_type) == "DYNAMIC_STRING"

    fixed_width_strings_data.update(dynamic_strings_data)
    expected_df = fixed_width_strings_data
    read_df = dynamic_schema_store.read(symbol).data
    assert_frame_equal(expected_df, read_df)


def test_update_fixed_width_to_dynamic_strings(dynamic_schema_store):
    symbol = "test_update_fixed_width_to_dynamic_strings"

    dynamic_strings_index = pd.date_range("2000-1-1", periods=3)
    dynamic_strings_data = pd.DataFrame({"a": ["hello", "bonjour", "gutentag"]}, index=dynamic_strings_index)
    dynamic_schema_store.write(symbol, dynamic_strings_data, dynamic_strings=True)

    fixed_width_strings_index = pd.date_range("2000-1-2", periods=1)
    fixed_width_strings_data = pd.DataFrame({"a": ["annyeonghaseyo"]}, index=fixed_width_strings_index)
    dynamic_schema_store.update(symbol, fixed_width_strings_data, dynamic_strings=False)

    dynamic_strings_data.update(fixed_width_strings_data)
    expected_df = dynamic_strings_data
    read_df = dynamic_schema_store.read(symbol).data
    assert_frame_equal(expected_df, read_df)


def test_numeric_update_case(dynamic_schema_store):
    symbol = "test_numeric_update_case"
    nonreg = get_native_lib()
    data1 = nonreg.read("numeric_update1").data
    data2 = nonreg.read("numeric_update2").data
    expected = data2.append(data1)
    expected.sort_index(axis=1, inplace=True)

    dynamic_schema_store.write(symbol, data1)
    dynamic_schema_store.update(symbol, data2, dynamic_schema=True)

    result = dynamic_schema_store.read(symbol, dynamic_schema=True).data
    result.sort_index(axis=1, inplace=True)

    assert_frame_equal(expected, result)


def test_filter_pre_epoch_date():
    symbol = "pre_epoch_timeseries"
    nonreg = get_native_lib()
    date_range = DateRange(start=None, end=datetime.datetime(2021, 1, 14, 11, 51, 17, 548000))
    vit = nonreg.read(symbol, date_range=date_range)
    assert len(vit.data) == 18200


def test_filter_pre_epoch_date_s3():
    symbol = "pre_epoch_timeseries"
    nonreg = get_native_lib("arcticc.nonreg_s3")
    date_range = DateRange(start=None, end=datetime.datetime(2021, 1, 14, 11, 51, 17, 548000))
    vit = nonreg.read(symbol, date_range=date_range)
    assert len(vit.data) == 18200


def test_centaur_column_regression():
    symbol = "JP_country_traded_ISO"
    nonreg = get_native_lib("arcticc.nonreg_s3")
    columns = ["AST100318", "AST12541"]
    nonreg.read(symbol, columns=columns)


def random_combination(iterable, r, num):
    i = 0
    pool = tuple(iterable)
    n = len(pool)
    rng = range(n)
    while i < num:
        i += 1
        yield [pool[j] for j in sample(rng, r)]


def test_all_column_combinations():
    symbol = "JP_country_traded_ISO"
    nonreg = get_native_lib("arcticc.nonreg_s3")
    columns = nonreg.get_info(symbol)["col_names"]["columns"]
    columns.pop(0)
    df = nonreg.read(symbol).data.pd
    for r in range(2, 500, 17):
        cs = list(random_combination(columns, r, 3))
        for c in cs:
            print("Checking columns {}", c)
            vit = nonreg.read(symbol, columns=c)
            df1 = df[list(c)]
            df1.sort_index(axis=1, inplace=True)
            result = vit.data.pd
            result.sort_index(axis=1, inplace=True)
            assert_frame_equal(df1, result)


def test_head_many_columns():
    symbol = "ML Industry Lvl 4"
    nonreg = get_native_lib("arcticc.nonreg_s3")
    nonreg.head(symbol).data


def test_no_consolidation_no_index():
    symbol = "reference_file_test1"
    nonreg = get_native_lib("arcticc.nonreg_s3")
    nonreg.read(symbol)  # used to throw


def test_read_index_no_rows():
    symbol = "string_col_no_rows"
    nonreg = get_native_lib("arcticc.nonreg_s3")
    nonreg.read_index(symbol)  # used to throw
