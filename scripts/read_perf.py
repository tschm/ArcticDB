from arcticc.version_store.helper import ArcticcLocalConf, Defaults
import numpy as np
import pandas as pd
import time
from arcticc.version_store.helper import ArcticcMemConf, add_lmdb_library_to_env, EnvironmentConfigsMap

# from tests.util import configure_test_logger


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


MEGABYTE = 1 << 20
DATA_SIZE = 512 * MEGABYTE
NCOLS = 16

cases = {"high_entropy": {"pct_null": 0.0, "repeats": 1}, "low_entropy": {"pct_null": 0.0, "repeats": 1000}}


def get_timing(f, path, niter):
    start = time.time()
    for i in range(niter):
        f(path)
    elapsed = time.time() - start
    return elapsed


NITER = 5

results = []

readers = [
    #  ('pyarrow', lambda path: read_pyarrow(path)),
]

case_files = {}

# configure_test_logger('DEBUG')
# cfg = EnvironmentConfigsMap()
# add_lmdb_library_to_env(cfg, lib_name="perf.test", env_name=Defaults.ENV, db_dir="/tmp")

# arcticc = ArcticcMemConf(cfg, Defaults.ENV)
# version_store = arcticc["perf.test"]
from ahl.mongo.mongoose import NativeMongoose

nm = NativeMongoose("research")
version_store = nm.get_library("example.perf")
version_keys = []

for case, params in cases.items():
    compression = "LZ4"
    symbol = "{0}_{1}".format(case, compression)
    path = "/tmp/{0}.parquet".format(symbol)
    df = generate_data(DATA_SIZE, NCOLS, **params)
    version_keys.append(write_to_arctic(df, symbol, version_store))
    df = None
    case_files[case, compression] = path

for case, params in cases.items():
    path = case_files[case, compression]

    # prime the file cache, seems a bit like cheating actually
    # read_pyarrow(path)
    # read_pyarrow(path)

    for reader_name, f in readers:
        elapsed = get_timing(f, path, NITER) / NITER
        result = case, compression, reader_name, elapsed
        print("parquet read time:" + str(result))
        results.append(result)

for key in version_keys:
    start = time.time()
    version_store.read(key.symbol)
    elapsed = time.time() - start
    print("arctic read time: " + str(elapsed))
