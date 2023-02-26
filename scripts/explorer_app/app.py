from ahl.mongo.hosts import get_mongoose_lib
from ahl.mongo.mongoose.mongoose import NativeMongoose
from arcticc.toolbox.storage import (
    get_library_tool,
    KeyType,
    get_conschecker,
    mem_seg_to_dataframe,
    read_decode,
    df_to_keys,
)
from flask import Flask, render_template, request, url_for, json
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.url_map.strict_slashes = False
env = "mktdatad"
m = NativeMongoose(env, app_name="admin")

"""
TODO: 
factor out the common parts in the templates
refactor the common code
figuring out perms
get symbol info
404 handle things not existing
"""


def key_to_url(key, library):
    if key.key_type == KeyType.TABLE_INDEX:
        return url_for("get_data", library=library, symbol=key.id, version=key.version_id)
    elif key.key_type == KeyType.VERSION:
        return url_for("get_version", library=library, symbol=key.id, version_id=key.version_id)
    elif key.key_type == KeyType.TABLE_DATA:
        # probably just raise for now.
        return url_for(
            "get_dataframe",
            library=library,
            symbol=key.id,
            version=key.version_id,
            start_index=key.start_index,
            end_index=key.end_index,
        )
    else:
        raise Exception("key not supported")


def get_keys_in_segment(lt, key, symbol):
    # ref_key = lt.find_keys_for_id(KeyType.VERSION_REF, symbol)[0]

    ik, index_seg, ref_segment = read_decode(lt, key)
    keys = df_to_keys(symbol, mem_seg_to_dataframe(ref_segment))
    return keys


@app.route("/")
def get_host():
    data = m.list_libraries()

    return render_template("index.html", parent=env, children=data, extra="")


@app.route("/library/<library>")
def get_library(library):
    # TODO: snapshots
    lib = m.get_library(library, use_cache=False)
    symbols = [sym for sym in lib.list_symbols()]
    desc = lib._lib_cfg.lib_desc
    relevant_config_options = {
        "prune_previous_version": getattr(desc.version.write_options, "prune_previous_version"),  # default: False
        "de_duplication": getattr(desc.version.write_options, "de_duplication"),  # default: False,
        "snapshot_dedup": getattr(desc.version.write_options, "snapshot_dedup"),  # default: False
        "dynamic_strings": getattr(desc.version.write_options, "dynamic_strings"),  # default: False
        "recursive_normalizers": getattr(desc.version.write_options, "recursive_normalizers"),  # default: False
        "pickle_on_failure": getattr(desc.version.write_options, "pickle_on_failure"),  # default: False
        "use_tombstones": getattr(desc.version.write_options, "use_tombstones"),  # default: False
        "delayed_deletes": getattr(desc.version.write_options, "delayed_deletes"),  # default: False
        "symbol_list": getattr(desc.version, "symbol_list"),
    }

    return render_template("library.html", parent=library, children=symbols, cfg=relevant_config_options)


@app.route("/library/<library>/symbol/<symbol>")
def get_symbol(library, symbol):
    lib = get_mongoose_lib(f"native://{library}@{env}")
    lt = get_library_tool(lib)
    cc = get_conschecker(lib)
    sym_info = lib.get_info(symbol)

    vref_keys = lt.find_keys_for_id(KeyType.VERSION_REF, symbol)

    res = cc.run([symbol])

    extra_info = {
        "total_versions": len(vref_keys),
        "check_ref": lib.version_store.check_ref_key(symbol),
        "consistency_check": res,
        "fsck": res["missing"] == 0,
    }

    return render_template(
        "symbol.html",
        library=library,
        symbol=symbol,
        symbol_info=sym_info,
        conscheck=res,
        children=vref_keys,
        extra=str(extra_info),
    )


@app.route("/library/<library>/symbol/<symbol>/vref")
def get_version_ref(library, symbol):
    lib = get_mongoose_lib(f"native://{library}@{env}")
    lt = get_library_tool(lib)
    ref_key = lt.find_keys_for_id(KeyType.VERSION_REF, symbol)[0]

    ik, index_seg, ref_segment = read_decode(lt, ref_key)
    cols = df_to_keys(symbol, mem_seg_to_dataframe(ref_segment))

    return render_template("vref.html", library=library, children=cols, to_url=key_to_url, symbol=symbol)


