from arcticc.version_store._custom_normalizers import register_normalizer, clear_registered_normalizers
import sys

import signal

if sys.platform == "win32":
    # Hack to define signal.SIGKILL as some deps eg pytest-test-fixtures hardcode SIGKILL terminations.
    signal.SIGKILL = signal.SIGINT

import string
import time
import os
import pytest
import numpy as np
import pandas as pd
import random
from datetime import datetime
from typing import Optional
from functools import partial

from pytest_server_fixtures import CONFIG
from arcticc.pb2.storage_pb2 import EnvironmentConfigsMap
from arcticc.pb2.lmdb_storage_pb2 import Config as LmdbConfig

from arcticc.version_store.helper import (
    get_storage_for_lib_name,
    get_secondary_storage_for_lib_name,
    get_lib_cfg,
    create_test_lmdb_cfg,
    create_test_s3_cfg,
)

from arcticc.config import Defaults
from arcticc.util.test import configure_test_logger, apply_lib_cfg
from arcticc.version_store import NativeVersionStore
from numpy.random import RandomState
from pandas import DataFrame

_rnd = RandomState(0x42)

configure_test_logger()

# pytest_plugins = ['pytest_profiling']

_CONTAINER_MONGOD = "/opt/mongo/bin/mongod"


@pytest.fixture()
def sym():
    return "test" + datetime.utcnow().strftime("%Y-%m-%dT%H_%M_%S_%f")


@pytest.fixture()
def lib_name():
    return "local.test" + datetime.utcnow().strftime("%Y-%m-%dT%H_%M_%S_%f")


# No longer necessary given both the dir and the lib_name are now unique
def get_temp_dbdir(tmpdir):
    return str(tmpdir.mkdir("lmdb.{:x}".format(_rnd.randint(100000))))


@pytest.fixture(autouse=True)
def fix_mongod():
    if not os.path.isfile(CONFIG.mongo_bin):
        CONFIG.mongo_bin = _CONTAINER_MONGOD


@pytest.fixture
def arcticc_native_local_lib_cfg(tmpdir):
    def create(lib_name):
        return create_local_lmdb_cfg(lib_name=lib_name, db_dir=str(tmpdir))

    # def create(lib_name):
    #    return create_test_s3_cfg(lib_name=lib_name)

    # def create(lib_name):
    #   return create_test_vast_cfg(lib_name=lib_name)

    return create


@pytest.fixture
def arcticc_native_local_lib_cfg_extra(tmpdir):
    def create():
        return create_local_lmdb_cfg(lib_name="local.extra", db_dir=get_temp_dbdir(tmpdir))

    return create


def _version_store_factory_body(
    used, make_cfg, default_name, *, name: str = None, reuse_name=False, **kwargs
) -> NativeVersionStore:
    name = name or default_name
    if name == "_unique_":
        name = name + str(len(used))
    assert (name not in used) or reuse_name, f"{name} is already in use"
    cfg = make_cfg(name)
    lib = cfg.env_by_id[Defaults.ENV].lib_by_path[name]
    # Use symbol list by default (can still be overridden by kwargs)
    lib.version.symbol_list = True
    apply_lib_cfg(lib, kwargs)
    out = ArcticcMemConf(cfg, Defaults.ENV)[name]
    used[name] = out
    return out


@pytest.fixture
def version_store_factory(arcticc_native_local_lib_cfg, lib_name):
    """Factory to create any number of distinct LMDB libs with the given WriteOptions or VersionStoreConfig.

    Accepts legacy options col_per_group and row_per_segment which defaults to 2.
    `name` can be a magical value "_unique_" which will create libs with unique names."""
    used = {}

    def version_store(col_per_group: Optional[int] = 2, row_per_segment: Optional[int] = 2, **kwargs):
        if col_per_group is not None and "column_group_size" not in kwargs:
            kwargs["column_group_size"] = col_per_group
        if row_per_segment is not None and "segment_row_size" not in kwargs:
            kwargs["segment_row_size"] = row_per_segment
        return _version_store_factory_body(used, arcticc_native_local_lib_cfg, lib_name, **kwargs)

    return version_store


@pytest.fixture
def s3_store_factory(lib_name):
    """Factory to create any number of S3 libs on Pure with the given WriteOptions or VersionStoreConfig.

    `name` can be a magical value "_unique_" which will create libs with unique names.
    This factory will clean up any libraries requested
    """
    used = {}
    try:
        yield partial(_version_store_factory_body, used, create_test_s3_cfg, lib_name)
    finally:
        for lib in used.values():
            lib.version_store.clear()


@pytest.fixture
def lmdb_version_store(version_store_factory):
    return version_store_factory(col_per_group=None, row_per_segment=None)
    # FUTURE: replace most of the fixtures below with factory calls in test methods


