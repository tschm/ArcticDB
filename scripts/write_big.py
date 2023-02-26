from ahl.mongo.mongoose import NativeMongoose
import numpy as np
import pandas as pd
import time
from pandas.util.testing import assert_frame_equal
from numpy.random import RandomState
import pytest

nm = NativeMongoose("research")

lib = nm.get_library("example.big_data")


def generate_floats(n, pct_null, repeats=1):
    rand = RandomState()
    nunique = int(n / repeats)
    unique_values = rand.randn(nunique)

    num_nulls = int(nunique * pct_null)
    null_indices = rand.choice(nunique, size=num_nulls, replace=False)
    unique_values[null_indices] = np.nan

    return unique_values.repeat(repeats)


DATA_GENERATORS = {"float": generate_floats}


def generate_data(nrows, ncols, pct_null=0.1, repeats=1, dtype="float"):
    datagen_func = DATA_GENERATORS[dtype]

    data = {"c" + str(i): datagen_func(nrows, pct_null, repeats) for i in range(ncols)}
    dtidx1 = pd.date_range("19700101", periods=100000)
    return pd.DataFrame(data, index=dtidx1)


def get_df():
    return generate_data(100000, 100000, 0.0, 1000)


lib.write("many_floats", get_df())
