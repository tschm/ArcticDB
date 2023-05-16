from logging import getLogger
from typing import AnyStr, Optional, Callable, Any, Iterable

import pymongo
from google.protobuf import field_mask_pb2
from google.protobuf.json_format import MessageToDict, ParseDict

from arcticdb.exceptions import ArcticNativeException
from arcticc.pb2.storage_pb2 import VariantStorage, LibraryConfig, LibraryDescriptor, Permissions
from arcticdb.preconditions import check

from man.arcticdb.config import Defaults


logger = getLogger(__name__)

EnvNameType = AnyStr
_DEFAULT_APPLICATION_NAME = "mongoose"


def _mongo_dict_to_config(cfg, config_type):
    if cfg:
        if config_type == "library":
            proto_msg = LibraryDescriptor()
        elif config_type == "storage":
            proto_msg = VariantStorage()
        elif config_type == "permissions":
            proto_msg = Permissions()
        else:
            raise ArcticNativeException("Unrecognised configuration type: {}".format(config_type))
        cfg = ParseDict(cfg, proto_msg, ignore_unknown_fields=True)
    return cfg


class MongoDBConnector(object):
    @classmethod
    def from_mongo_client(cls, mongo_client, env, auther=None):
        return cls(mongo_client, env, auther)

    @classmethod
    def from_connection_string(
        cls,
        mongo_host,
        hostname_resolver=None,
        auther=None,
        get_authenticated_users=None,
        app_name=_DEFAULT_APPLICATION_NAME,
    ):
        return cls(
            pymongo.MongoClient(hostname_resolver(mongo_host) if hostname_resolver else mongo_host),
            mongo_host,
            auther,
            app_name=app_name,
            get_authenticated_users=get_authenticated_users,
        )

    def __init__(
        self,
        mongo_client: pymongo.MongoClient,
        env: EnvNameType,
        auther: Callable[[pymongo.database.Database, EnvNameType], None] = None,
        get_authenticated_users: Callable[[str, str, str], Iterable[Any]] = None,
        app_name: str = _DEFAULT_APPLICATION_NAME,
    ):
        self.client = mongo_client
        self.auther = auther
        self.get_authenticated_users = get_authenticated_users
        check(env is not None, "Environment string cannot be none")
        self.env = env
        self.user = None
        self.authenticated_users = []
        self.application_name = app_name

    def close(self):
        self.client.close()

    def get_db(self, db_name: str) -> pymongo.database.Database:
        db: pymongo.database.Database = self.client[db_name]

        if self.auther is not None and self.env is not None:
            try:
                creds = self.auther(db, self.env, app_name=self.application_name)
            except TypeError:
                if self.application_name != _DEFAULT_APPLICATION_NAME:
                    logger.warn("Calling auther without using app_name")
                creds = self.auther(db, self.env)
            if creds is not None:
                self.user = creds.user

            admin_db = self.client["admin"]

            try:
                self.auther(admin_db, self.env, app_name=self.application_name)
            except TypeError:
                self.auther(admin_db, self.env)

        if self.get_authenticated_users is not None and self.env is not None:
            self.authenticated_users = list(self.get_authenticated_users(self.env, self.application_name, db_name))

        return db

    def get_user(self):
        return self.user