@pytest.fixture
def lmdb_version_store_ts_norm(version_store_factory):
    normalizers = pytest.importorskip("ahl.mongo.mongoose.normalizers")
    try:
        register_normalizer(normalizers.TimeSeriesNormalizer())
        yield lmdb_version_store(version_store_factory)
    finally:
        clear_registered_normalizers()


@pytest.fixture
def version_store_sync_test_factory(mongo_server_sess, tmpdir):
    def version_stores(num_targets=1, delayed_deletes=True, fast_tombstone_all=True, name=None):
        # type: (Optional[int], Optional[bool], Optional[bool], Optional[str])->(NativeVersionStore, List[NativeVersionStore])
        cfg = EnvironmentConfigsMap()
        # 0 will be the source, 1-num_targets will be the targets
        libs = []
        # Add a random hash on each call, otherwise calling twice with the same arguments creates the same storage_ids
        base_lib_name = (
            name
            if name
            else "lib-{}-{}-{}-{}".format(
                "".join(random.choices(string.ascii_letters, k=5)), num_targets, delayed_deletes, fast_tombstone_all
            )
        )
        for i in range(num_targets + 1):
            lib_name = "local.{}-{}".format(base_lib_name, "source" if i == 0 else "target-{}".format(i))
            add_mongo_library_to_env(
                cfg,
                lib_name=lib_name,
                env_name=Defaults.ENV,
                uri="mongodb://{}:{}".format(mongo_server_sess.hostname, mongo_server_sess.port),
            )
            lib_cfg = cfg.env_by_id[Defaults.ENV].lib_by_path[lib_name]
            lib_cfg.version.write_options.sync_passive.enabled = True
            lib_cfg.version.write_options.delayed_deletes = delayed_deletes
            lib_cfg.version.write_options.fast_tombstone_all = fast_tombstone_all
            # Set some default config we want for all tests
            lib_cfg.version.symbol_list = True
            lib_cfg.version.write_options.column_group_size = 2
            lib_cfg.version.write_options.segment_row_size = 2
            libs.append(ArcticcMemConf(cfg, Defaults.ENV)[lib_name])
        storage_ids = [x.lib_cfg().lib_desc.storage_ids[0] for x in libs]
        return libs[0], libs[1:], storage_ids

    return version_stores


