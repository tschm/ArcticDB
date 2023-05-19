import datetime
import sys

import numpy as np
from numpy.testing import assert_equal
import pandas as pd

from arcticc.version_store import TimeFrame
import pytest


def get_artifacts_dir():
    this_path = sys.path[0]
    return this_path + "/tests/artifacts"


@pytest.mark.parametrize("lib_type", ["lmdb_version_store", "s3_version_store"])
def test_jpm_roundtrip(lib_type, request):
    lib = request.getfixturevalue(lib_type)
    index = pd.DatetimeIndex(
        np.array(
            [
                datetime.datetime(2019, 2, 25, 21, 30),
                datetime.datetime(2019, 2, 26, 21, 30),
                datetime.datetime(2019, 2, 27, 21, 30),
                datetime.datetime(2019, 2, 28, 21, 30),
                datetime.datetime(2019, 3, 1, 21, 30),
                datetime.datetime(2019, 3, 4, 21, 30),
                datetime.datetime(2019, 3, 5, 21, 30),
                datetime.datetime(2019, 3, 6, 21, 30),
                datetime.datetime(2019, 3, 7, 21, 30),
                datetime.datetime(2019, 3, 8, 21, 30),
                datetime.datetime(2019, 3, 11, 21, 30),
                datetime.datetime(2019, 3, 12, 21, 30),
                datetime.datetime(2019, 3, 13, 21, 30),
                datetime.datetime(2019, 3, 14, 21, 30),
                datetime.datetime(2019, 3, 15, 21, 30),
                datetime.datetime(2019, 3, 18, 21, 30),
                datetime.datetime(2019, 3, 19, 21, 30),
                datetime.datetime(2019, 3, 20, 21, 30),
                datetime.datetime(2019, 3, 21, 21, 30),
                datetime.datetime(2019, 3, 22, 21, 30),
                datetime.datetime(2019, 3, 25, 21, 30),
            ]
        )
    ).values

    values = np.array(
        [
            0.022975,
            0.022875,
            0.0226,
            0.022925,
            0.02325,
            0.0235,
            0.02335,
            0.02305,
            0.02265,
            0.022275,
            0.02225,
            0.022325,
            0.021975,
            0.022075,
            0.022275,
            0.0222,
            0.021925,
            0.021825,
            0.021525,
            0.021425,
            0.0207,
        ]
    )

    jpm_data = TimeFrame(times=index, columns_names=["values"], columns_values=[values])

    symbol = "IRS_NZD_8Y_3M"
    versioned_item = lib.write(symbol, jpm_data)

    assert versioned_item.symbol == symbol
    assert versioned_item.version == 0

    vit = lib.read(symbol)
    dat = vit.data
    assert_equal(dat.times, jpm_data.times)
    assert_equal(dat.columns_names, jpm_data.columns_names)
    assert_equal(dat.columns_values, jpm_data.columns_values)
