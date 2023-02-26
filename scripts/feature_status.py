import random

from ahl.mongo.mongoose import NativeMongoose
from man.arctic.config import NativeMongooseConfigHelper, set_config_option_for_library

host = "research"

nm = NativeMongoose(host)

write_feature_flags = [
    "prune_previous_version",  # default: False
    "de_duplication",  # default: False
    "dynamic_strings",  # default: False
    "recursive_normalizers",  # default: False
    "pickle_on_failure",  # default: False
    "use_tombstones",  # default: False
]

version_feature_flags = ["symbol_list"]  # False


def has_symbol_list_function(lib_cfg):
    print("{}:\t{}".format(lib_cfg.lib_desc.name, lib_cfg.lib_desc.version.symbol_list))


def run_function_on_lib_config(lib_name, func):
    config_helper = NativeMongooseConfigHelper(host)
    config_reader = config_helper.get_config_reader()
    cfg, open_mode = config_reader.get_lib_config_and_open_mode(lib_name)
    func(cfg)


def predicate_function(lib_cfg):
    storage_id = lib_cfg.lib_desc.storage_ids[0]
    print(storage_id)


def get_feature_value_in_config(host, lib_name, feature):
    config_helper = NativeMongooseConfigHelper(host)
    config_reader = config_helper.get_config_reader()
    cfg = config_reader.get_lib_config_without_storage(lib_name)
    if feature in version_feature_flags:
        return getattr(cfg.lib_desc.version, feature)
    elif feature in write_feature_flags:
        return getattr(cfg.lib_desc.version.write_options, feature)


def get_arcticc_version_for_user():
    pass


def get_rollout_status(feature="symbol_list", env="research", restrict_libs=None, n_sample_libs=None):
    m = NativeMongoose(env)
    all_libs = m.list_libraries()
    sample_size = min(n_sample_libs, len(all_libs)) if n_sample_libs else len(all_libs)
    if restrict_libs:
        sample_libs = restrict_libs if isinstance(restrict_libs, list) else [restrict_libs]
    else:
        sample_libs = random.sample(all_libs, sample_size)
    print("Total libs as sample in {}: {}".format(env, len(sample_libs)))
    libs_with_feature_enabled = []

    for lib_name in sample_libs:
        try:
            # TODO: get the entire config collection from Mongo rather than multiple reads?
            feature_value = get_feature_value_in_config(host, lib_name, feature)
        except Exception as e:
            # TODO: Handle private libs
            print("Failed to get config for: {} due to {}".format(lib_name, e))
            continue
        if feature_value:
            # print('feature_value=', feature_value, 'for', lib_name)
            libs_with_feature_enabled.append(lib_name)

    print(
        "{} is enabled in {}/{} libraries ({}%)".format(
            feature,
            len(libs_with_feature_enabled),
            len(sample_libs),
            round(float(len(libs_with_feature_enabled) / len(sample_libs)) * 100.0, 2),
        )
    )
    return libs_with_feature_enabled


def get_top_group_with_missing_feature(feature="use_tombstones", host="research"):
    m = NativeMongoose(host)
    res = get_rollout_status(feature, host)
    all_libs = m.list_libraries()
    remaining = set(all_libs) - set(res)
    prefixes = [x.split(".")[0] for x in remaining]
    from collections import Counter

    grp = Counter(prefixes)
    print("largest 20 groups with missing feature: ", grp.most_common(20))
    return grp, remaining


def set_feature_for_libs(libs, feature, value=True, env="research", dry_run=True):
    sample_libs = libs if isinstance(libs, list) else [libs]
    for lib in sample_libs:

        try:
            final_cfg = set_config_option_for_library(lib, env, feature, value=value, dry_run=dry_run)
            if dry_run:
                print("dry_run was enabled, Final cfg will be: ", final_cfg)
            else:
                print("Config changed to:", final_cfg)
        except Exception as e:
            print("failed for ", lib, "due to", e)