@pytest.fixture
def lmdb_version_store_column_buckets(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.dynamic_schema = True
    lib_cfg.version.write_options.column_group_size = 3
    lib_cfg.version.write_options.segment_row_size = 2
    lib_cfg.version.write_options.bucketize_dynamic = True
    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_column_buckets_dynamic_string(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.dynamic_schema = True
    lib_cfg.version.write_options.column_group_size = 3
    lib_cfg.version.write_options.segment_row_size = 2
    lib_cfg.version.write_options.bucketize_dynamic = True
    lib_cfg.version.write_options.dynamic_strings = True
    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_new(arcticc_native_local_lib_cfg, lib_name):
    # TODO: this fixture has all the defaults which are enabled for version store, I haven't renamed
    # the original fixture as some of our tests that rely on no pruning will fail.
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.use_tombstones = True
    lib_cfg.version.write_options.prune_previous_version = True
    lib_cfg.version.symbol_list = True

    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_dynamic_schema(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.use_tombstones = True
    lib_cfg.version.write_options.prune_previous_version = True
    lib_cfg.version.write_options.dynamic_schema = True
    lib_cfg.version.write_options.dynamic_strings = True
    lib_cfg.version.symbol_list = True

    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_tombstones_no_symbol_list(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.use_tombstones = True
    lib_cfg.version.write_options.prune_previous_version = True
    lib_cfg.version.symbol_list = False

    return arcticc[lib_name]


@pytest.fixture
def lmdb_tick_store_small_row(arcticc_native_local_lib_cfg, lib_name):
    # Note this is the same as a version store with no column filtering for now.
    cfg = arcticc_native_local_lib_cfg(lib_name)
    lib = cfg.env_by_id[Defaults.ENV].lib_by_path[Defaults.LIB]
    lib.version.write_options.column_group_size = np.iinfo(np.int32).max  # TODO shouldn't be needed
    lib.version.write_options.segment_row_size = 3
    lib.version.write_options.dynamic_schema = True
    return ArcticcMemConf(cfg=cfg, env=Defaults.ENV)[lib_name]


@pytest.fixture
def lmdb_tick_store(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.column_group_size = np.iinfo(np.int32).max  # TODO shouldn't be needed
    lib_cfg.version.write_options.dynamic_schema = True
    lib_cfg.version.write_options.allow_sparse = True
    lib_cfg.version.write_options.incomplete = True
    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_double_storage(arcticc_native_local_lib_cfg, tmpdir, lib_name):
    config = arcticc_native_local_lib_cfg(lib_name)
    arcticc = ArcticcMemConf(config, env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.storage_fallthrough = True

    lmdb = LmdbConfig()
    lmdb.path = get_temp_dbdir(tmpdir)
    env = config.env_by_id[Defaults.ENV]
    sid, storage = get_secondary_storage_for_lib_name(lib_name, env=env)
    storage.config.Pack(lmdb, type_url_prefix="cxx.arctic.org")
    lib_cfg.storage_ids.append(sid)

    return arcticc[lib_name]


@pytest.fixture
def dynamic_schema_store(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.column_group_size = np.iinfo(np.int32).max  # TODO shouldn't be needed
    lib_cfg.version.write_options.dynamic_schema = True
    lib_cfg.version.write_options.allow_sparse = True
    return arcticc[lib_name]


@pytest.fixture
def lmdb_tick_store_set_tz(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.dynamic_schema = True
    lib_cfg.version.write_options.allow_sparse = True
    lib_cfg.version.write_options.set_tz = True
    lib_cfg.version.write_options.incomplete = True
    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_extra(arcticc_native_local_lib_cfg_extra, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg_extra(), env=Defaults.ENV)
    return arcticc["local.extra"]


@pytest.fixture
def lmdb_version_store_allows_pickling(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.use_norm_failure_handler_known_types = True
    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_no_symbol_list(version_store_factory):
    return version_store_factory(col_per_group=None, row_per_segment=None, symbol_list=False)


@pytest.fixture
def lmdb_version_store_arcticc(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.symbol_list = True
    return arcticc, lib_name


@pytest.fixture
def lmdb_version_store_tombstone_and_pruning(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.use_tombstones = True
    lib_cfg.version.write_options.prune_previous_version = True
    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_tombstone(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.use_tombstones = True
    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_delayed_deletes(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.delayed_deletes = True
    return arcticc[lib_name]


# Note: The lmdb_version_store_with_write_option fixture essentially replaces all of these fixtures
@pytest.fixture
def lmdb_version_store_delayed_deletes_with_pruning_tombstones(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.delayed_deletes = True
    lib_cfg.version.write_options.use_tombstones = True
    lib_cfg.version.write_options.prune_previous_version = True
    lib_cfg.version.symbol_list = True

    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_ignore_order(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.ignore_sort_order = True

    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_with_write_option(arcticc_native_local_lib_cfg, request, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    for option in request.param:
        if option == "sync_passive.enabled":
            setattr(lib_cfg.version.write_options.sync_passive, "enabled", True)
        else:
            setattr(lib_cfg.version.write_options, option, True)

    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_tombstone_and_sync_passive(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.use_tombstones = True
    lib_cfg.version.write_options.sync_passive.enabled = True
    return arcticc[lib_name]


@pytest.fixture
def s3_version_store(s3_store_factory):
    return s3_store_factory()


@pytest.fixture
def vast_version_store(lib_name):
    arcticc = ArcticcMemConf(create_test_vast_cfg(lib_name=lib_name), env=Defaults.ENV)
    return arcticc[lib_name]


@pytest.fixture
def s3_version_store_tombstones(s3_store_factory):
    return s3_store_factory(use_tombstones=True)


@pytest.fixture
def s3_version_store_fixture(lib_name):
    params = ["use_tombstones"]
    return make_s3_fixture(lib_name, params)  # TODO: replace all make_s3_fixture with s3_store_factory


@pytest.fixture
def vast_version_store_fixture(lib_name):
    params = ["use_tombstones"]
    return make_vast_fixture(lib_name, params)


@pytest.fixture
def s3_version_store_fixture_prune_previous(lib_name):
    params = ["use_tombstones", "prune_previous_version"]
    return make_s3_fixture(lib_name, params)


@pytest.fixture
def s3_tick_store_set_tz(lib_name):
    params = ["use_tombstones", "set_tz", "dynamic_schema", "allow_sparse", "incomplete"]
    return make_s3_fixture(lib_name, params)


@pytest.fixture
def s3_tick_store_compact_dedup(lib_name):
    params = [
        "use_tombstones",
        "set_tz",
        "dynamic_schema",
        "allow_sparse",
        "incomplete",
        "compact_incomplete_dedup_rows",
    ]
    return make_s3_fixture(lib_name, params)


@pytest.fixture
def mongo_store_factory(mongo_server_sess, lib_name):
    """Similar capability to `s3_store_factory`, but uses a mongo store."""
    used = {}
    uri = "mongodb://{}:{}".format(mongo_server_sess.hostname, mongo_server_sess.port)
    cfg_maker = partial(create_local_mongo_cfg, uri=uri)
    try:
        yield partial(_version_store_factory_body, used, cfg_maker, lib_name)
    finally:
        for lib in used.values():
            lib.version_store.clear()


@pytest.fixture
def s3_dynamic_schema_store(lib_name):
    params = ["use_tombstones", "dynamic_schema", "dynamic_strings"]
    return make_s3_fixture(lib_name, params)


@pytest.fixture
def mongo_version_store(mongo_store_factory):
    return mongo_store_factory()


@pytest.fixture
def mongo_version_store_tombstones(mongo_store_factory):
    return mongo_store_factory(use_tombstones=True)


@pytest.fixture
def lmdb_version_store_small_segment(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.column_group_size = 1000
    lib_cfg.version.write_options.segment_row_size = 1000

    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_tiny_segment(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.column_group_size = 2
    lib_cfg.version.write_options.segment_row_size = 2

    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_tiny_segment_dynamic_string(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.column_group_size = 2
    lib_cfg.version.write_options.segment_row_size = 2
    lib_cfg.version.write_options.dynamic_schema = True
    lib_cfg.version.write_options.dynamic_strings = True
    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_tiny_segment_dynamic(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.column_group_size = 2
    lib_cfg.version.write_options.segment_row_size = 2
    lib_cfg.version.write_options.dynamic_schema = True

    return arcticc[lib_name]


@pytest.fixture
def lmdb_version_store_tiny_segment_dynamic_dynamic_string(arcticc_native_local_lib_cfg, lib_name):
    arcticc = ArcticcMemConf(arcticc_native_local_lib_cfg(lib_name), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.write_options.column_group_size = 2
    lib_cfg.version.write_options.segment_row_size = 2
    lib_cfg.version.write_options.dynamic_schema = True
    lib_cfg.version.write_options.dynamic_strings = True
    return arcticc[lib_name]


@pytest.fixture
def mongo_version_store_failure_sim(mongo_server_sess, lib_name):
    uri = "mongodb://{}:{}".format(mongo_server_sess.hostname, mongo_server_sess.port)
    arcticc = ArcticcMemConf(create_local_mongo_cfg(lib_name=lib_name, uri=uri), env=Defaults.ENV)
    lib_cfg = get_lib_cfg(arcticc, Defaults.ENV, lib_name)
    lib_cfg.version.failure_sim.write_failure_prob = 0.3
    lib_cfg.version.failure_sim.read_failure_prob = 0.3
    return arcticc[lib_name]


@pytest.fixture
def ut_small_all_version_store(arcticc_native_local_lib_cfg, lib_name):
    cfg = arcticc_native_local_lib_cfg(lib_name)
    lib = cfg.env_by_id[Defaults.ENV].lib_by_path[Defaults.LIB]
    lib.version.write_options.column_group_size = 2
    lib.version.write_options.segment_row_size = 2
    return ArcticcMemConf(cfg=cfg, env=Defaults.ENV)[lib_name]


@pytest.fixture
def arcticc_native_test_lib_cfg(tmpdir):
    def create():
        lib_name = "test.example"
        env_name = "research"
        cfg = EnvironmentConfigsMap()
        env = cfg.env_by_id[env_name]

        lmdb = LmdbConfig()
        lmdb.path = get_temp_dbdir(tmpdir)
        sid, storage = get_storage_for_lib_name(lib_name, env)
        storage.config.Pack(lmdb, type_url_prefix="cxx.arctic.org")

        lib_desc = env.lib_by_path[lib_name]
        lib_desc.storage_ids.append(sid)
        lib_desc.name = lib_name
        lib_desc.description = "A friendly config for testing"

        version = lib_desc.version
        version.write_options.column_group_size = 23
        version.write_options.segment_row_size = 42

        return cfg

    return create


@pytest.fixture
def one_col_df(start=0):
    # type: () -> DataFrame
    return DataFrame({"x": np.arange(start, start + 10, dtype=np.int64)})


@pytest.fixture
def two_col_df(start=0):
    # type: () -> DataFrame
    return DataFrame(
        {"x": np.arange(start, start + 10, dtype=np.int64), "y": np.arange(start + 10, start + 20, dtype=np.int64)}
    )


@pytest.fixture
def three_col_df(start=0):
    # type: () -> DataFrame
    return DataFrame(
        {
            "x": np.arange(start, start + 10, dtype=np.int64),
            "y": np.arange(start + 10, start + 20, dtype=np.int64),
            "z": np.arange(start + 20, start + 30, dtype=np.int64),
        },
        index=np.arange(start, start + 10, dtype=np.int64),
    )


def get_val(col):
    d_type = col % 3
    if d_type == 0:
        return random.random() * 10
    elif d_type == 1:
        return random.random()
    else:
        return str(random.random() * 10)


@pytest.fixture
def get_wide_df():
    def get_df(ts, width, max_col_width):
        cols = random.sample(range(max_col_width), width)
        return pd.DataFrame(index=[pd.Timestamp(ts)], data={str(col): get_val(col) for col in cols})

    return get_df