@app.route("/library/<library>/symbol/<symbol>/versions")
def get_all_version(library, symbol):
    lib = get_mongoose_lib(f"native://{library}@{env}")
    lt = get_library_tool(lib)
    version_keys = lt.find_keys_for_id(KeyType.VERSION, symbol)

    return render_template("versions.html", symbol=symbol, library=library, children=version_keys, to_url=key_to_url)


# TODO filter by creation_ts or hash?
@app.route("/library/<library>/symbol/<symbol>/version/<version_id>")
def get_version(library, symbol, version_id):
    lib = get_mongoose_lib(f"native://{library}@{env}")
    lt = get_library_tool(lib)

    all_version_keys = [k for k in lt.find_keys_for_id(KeyType.VERSION, symbol)]
    filtered_key = [v for v in all_version_keys if v.version_id == int(version_id)][0]
    child_keys = get_keys_in_segment(lt, filtered_key, symbol)

    return render_template("version.html", library=library, children=child_keys, symbol=symbol, to_url=key_to_url)


@app.route("/library/<library>/symbol/<symbol>/version_filtered")
def get_version_by_filter(library, symbol):
    def matches_filter(args, key):
        version_id = args.get("version_id")
        creation_ts = args.get("creation_ts")
        content_hash = args.get("content_hash")
        if version_id or creation_ts or content_hash:
            return (
                (key.version_id == version_id) or (key.creation_ts == creation_ts) or (key.content_hash == content_hash)
            )
        else:
            return True

    lib = get_mongoose_lib(f"native://{library}@{env}")
    lt = get_library_tool(lib)

    all_version_keys = [k for k in lt.find_keys_for_id(KeyType.VERSION, symbol)]
    print("all_version_keys=", all_version_keys)
    filtered_key = [v for v in all_version_keys if matches_filter(request.args, v)][0]
    print("fitlered key=", filtered_key)
    child_keys = get_keys_in_segment(lt, filtered_key, symbol)
    # all_index_keys = lt.find_keys_for_id(KeyType.TABLE_INDEX, symbol)

    extra_info = {"total_index_keys": len(child_keys)}
    return render_template("base.html", parent=library, children=child_keys, extra=str(extra_info))


@app.route("/library/<library>/symbol/<symbol>/version/<version>/data/")
def get_data(library, symbol, version):
    lib = get_mongoose_lib(f"native://{library}@{env}")
    lt = get_library_tool(lib)
    all_index_keys = lt.find_keys_for_id(KeyType.TABLE_INDEX, symbol)
    index_key_for_version = [k for k in all_index_keys if k.version_id == int(version)]
    if len(index_key_for_version) == 0:
        raise Exception("Index key not found, possible consistency issue.")
    index_key = index_key_for_version[0]
    keys = get_keys_in_segment(lt, index_key, symbol)

    return render_template("index_key.html", library=library, symbol=symbol, children=keys, to_url=key_to_url)


@app.route("/library/<library>/symbol/<symbol>/version/<version>/dataframe/<start_index>/<end_index>")
def get_dataframe(library, symbol, version, start_index, end_index):
    lib = get_mongoose_lib(f"native://{library}@{env}")
    lt = get_library_tool(lib)
    all_data_keys = lt.find_keys_for_id(KeyType.TABLE_DATA, symbol)
    matching_data_keys = [
        k
        for k in all_data_keys
        if (k.version_id == int(version)) and (k.start_index == int(start_index)) and (k.end_index == int(end_index))
    ]
    if len(matching_data_keys) == 0:
        raise Exception("key not found")
    data_key = matching_data_keys[0]
    read_decode(lt, data_key)
    ik, index_seg, data_segment = read_decode(lt, data_key)
    df = mem_seg_to_dataframe(data_segment)

    return render_template("data.html", library=library, symbol=symbol, dataframe=df.to_json())


if __name__ == "__main__":
    app.run("0.0.0.0", 5388)
