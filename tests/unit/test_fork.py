import time
import sys
import pytest
from multiprocessing import Pool
from pickle import loads, dumps

import numpy as np
import pandas as pd
from arcticc.pb2.storage_pb2 import EnvironmentConfigsMap
from pandas.testing import assert_frame_equal

from arcticc.mongo_config_helper import MongoConfigDAO
from arcticc.toolbox.config import ArcticcMongoConfigWriter
from arcticc.version_store._custom_normalizers import register_normalizer
from arcticc.version_store.helper import ArcticcMongoConf
from arcticc.version_store.helper import add_lmdb_library_to_env, _extract_lib_config
from arcticc.util.test import TestCustomNormalizer


def df(symbol):
    return pd.DataFrame({symbol: np.arange(100)})


def write_symbol(args):
    store, symbol = args
    print("start {}".format(symbol))
    store.write(symbol, df(symbol))
    print("end {}".format(symbol))
    return symbol


def check_lib_config(lib):
    assert lib.env == "test"
    found_test_normalizer = False
    for normalizer in lib._custom_normalizer._normalizers:
        if normalizer.__class__.__name__ == "TestCustomNormalizer":
            found_test_normalizer = True

    assert found_test_normalizer


def test_pickle_store(lmdb_version_store):
    d = {"a": "b"}
    lmdb_version_store.write("xxx", d)
    ser = dumps(lmdb_version_store)
    nvs = loads(ser)
    out = nvs.read("xxx")
    assert d == out.data


def test_map(lmdb_version_store):
    symbols = ["XXX", "YYY"]
    p = Pool(1)
    p.map(write_symbol, [(lmdb_version_store, s) for s in symbols])
    for s in symbols:
        vit = lmdb_version_store.read(s)
        assert_frame_equal(vit.data, df(s))
    p.close()
    p.join()


def _read_and_assert_symbol(args):
    lib, symbol, idx = args
    print("start {}_{}".format(symbol, idx))
    ss = lib.read(symbol)
    assert_frame_equal(ss.data, df("test1"))
    print("end {}".format(idx))


def test_parallel_reads(s3_version_store):
    symbols = ["XXX"] * 20
    p = Pool(10)
    s3_version_store.write(symbols[0], df("test1"))
    time.sleep(0.1)  # Make sure the writes have finished.
    p.map(_read_and_assert_symbol, [(s3_version_store, s, idx) for idx, s in enumerate(symbols)])
    p.close()
    p.join()


@pytest.mark.skipif(sys.platform == "win32", reason="SKIP_WIN Skipping Mongo fixtures for now")
def test_serialize_config(mongo_server):
    env = "test"

    register_normalizer(TestCustomNormalizer())
    # toolbox functionality only - we do not allow direct writes to config db
    writer_dao = MongoConfigDAO.from_mongo_client(mongo_server.api, env=env)
    config_writer = ArcticcMongoConfigWriter(writer_dao)

    config_writer.add_lib_config_coll()
    config_writer.add_storage_config_coll()

    cfg = EnvironmentConfigsMap()
    add_lmdb_library_to_env(cfg, lib_name="vol.test", db_dir="~/tmp/", env_name=env)
    config_writer.add_library_and_storage_config("vol.test", _extract_lib_config(cfg.env_by_id[env], "vol.test"))
    dao = MongoConfigDAO.from_mongo_client(mongo_server.api, env=env)
    mongo_resolver = ArcticcMongoConf(dao)
    vol = mongo_resolver["vol.test"]

    symbols = ["XXX", "YYY"]
    p = Pool(1)
    p.map(check_lib_config, [(vol) for s in symbols])
    p.close()
    p.join()
