from urllib.parse import quote_plus

from arcticdb.version_store.helper import *
from arcticdb.version_store.helper import extract_lib_config as _extract_lib_config
from arcticdb.version_store.helper import create_test_lmdb_cfg as create_local_lmdb_cfg
from arcticdb.version_store.helper import (
    ArcticMemoryConfig,
    ArcticcFileConfig,
    ArcticConfig,
    get_s3_proto,
    get_storage_for_lib_name,
)

from arcticc.pb2.storage_pb2 import (
    EnvironmentConfigsMap,
    EnvironmentConfig,
    LibraryConfig,
    LibraryDescriptor,
    VariantStorage,
    Permissions,
    NoCredentialsStore,
)

from arcticc.pb2.mongo_storage_pb2 import Config as MongoConfig

from arcticdb.config import *  # for backward compat after moving to config
from arcticdb.exceptions import ArcticNativeException, LibraryNotFound
from arcticdb.version_store._store import NativeVersionStore
from arcticdb.preconditions import check

from arcticdb.authorization.permissions import perms_to_openmode

from arcticc.exceptions import CredentialsException
from man.arcticdb.pb_util import ARCTIC_NATIVE_PROTO_TYPE_URL
from man.arcticdb.config import Defaults

ArcticcLocalConf = ArcticcFileConfig
ArcticcMemConf = ArcticMemoryConfig


def _alter_mongo_storage_lib_config(lib_config, connector, uri_builder):
    # type: (LibraryConfig, MongoDBConnector, Callable)->None
    """Deduce the connection uri based on the connector and the library name.

    Parameters
    ----------
    lib_config library config that potentially contains a mongo storage
    connector mongo_db_connector used to connect and authenticate to the db
    """
    check(connector is not None, "Cannot alter mongo config without connector")
    for sid, storage in lib_config.storage_by_id.items():
        if not storage.config.type_url.endswith("arcticc.pb2.mongo_storage_pb2.Config"):
            continue

        mongo_cfg = MongoConfig()
        storage.config.Unpack(mongo_cfg)
        if mongo_cfg.uri:
            return  # already configured

        try:
            db_name = "arcticc_{}".format(lib_config.lib_desc.name.split(".")[0])
            db = connector.get_db(db_name)
            mongo_cfg.uri = uri_builder(db)
        except CredentialsException:
            try:
                # Try to auth against admin db
                admin_db_name = "admin"
                admin_db = connector.get_db(admin_db_name)
                mongo_cfg.uri = uri_builder(admin_db)
            except CredentialsException:
                raise CredentialsException("Failed to authenticate against {} db".format(db_name))
        storage.config.Pack(mongo_cfg, type_url_prefix=ARCTIC_NATIVE_PROTO_TYPE_URL)


def _build_uri_from_db(db):
    def hostport(node):
        return "{}:{}".format(node[0], node[1])

    nodes = ",".join([hostport(n) for n in db.client.nodes])
    if db.name in db.client._MongoClient__all_credentials:
        cred = db.client._MongoClient__all_credentials[db.name]
    else:
        raise CredentialsException("No credentials found in {}".format(db.name))
    return "mongodb://{user}:{pwd}@{nodes}/?authSource={db}".format(
        user=quote_plus(cred.username), pwd=quote_plus(cred.password), nodes=nodes, db=db.name
    )


def _add_lib_desc_to_env(env, lib_name, sid, description=None, lib_type="VersionStore", prefer_native=False):
    # type: (EnvironmentConfigsMap, LibName, StorageId, Optional[AnyStr], Optional[AnyStr], bool)->None
    if lib_name in env.lib_by_path:
        raise ArcticNativeException("Library {} already configured in {}".format(lib_name, env))
    lib_desc = env.lib_by_path[lib_name]
    lib_desc.storage_ids.append(sid)
    lib_desc.name = lib_name
    if description:
        lib_desc.description = description
    lib_desc.prefer_native_library_on_name_collision = prefer_native