class MongoConfigDAO(object):
    _DEFAULT_CONFIG_DB = "arctic_native_config"

    def __init__(
        self,
        db_connector,
        config_db_name=None,
        retry_func=None,
        lib_coll_name=Defaults.DEFAULT_LIB_COLL,
        storage_coll_name=Defaults.DEFAULT_STORAGE_COLL,
        lib_meta_coll=Defaults.DEFAULT_LIB_META_COLL,
    ):
        self._db_connector = db_connector
        self._config_db_name = config_db_name or MongoConfigDAO._DEFAULT_CONFIG_DB
        self._db = db_connector.get_db(self._config_db_name)
        self._lib_coll = self.get_config_coll(lib_coll_name)
        self._storage_coll = self.get_config_coll(storage_coll_name)
        self._lib_meta_coll = self.get_config_coll(lib_meta_coll)

        if retry_func is not None:
            for m in ["get_config_coll", "get_config", "add_config", "list_libraries"]:
                setattr(self, m, retry_func(getattr(self, m)))

    @classmethod
    def from_mongo_client(cls, mongo_client, env, auther=None, config_db=None, retry_func=None):
        """Deprecated, use from_db_connector instead"""
        return cls.from_db_connector(
            MongoDBConnector.from_mongo_client(mongo_client, env, auther), config_db=config_db, retry_func=retry_func
        )

    @classmethod
    def from_conn_string(
        cls,
        mongo_host,
        config_db=None,
        hostname_resolver=None,
        auther=None,
        get_authenticated_users=None,
        retry_func=None,
        app_name=_DEFAULT_APPLICATION_NAME,
    ):
        """Deprecated, use from_db_connector instead"""
        return cls.from_db_connector(
            MongoDBConnector.from_connection_string(
                mongo_host,
                auther=auther,
                get_authenticated_users=get_authenticated_users,
                hostname_resolver=hostname_resolver,
                app_name=app_name,
            ),
            config_db=config_db,
            retry_func=retry_func,
        )

    @classmethod
    def from_db_connector(
        cls,
        db_connector: MongoDBConnector,
        config_db: Optional[AnyStr] = None,
        retry_func: Optional[Callable[[Callable[[Any], Any]], Callable[[Any], Any]]] = None,
    ) -> "MongoConfigDAO":
        return cls(db_connector, config_db, retry_func=retry_func)

    def close(self):
        self._db_connector.close()

    def get_config_coll(self, config_coll):
        return self._db[config_coll]

    def get_config(self, id_name, id_value, coll, config_type=None):
        # A bit weird that it defaults like this, but this was the original behaviour
        config_type = id_name if config_type is None else config_type
        cfg = coll.find_one({id_name: id_value}, {"_id": 0})
        return _mongo_dict_to_config(cfg, config_type)

    def get_configs(self, id_name, id_value, coll, config_type=None):
        config_type = id_name if config_type is None else config_type
        cfgs = coll.find({id_name: id_value}, {"_id": 0})
        return [_mongo_dict_to_config(cfg, config_type) for cfg in cfgs]

    def config_exists(self, id_name, id_value, coll):
        return coll.count_documents({id_name: id_value}, limit=1) != 0

    def delete_config(self, id_name, id_value, coll):
        coll.delete_one({id_name: id_value})

    def get_user(self):
        return self.db_connector.get_user()

    def get_authenticated_users(self):
        return self.db_connector.authenticated_users

    def get_config_db_name(self):
        return self._config_db_name

    def add_config(self, id_name, id_value, cfg, coll):
        config = MessageToDict(cfg)
        config[id_name] = id_value
        coll.insert_one(config)
        return config

    def get_lib_metadata(self, lib_name):
        return self._lib_meta_coll.find_one({"library": lib_name})

    def get_libs_metadata(self, lib_name):
        # TODO: replace get_lib_metadata with this once man.core is old enough to prevent compatibility issues.
        query = {}
        if lib_name:
            if isinstance(lib_name, str):
                query["library"] = lib_name
            elif isinstance(lib_name, list):
                query["library"] = {"$in": lib_name}

        return list(self._lib_meta_coll.find(query))

    def update_lib_metadata(self, name, metadata):
        self._lib_meta_coll.update_one({"library": name}, {"$set": metadata}, upsert=True)

    def delete_libs_metadata(self, lib_name):
        query = dict()
        if isinstance(lib_name, str):
            query["library"] = lib_name
        elif isinstance(lib_name, list):
            query["library"] = {"$in": lib_name}

        self._lib_meta_coll.delete_many(query)

    def upsert_config(self, id_name, id_value, cfg, coll, upsert=True):
        update = {"$set": MessageToDict(cfg)}
        config = coll.find_one_and_update({id_name: id_value}, update=update, upsert=upsert, new=True)
        return config

    def list_libraries(self, lib_name_regex=None):
        query = {"library": {"$regex": lib_name_regex}} if lib_name_regex else {}
        libraries = self._lib_coll.find(query, {"library": 1, "_id": 0})
        return (lib["library"] for lib in libraries)

    def list_storages(self):
        storages = self._storage_coll.find({}, {"storage": 1, "_id": 0})
        return (storage["storage"] for storage in storages)

    def delete_library_config(self, name):
        self._lib_coll.delete_one({"name": name})

    def delete_storage_config(self, storage_name):
        self._storage_coll.delete_one({"storage": storage_name})

    def find_library_config(self, name):
        return self.get_config("library", name, self._lib_coll)

    def find_storage_config(self, name):
        return self.get_config("storage", name, self._storage_coll)

    @property
    def db_connector(self):
        # type: ()->MongoDBConnector
        return self._db_connector


