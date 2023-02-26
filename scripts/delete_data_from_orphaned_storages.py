import argparse
from logging import getLogger

from man.arctic.scripts.arctic_native_helper import get_admin_dao, get_admin_credentials_helper
from arcticc.version_store._store import NativeVersionStore
from arcticc.pb2.storage_pb2 import LibraryConfig
from arcticc.pb2.s3_storage_pb2 import Config as S3Config

logger = getLogger(__name__)

NAMESPACE_MAP = {
    "mktdatad": {
        "PAREPORT",
        "SP1284",
        "alertingalicisprj",
        "alla",
        "asd",
        "backuptest",
        "centraltrading_ahl",
        "centraltrading",
        "codex",
        "equities",
        "mhertz_test",
        "msl",
        "not_rseaman_2021",
        "not_rseaman",
        "project1",
        "project2",
        "rseaman1",
        "rseaman_delete_1",
        "rseaman_demo_1",
        "rseaman_mongo",
        "rseaman1",
        "rseaman_test",
        "sdf",
        "sleveridge",
        "test",
        "trading_data",
    },
    "research": [
        "HAN",
        "PAREPORT",
        "QARL_ML",
        "Risk_Data_Store",
        "SECTOR_REVIEW",
        "VOLTABOND",
        "aca",
        "ahl_marketdata_cache",
        "ahl_marketdata_private",
        "ahl_msl",
        "ahl",
        "ahlgraph",
        "ahlmarketdata_cache",
        "amaher",
        "amdcache_ahl",
        "amulliner",
        "analyst_comp",
        "arctic_native",
        # "backup", DO NOT INCLUDE backup_native_config, STORAGES IN HERE ARE referred to by pre/prod libs
        "beta_stresses",
        "bonsai_euro",
        "build_metrics",
        "capacity_data",
        "cdsvol",
        "centraltrading_ahl",
        "centraltrading",
        "codex",
        "credit",
        "dyin",
        "etfs",
        "fixed_income",
        "fstock_revamp",
        "fts",
        "glgBAM",
        "glg_ia",
        "glg",
        "glg_strat_bond",
        "glg_test",
        "glgperflab",
        "gpm",
        "haystack",
        "hmartay",
        "hmartay_test2",
        "hmartay_test4",
        "hmartay_test",
        "hmartaytest6",
        "hola",
        "indexarb",
        "intraday",
        "ir",
        "liquidity_dev",
        "margin_estimation",
        "marketdata_cache",
        "mh_test",
        "mkd_ahlmarketdata_cache",
        "msl",
        "numeric",
        "p1",
        "pajohnston",
        "pfa",
        "pm",
        "project1",
        "project2",
        "project3",
        "qarl_ahl",
        "qarl",
        "qarl_numeric",
        "reddit",
        "risk",
        "riskfrm",
        "rseaman1",
        "rseaman20210226",
        "shared",
        "skhare",
        "support",
        "swx10",
        "tcryp",
        "test3",
        "test6",
        "test_centaur",
        "test",
        "timtest1",
        "tisaacs",
        "tisaacs_private",
        "tmacetest",
        "trains",
        "triskcnoff",
        "vamos",
        "warehouse",
        "wdealtry",
        "xgao",
    ],
}


def parse_args():
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("--env", required=True, type=str)
    parser.add_argument("--for-real", default=False, action="store_true", help="Actually delete data and config")
    opts = parser.parse_args()
    dry_run = not opts.for_real
    env = opts.env
    if env not in NAMESPACE_MAP.keys():
        raise Exception(f"Invalid env '{env}' (options are {list(NAMESPACE_MAP.keys())})")
    return dry_run, env


def get_daos(env, dry_run):
    credentials_helper = get_admin_credentials_helper(env, "admin", dry_run)
    # Create a dict from namespace to dao
    # "arctic" is the default namespace for libs without a credentials_store set
    daos = {"arctic": get_admin_dao(env, "admin", dry_run)}
    for namespace in NAMESPACE_MAP[env]:
        # Create dummy lib_cfg to conform to CredentialsHelper interface
        lib_cfg = LibraryConfig()
        lib_cfg.lib_desc.credentials_store.mongo.database = namespace
        daos[namespace], _ = credentials_helper._get_matching_helper(lib_cfg)._get_dao_and_database_name(lib_cfg)
    return daos


def get_storage_ids(daos):
    storage_ids = {}
    for namespace, dao in daos.items():
        storage_ids[namespace] = set(dao.list_storages())
    return storage_ids


def remove_referenced_storage_ids(namespace, dao, storage_ids):
    lib_names = list(dao.list_libraries())
    for lib_name in lib_names:
        lib_desc = dao.find_library_config(lib_name)
        if lib_desc is not None:
            lib_namespace = namespace
            if lib_desc.HasField("credentials_store") and lib_desc.credentials_store.HasField("mongo"):
                lib_namespace = lib_desc.credentials_store.mongo.database
            if lib_namespace in storage_ids.keys():
                storage_ids[lib_namespace] = storage_ids[lib_namespace].difference(set(lib_desc.storage_ids))
            else:
                logger.warning(
                    f"Storage config for {lib_name} in {lib_namespace}_native_config db, please add {lib_namespace} to the NAMESPACE_MAP"
                )
        else:
            logger.error(f"Could not find lib_cfg for {lib_name}")
    return storage_ids


def remove_orphaned_data(env, daos, storage_ids, dry_run):
    for namespace, storage_ids in storage_ids.items():
        for idx, storage_id in enumerate(storage_ids):
            try:
                lib = construct_dummy_library(env, daos[namespace], storage_id, on_res_flashblade)
                if lib:
                    logger.info(f"{idx+1}/{len(storage_ids)} clearing {storage_id} in {namespace}_native_config")
                    if not dry_run:
                        lib.version_store.clear()
                        daos[namespace].delete_storage_config(storage_id)
            except Exception as e:
                logger.error(f"Failed to clear {storage_id}\n{e}")


def on_res_flashblade(storage_cfg):
    try:
        s3_config = S3Config()
        storage_cfg.config.Unpack(s3_config)
        return s3_config.endpoint in [
            "s3.gdc.res.m",
            "http://s3.gdc.res.m",
            "105.fb.gdc.storage.res.m",
            "http://105.fb.gdc.storage.res.m",
        ]
    except:
        return False


def construct_dummy_library(env, dao, storage_id, filter=lambda *_: True):
    storage_cfg = dao.find_storage_config(storage_id)
    if storage_cfg is not None and filter(storage_cfg):
        lib_cfg = LibraryConfig()
        # Need a dummy name to create version store, just use the storage_id
        lib_cfg.lib_desc.name = storage_id
        lib_cfg.lib_desc.storage_ids[:] = [storage_id]
        lib_cfg.storage_by_id[storage_id].CopyFrom(storage_cfg)
        return NativeVersionStore.create_store_from_lib_config(lib_cfg, env)


if __name__ == "__main__":
    dry_run, env = parse_args()
    # Dict from namespace to dao
    daos = get_daos(env, dry_run)
    # List storage_ids BEFORE finding storage_ids associated with libraries.
    # If done the other way around, there is a race with libraries being created.
    # Dict from namespace to set of storage IDs in that namespace
    storage_ids = get_storage_ids(daos)
    # Remove from the dict any storage_ids that are referenced in a lib_cfg in arctic_native_config
    # or in <namespace>_native_config for any of the namespaces
    for namespace, dao in daos.items():
        storage_ids = remove_referenced_storage_ids(namespace, dao, storage_ids)
    remove_orphaned_data(env, daos, storage_ids, dry_run)