def add_mongo_library_to_env(
    cfg, lib_name, env_name, uri=None, description=None, lib_type="VersionStore", prefer_native=False
):
    env = cfg.env_by_id[env_name]
    mongo = MongoConfig()
    if uri is not None:
        mongo.uri = uri

    sid, storage = get_storage_for_lib_name(lib_name, env)
    storage.config.Pack(mongo, type_url_prefix="cxx.arctic.org")
    _add_lib_desc_to_env(env, lib_name, sid, description, lib_type, prefer_native)


def lib_desc_has_credentials_store(lib_desc):
    return lib_desc.credentials_store.WhichOneof("store_type") is not None and not lib_desc.credentials_store.HasField(
        "nostore"
    )


def _add_storage_to_env(env, lib_name, sid):
    lib_desc = env.lib_by_path[lib_name]
    lib_desc.storage_ids.append(sid)


def _add_backup_storage_to_env(env, lib_name, sid):
    lib_desc = env.lib_by_path[lib_name]
    lib_desc.backup_storage_ids.append(sid)


def add_s3_storage_to_env(
    cfg,
    lib_name,
    env_name,
    credential_name,
    credential_key,
    bucket_name=Defaults.DEFAULT_S3_BUCKET,
    endpoint=Defaults.DEFAULT_S3_ENDPOINT,
    with_prefix=True,
    is_backup_storage=False,
    is_https=False,
    is_vast=False,
    region=None,
    use_virtual_addressing=False,
):
    env = cfg.env_by_id[env_name]
    is_vast = is_vast or Defaults.DEFAULT_VAST_ENDPOINT_TOKEN in bucket_name
    sid, storage = get_s3_proto(
        cfg=cfg,
        lib_name=lib_name,
        env_name=env_name,
        credential_name=credential_name,
        credential_key=credential_key,
        bucket_name=bucket_name,
        endpoint=endpoint,
        with_prefix=with_prefix,
        is_https=is_https,
        is_vast=is_vast,
        region=region,
        use_virtual_addressing=use_virtual_addressing,
    )

    if is_backup_storage:
        _add_backup_storage_to_env(env, lib_name, sid)
    else:
        _add_storage_to_env(env, lib_name, sid)