class ArcticcMongoConfigWriter(object):
    def __init__(self, mongo_config: MongoConfigDAO):
        self._dao = mongo_config

    def add_lib_config_coll(self, coll_name="arcticc_lib_config", index="library"):
        return self._add_config_coll(coll_name, index)

    def add_storage_config_coll(self, coll_name="arcticc_storage_config", index="storage"):
        return self._add_config_coll(coll_name, index)

    def _add_config_coll(self, coll_name, index):
        coll = self._dao.get_config_coll(coll_name)
        coll.create_index(index, unique=True, background=True)
        return coll

    def add_storage_config(self, lib_cfg, use_existing_storage=True):
        # Order is important here as storages are shared among many libraries
        # but a library requires a storage to exist
        # add storage configs
        for storage_name, storage_cfg in lib_cfg.storage_by_id.items():
            self.add_storage_config_from_cfg(storage_name, storage_cfg, use_existing_storage)

    def add_library_config(self, lib_name, lib_cfg):
        # add a library config
        if not self._dao.config_exists(id_name="library", id_value=lib_name, coll=self._dao._lib_coll):
            self._dao.add_config(id_name="library", id_value=lib_name, cfg=lib_cfg.lib_desc, coll=self._dao._lib_coll)
        else:
            raise ArcticNativeException(
                "Library {} already exists on {}.".format(lib_name, self._dao._db_connector.env)
            )

    def add_library_and_storage_config(self, lib_name, lib_cfg, use_existing_storage=True):
        self.add_storage_config(lib_cfg, use_existing_storage)
        self.add_library_config(lib_name, lib_cfg)

    def delete_storage_config(self, lib_cfg):
        for storage_id in lib_cfg.lib_desc.storage_ids:
            try:
                self._dao.delete_storage_config(storage_id)
            except Exception as ex:
                raise ArcticNativeException(
                    "Could not delete storage config for lib: {}, ex: {}".format(lib_cfg.lib_desc.name, ex)
                )

    def delete_library_config(self, lib_name):
        try:
            self._dao.delete_library_config(lib_name)
        except Exception as ex:
            raise ArcticNativeException("Could not delete library config for lib: {} (ex:{})".format(lib_name, ex))

    # Updates specified paths of library descriptor
    def update_library_config(self, lib_name, lib_desc, paths):
        update_cfg = LibraryDescriptor()
        field_mask_pb2.FieldMask(paths=paths).MergeMessage(lib_desc, update_cfg)
        self._dao.upsert_config("library", lib_name, update_cfg, self._dao._lib_coll, False)

    def modify_library_config(self, lib_name, lib_cfg):
        self.delete_library_config(lib_name)
        self.add_library_config(lib_cfg.lib_desc.name, lib_cfg)

    def modify_storage_config(self, lib_name, lib_cfg):
        self.delete_storage_config(lib_cfg)
        self.add_storage_config(lib_cfg, use_existing_storage=False)

    def delete_config(self, lib_name, lib_cfg):
        self.delete_library_config(lib_name)
        self.delete_storage_config(lib_cfg)

    def ensure_lib_sharded(self, lib_name):
        self._ensure_index(lib_name)

    def _ensure_index(self, lib_name):
        pass

    def add_storage_config_from_cfg(self, storage_name, storage_cfg, use_existing_storage=True):
        if not self._dao.config_exists(id_name="storage", id_value=storage_name, coll=self._dao._storage_coll):
            self._dao.add_config("storage", storage_name, storage_cfg, self._dao._storage_coll)
        else:
            if not use_existing_storage:
                raise ArcticNativeException(
                    "Storage {} already exists on {}.".format(storage_name, self._dao._db_connector.env)
                )

    @property
    def env(self):
        return self._dao.db_connector.env
