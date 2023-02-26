from arcticc.config import load_envs_config, save_envs_config, _DEFAULT_ENVS_PATH
from arcticc.version_store.helper import ArcticcLocalConf
import os.path as osp
from arcticc.pb2.storage_pb2 import EnvironmentConfigsMap, NoCredentialsStore
from man.arctic.config import NativeMongooseConfigHelper
from ahl.mongo.mongoose import NativeMongoose

env = "mktdatap"
lib_name = "vol.voltaetf"
conf_path = "/users/is/wdealtry/workspace/arcticc/nogit/envs.yaml"
make_writable = False

if osp.exists(conf_path):
    existing_config = load_envs_config(conf_path=_DEFAULT_ENVS_PATH)
else:
    existing_config = EnvironmentConfigsMap()

config_helper = NativeMongooseConfigHelper(env)
config_reader = config_helper.get_config_reader()
nm = NativeMongoose(env)
credentials_helper = nm._credentials_helper

cfg, open_mode = config_reader.get_lib_config_and_open_mode(lib_name, credentials_helper=credentials_helper)

env_cfg = existing_config.env_by_id[env]
env_cfg.lib_by_path[lib_name].CopyFrom(cfg.lib_desc)

if make_writable:
    env_cfg.lib_by_path[lib_name].credentials_store.nostore.enabled = True

for storage_id in cfg.lib_desc.storage_ids:
    env_cfg.storage_by_id[storage_id].CopyFrom(cfg.storage_by_id[storage_id])

save_envs_config(existing_config, conf_path)