def set_feature_for_libs_with_username(username: str, nm: NativeMongoose, feature: str, env, dry_run):
    target_libs = [l for l in nm.list_libraries() if l.startswith(username)]
    print("enabling {} for libs: {}".format(feature, target_libs))
    set_feature_for_libs(target_libs, feature, value=True, env=env, dry_run=dry_run)


manual_groups = {
    "arctic_native": ["pverma", "skhare", "wdealtry"],
    "data_engineering": ["enazif", "amaher", "rseaman", "tmace", "mhertz", "vmereuta", "jpatti"],
}


def enable_feature_for_group(group_name: str, feature: str, env: str = "research", dry_run: bool = True):
    m = NativeMongoose(env)
    users_in_group = manual_groups[group_name]
    print("users in group: ", users_in_group)
    for user in users_in_group:
        set_feature_for_libs_with_username(user, m, feature, env, dry_run)


excluded_prefixes = [
    "centaur",
    "security_master",
    "datascience",
    "gpm",
    "glg",
    "risk",
    "equities",
    "__test",
    "kestrel",
    "spark",
    "resvol",
    "ra",
    "ir",
]


def get_random_libs(env, excluded_prefixes, count):
    all_libs = NativeMongoose(env).list_libraries()
    remaining_libs = [l for l in all_libs if l.split(".")[0] not in excluded_prefixes and not l.endswith("backup")]

    return random.sample(remaining_libs, count) if count < len(remaining_libs) else remaining_libs


def get_random_libs_without_tombstones(env, excluded_prefixes, count):
    valid_libs = []
    m = NativeMongoose(env)
    while len(valid_libs) < count:
        sample_libs = get_random_libs(env, excluded_prefixes, count)

        def has_tombstone_not_enabled_and_s3(lib_name):
            try:
                lib = m[lib_name]
                return (
                    not lib._lib_cfg.lib_desc.version.write_options.use_tombstones
                ) and lib.get_backing_store() == "s3_storage"
            except Exception as e:
                return False

        filtered = [lib for lib in sample_libs if has_tombstone_not_enabled_and_s3(lib)]
        # nothing left
        if len(filtered) == 0:
            break

        valid_libs += filtered

    return valid_libs


# todo check if feature isn't already enabled
# sample_libs = get_random_libs_without_tombstones("research", excluded_prefixes, 10000)
# sample_libs = get_random_libs("research", excluded_prefixes, 30)
# print("random=", sample_libs)
# input("{} libs look good for tombstones?".format(len(sample_libs)))
# set_feature_for_libs_with_username('djepson', NativeMongoose('research'), "use_tombstones", "research", False)
# set_feature_for_libs_with_username('djepson', NativeMongoose('research'), "prune_previous_version", "research", False)
# set_feature_for_libs(sample_libs, "use_tombstones", dry_run=False)
# set_feature_for_libs(sample_libs, "prune_previous_version", dry_run=False)
# =======
# # get_random_libs("research", excluded_prefixes, 10)
# get_rollout_status("prune_previous_version", "research")
# get_rollout_status("use_tombstones", "research")
# >>>>>>> works

# enable_feature_for_group('data_engineering', 'prune_previous_version', 'research', dry_run=False)
# enable_feature_for_group('data_engineering', 'use_tombstones', 'research', dry_run=False)
# enable_feature_for_group('data_engineering', 'symbol_list', 'research', dry_run=False)

# get_rollout_status('use_tombstones')
# for feature in write_feature_flags:
#     get_rollout_status('symbol_list')

# set_feature_for_libs('skhare.tombtest1', 'use_tombstones', value=True, dry_run=False)


# write_feature_flags = [
#     "prune_previous_version",  # default: False
#     "de_duplication",  # default: False
#     "dynamic_strings",  # default: False
#     "recursive_normalizers",  # default: False
#     "pickle_on_failure",  # default: False
#     "use_tombstones",  # default: False
# ]
#
# version_feature_flags = [
#     "symbol_list",  # False
# ]
