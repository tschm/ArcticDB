from ahl.mongo import NativeMongoose
from arcticc.toolbox.storage import KeyType, get_library_tool


def find_leaked_version_keys(lib_name, env, syms, delete_version_keys=False):
    lib = NativeMongoose(env)[lib_name]
    lt = get_library_tool(lib)
    for sym in syms:
        all_version_keys = lt.find_keys_for_id(KeyType.VERSION, sym)
        all_version_ids = [v.version_id for v in all_version_keys]
        good_version_ids = [v["version"] for v in lib.list_versions(sym)]
        to_del = set(all_version_ids) - set(good_version_ids)
        print("sym=", sym, "to_del=", to_del)
        # Now delete the to_del version_ids
        for v_key in all_version_keys:
            if v_key.version_id in to_del:
                print("to be deleted: symbol: {}, key: {}".format(sym, v_key))
                if delete_version_keys:
                    lt.remove(v_key)


def fix_ref_keys(lib_name, env, syms):
    lib = NativeMongoose(env)[lib_name]
    for sym in syms:
        lib.version_store.fix_ref_key(sym)


def main():
    symbols = [
        "data_graph_regional_v1.Region.EU/els_barra_universe_args_0",
        "data_graph_regional_v1.Region.JP/barra_JPE4L/factor_exposure_by_day/201906",
        "data_graph_regional_v1.Region.JP/ibes_v1_monthly_consensus/est_rev_down_fy2",
        "data_graph_regional_v1.Region.US/download_filter/available_stocks",
    ]

    host = "glg-ar-data-pre"
    lib_name = "glg.equities"
    find_leaked_version_keys(lib_name, host, symbols)


if __name__ == "__main__":
    main()
