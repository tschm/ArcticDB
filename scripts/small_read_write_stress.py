# Script to compare Pure and Vast timings with small data sizes, looking at latency rather than bandwidth
# Use in conjunction with peformance tracing
from arcticc.version_store.helper import Defaults
import numpy as np
import pandas as pd
import time
from arcticc.version_store.helper import ArcticcMemConf, EnvironmentConfigsMap

from arcticc.version_store.helper import create_test_s3_cfg, create_test_vast_cfg


def generate_floats(n, pct_null, repeats=1):
    nunique = int(n / repeats)
    unique_values = np.random.randn(nunique)

    num_nulls = int(nunique * pct_null)
    null_indices = np.random.choice(nunique, size=num_nulls, replace=False)
    unique_values[null_indices] = np.nan

    return unique_values.repeat(repeats)


DATA_GENERATORS = {"float": generate_floats}


def generate_data(total_size, ncols, pct_null=0.1, repeats=1, dtype="float"):
    type_ = np.dtype(float)
    nrows = total_size / ncols / np.dtype(type_).itemsize

    datagen_func = DATA_GENERATORS[dtype]

    data = {"c" + str(i): datagen_func(nrows, pct_null, repeats) for i in range(ncols)}
    return pd.DataFrame(data)


def write_to_arctic(df, symbol, version_store):
    start = time.time()
    key = version_store.write(symbol, df)
    elapsed = time.time() - start
    print("arctic write time: " + symbol + " " + str(elapsed))
    return key


KBYTE = 1 << 10
DATA_SIZE = 50 * KBYTE
NCOLS = 8

cases = {"high_entropy": {"pct_null": 0.0, "repeats": 1}, "low_entropy": {"pct_null": 0.0, "repeats": 10}}


def get_timing(f, path, niter):
    start = time.time()
    for i in range(niter):
        f(path)
    elapsed = time.time() - start
    return elapsed


NITER = 5

results = []
case_files = {}

cfg = EnvironmentConfigsMap()


def vast_version_store(lib_name):
    arcticc = ArcticcMemConf(create_test_vast_cfg(lib_name=lib_name), env=Defaults.ENV)
    return arcticc[lib_name]


def s3_version_store(lib_name):
    arcticc = ArcticcMemConf(create_test_s3_cfg(lib_name=lib_name), env=Defaults.ENV)
    return arcticc[lib_name]


version_store = s3_version_store("wdealtry.test_small_read_write_4")

for x in range(50):
    version_keys = []
    for case, params in cases.items():
        compression = "LZ4"
        symbol = "{0}_{1}".format(case, compression)
        df = generate_data(DATA_SIZE, NCOLS, **params)
        version_keys.append(write_to_arctic(df, symbol, version_store))
        df = None
        case_files[case, compression] = path

    for key in version_keys:
        start = time.time()
        version_store.read(key.symbol)
        elapsed = time.time() - start
        print("arctic read time: " + str(elapsed))

    for key in version_keys:
        start = time.time()
        version_store.delete(key.symbol)
        elapsed = time.time() - start
        print("arctic delete time: " + str(elapsed))