class ArcticcMongoConf(ArcticConfig):
    def __init__(self, dao):
        # type: (MongoConfigDAO)->None
        self._dao = dao
        self.set_mongo_connector(dao.db_connector)
        self.set_uri_builder(_build_uri_from_db)

    def __getitem__(self, lib_name):
        # type: (LibName)->NativeVersionStore
        return self.get_native_store(lib_name)

    def _alter_mongo_storage(self, lib_cfg):
        if hasattr(self, "mongo_connector"):
            _alter_mongo_storage_lib_config(lib_cfg, self.mongo_connector, self.uri_builder)

    def get_native_store(self, lib_name, credentials_helper=None):
        # type: (LibName, Optional[Callable])->NativeVersionStore
        lib_cfg, open_mode = self.get_lib_config_and_open_mode(lib_name, credentials_helper=credentials_helper)
        check(lib_cfg is not None, "Missing library {} in {}", lib_name, self.env)
        return NativeVersionStore.create_store_from_lib_config(lib_cfg, self.env, open_mode)

    def default_credentials_helper(self, lib_cfg):
        perms = Permissions()
        perms.write.enabled = True
        for sid in lib_cfg.lib_desc.storage_ids:
            try:
                found_cfg = self._dao.find_storage_config(sid)
                check(found_cfg is not None, "Config for storage id={} does not exist in {}", sid, self.env)
                lib_cfg.storage_by_id[sid].CopyFrom(found_cfg)
            except Exception as e:
                raise ArcticNativeException("Failed to get config for storage {}.\n{}".format(sid, str(e)))

        self._alter_mongo_storage(lib_cfg)
        return lib_cfg, perms

    def get_lib_config_without_storage(self, lib_name):
        # type: (LibName)->LibraryConfig
        lib_cfg = LibraryConfig()
        try:
            found_cfg = self._dao.find_library_config(lib_name)
            check(found_cfg is not None, "Config for lib_name={} does not exist in {}", lib_name, self.env)
            lib_cfg.lib_desc.CopyFrom(found_cfg)
            return lib_cfg
        except Exception as e:
            raise ArcticNativeException("Failed to get config for library {}.\n{}".format(lib_name, str(e)))

    def get_lib_config_and_open_mode(self, lib_name, credentials_helper=None):
        # type: (LibName, Callable)->LibraryConfig
        lib_cfg = self.get_lib_config_without_storage(lib_name)

        if lib_desc_has_credentials_store(lib_cfg.lib_desc):
            if credentials_helper is None:
                raise CredentialsException(
                    "No credentials helper, when credentials store was set: {}".format(
                        lib_cfg.lib_desc.credentials_store
                    )
                )

            lib_cfg_with_storage, perms = credentials_helper(lib_cfg)

        else:
            lib_cfg_with_storage, perms = self.default_credentials_helper(lib_cfg)

        open_mode = perms_to_openmode(perms)
        return lib_cfg_with_storage, open_mode

    def _get_lib_config_admin(self, lib_name, credentials_helper):
        # type: (LibName, Callable)->LibraryConfig
        lib_cfg = self.get_lib_config_without_storage(lib_name)

        if lib_desc_has_credentials_store(lib_cfg.lib_desc):
            if credentials_helper is None:
                raise CredentialsException(
                    "No credentials helper, when credentials store was set: {}".format(
                        lib_cfg.lib_desc.credentials_store
                    )
                )
            storage_dao, credentials_db = credentials_helper._get_matching_helper(lib_cfg)._get_dao_and_database_name(
                lib_cfg
            )
            for sid in lib_cfg.lib_desc.storage_ids:
                try:
                    found_cfg = storage_dao.find_storage_config(sid)
                    check(found_cfg is not None, "Config for storage id={} does not exist in {}", sid, credentials_db)
                    lib_cfg.storage_by_id[sid].CopyFrom(found_cfg)
                except Exception as e:
                    raise CredentialsException("Failed to get config for storage {}.\n{}".format(sid, str(e)))

            lib_cfg_with_storage = lib_cfg
            perms = Permissions()
            perms.write.enabled = True

        else:
            lib_cfg_with_storage, perms = self.default_credentials_helper(lib_cfg)

        open_mode = perms_to_openmode(perms)
        return lib_cfg_with_storage, open_mode

    def get_backup_storage_for_cfg(self, lib_cfg):
        for sid in lib_cfg.lib_desc.backup_storage_ids:
            try:
                found_cfg = self._dao.find_storage_config(sid)
                check(
                    found_cfg is not None,
                    "Config for backup storage id={} does not exist in {}",
                    sid,
                    self._dao.get_config_db_name(),
                )
                lib_cfg.storage_by_id[sid].CopyFrom(found_cfg)
            except Exception as e:
                raise CredentialsException("Failed to get config for Backup storage {}.\n{}".format(sid, str(e)))

    def _prefer_native_on_name_collision(self, lib_name):
        lib_cfg = LibraryConfig()
        try:
            found_cfg = self._dao.find_library_config(lib_name)
            check(found_cfg is not None, "Config for lib_name={} does not exist in {}", lib_name, self.env)
            # Protobuf defaults to False if not set which is what we want here.
            return lib_cfg.lib_desc.prefer_native_library_on_name_collision
        except LibraryNotFound:
            # It's fine if the lib is not found as this check avoids the user from checking for library exists
            # before calling this.
            return False

    @property
    def env(self):
        return self._dao.db_connector.env

    def list_libraries(self, regex=None):
        return list(self._dao.list_libraries(regex))

    def library_exists(self, lib_name):
        # type: (AnyStr)->bool
        return self._dao.find_library_config(lib_name) is not None
