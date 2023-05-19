import numpy as np
import pytest

from arcticc.config import Defaults
from arcticc.util.test import sample_dataframe
from arcticc.version_store._store import NativeVersionStore
from arcticc.authorization.permissions import OpenMode
from arcticcxx import set_config_int, unset_config_int
from arcticcxx.storage import KeyType


@pytest.fixture(autouse=True)
def make_lock_wait_less():
    set_config_int("StorageLock.WaitMs", 1)
    try:
        yield
    finally:
        unset_config_int("StorageLock.WaitMs")


@pytest.fixture
def small_max_delta():
    set_config_int("SymbolList.MaxDelta", 2)
    try:
        yield
    finally:
        unset_config_int("SymbolList.MaxDelta")


def test_with_symbol_list(lmdb_version_store):
    syms = []
    for i in range(100):
        df = sample_dataframe(100, i)
        sym = "sym_{}".format(i)
        lmdb_version_store.write(sym, df)
        syms.append(sym)

    list_syms = lmdb_version_store.list_symbols()
    assert len(list_syms) == len(syms)

    for sym in syms:
        assert sym in list_syms

    for sym in list_syms:
        assert sym in syms

    for j in range(0, 100, 2):
        sym = "sym_{}".format(j)
        lmdb_version_store.delete(sym)

    expected_syms = []
    for k in range(1, 100, 2):
        sym = "sym_{}".format(k)
        expected_syms.append(sym)

    list_syms = lmdb_version_store.list_symbols()
    assert len(list_syms) == len(expected_syms)

    for sym in expected_syms:
        assert sym in list_syms

    for sym in list_syms:
        assert sym in expected_syms


def test_symbol_list_with_rec_norm(lmdb_version_store):
    lmdb_version_store.write(
        "rec_norm", data={"a": np.arange(5), "b": np.arange(8), "c": None}, recursive_normalizers=True
    )
    assert not lmdb_version_store.is_symbol_pickled("rec_norm")
    assert lmdb_version_store.list_symbols() == ["rec_norm"]


def test_interleaved_store_read(version_store_factory):
    vs1 = version_store_factory(symbol_list=True)
    vs2 = version_store_factory(symbol_list=True, reuse_name=True)

    vs1.write("a", 1)
    vs2.delete("a")

    assert vs1.list_symbols() == []


@pytest.fixture
def mongo_version_store_symbol_list(mongo_store_factory):  # LMDB does not allow OpenMode to be changed
    return mongo_store_factory(symbol_list=True)


def make_read_only(lib):
    return NativeVersionStore.create_store_from_lib_config(lib.lib_cfg(), Defaults.ENV, OpenMode.READ)


def test_symbol_list_delete(lmdb_version_store):
    lib = lmdb_version_store
    lib.write("a", 1)
    assert lib.list_symbols() == ["a"]
    lib.write("b", 1)
    lib.delete("a")
    assert lib.list_symbols() == ["b"]


def test_symbol_list_delete_incremental(lmdb_version_store):
    lib = lmdb_version_store
    lib.write("a", 1)
    lib.write("a", 2, prune_previous=False)
    lib.write("b", 1)
    lib.delete_version("a", 0)
    assert sorted(lib.list_symbols()) == ["a", "b"]
    lib.delete_version("a", 1)
    assert lib.list_symbols() == ["b"]


def test_deleted_symbol_with_tombstones(lmdb_version_store_tombstones_no_symbol_list):
    lib = lmdb_version_store_tombstones_no_symbol_list
    lib.write("a", 1)
    assert lib.list_symbols() == ["a"]
    lib.write("b", 1)
    lib.delete("a")
    assert lib.list_symbols() == ["b"]


def test_empty_lib(lmdb_version_store):
    lib = lmdb_version_store
    assert lib.list_symbols() == []
    lt = lib.library_tool()
    assert len(lt.find_keys(KeyType.SYMBOL_LIST)) == 1
