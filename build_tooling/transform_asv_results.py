import pandas as pd
from arcticdb.storage_fixtures.s3 import real_s3_from_environment_variables
import json
from pathlib import Path
from arcticdb import Arctic
from arcticdb.version_store.library import Library
from argparse import ArgumentParser


def setup_machine_folder(json_data, machine_path):
    machine_path.mkdir()
    with open(machine_path / "machine.json", "w") as out:
        machine_data = json_data["params"]
        machine_data["version"] = 1
        json.dump(machine_data, out, indent=4, default=str)


def df_to_asv_json(results_df: pd.DataFrame):
    new_df = results_df.copy()
    new_df["date"] = (pd.to_datetime(results_df["date"]).astype(int) // 1000000).astype(
        object
    )
    new_df["version"] = results_df["version"].astype(object)

    metadata = {
        "commit_hash": new_df["commit_hash"].iloc[0],
        "env_name": new_df["env_name"].iloc[0],
        "date": new_df["date"].iloc[0],
        "params": eval(new_df["params"].iloc[0]),
        "python": new_df["python"].iloc[0],
        "requirements": eval(new_df["requirements"].iloc[0]),
        "env_vars": eval(new_df["env_vars"].iloc[0]),
        "result_columns": eval(new_df["result_columns"].iloc[0]),
        "durations": eval(new_df["durations"].iloc[0]),
        "version": new_df["version"].iloc[0],
    }

    json_data = {**metadata, "results": {}}
    for _, row in new_df.iterrows():
        test_name = row["test_name"]
        res_data = eval(row["results"])

        json_data["results"][test_name] = res_data
    return json_data


def asv_json_to_df(full_path: str) -> pd.DataFrame:
    with open(full_path, "r") as f:
        data = json.load(f)

    results_list = []
    for test_name, test_results in data["results"].items():
        flattened_data = pd.json_normalize(
            {"test_name": test_name, "results": str(test_results)}
        )
        flattened_data["commit_hash"] = data["commit_hash"]
        flattened_data["env_name"] = data["env_name"]
        flattened_data["date"] = data["date"]
        flattened_data["params"] = str(data["params"])
        flattened_data["python"] = data["python"]
        flattened_data["requirements"] = str(data["requirements"])
        flattened_data["env_vars"] = str(data["env_vars"])
        flattened_data["result_columns"] = str(data["result_columns"])
        flattened_data["durations"] = str(data["durations"])
        flattened_data["version"] = data["version"]
        results_list.append(flattened_data)

    results = pd.concat(results_list, ignore_index=True)
    results["date"] = pd.to_datetime(data["date"], unit="ms")
    return results


def get_results_lib(arcticdb_client_override, arcticdb_library):
    if arcticdb_client_override is not None:
        ac = Arctic(arcticdb_client_override)
    else:
        ac = (
            real_s3_from_environment_variables(shared_path=True)
            .create_fixture()
            .create_arctic()
        )

    lib = ac.get_library(arcticdb_library, create_if_missing=True)
    return lib


def save_asv_results(lib, json_path):
    for file_path in json_path.glob("**/*.json"):
        if "benchmark" in file_path.name or "machine" in file_path.name:
            continue
        full_path = str(file_path)
        commit_hash = file_path.name.split("-")[0]
        print(f"Processing {full_path}")
        df = asv_json_to_df(full_path)
        lib.write(commit_hash, df)


def extract_asv_results(lib, json_path):
    syms = lib.list_symbols()

    for sym in syms:
        print(f"Processing {sym}...")
        results_df = lib.read(sym).data
        json_data = df_to_asv_json(results_df)
        full_json_path = get_result_json_path(json_path, sym, json_data)

        print(f"Writing {full_json_path}...")
        with open(full_json_path, "w") as out:
            json.dump(json_data, out, indent=4, default=str)


def get_result_json_path(json_path, sym, json_data):
    env_name = json_data["env_name"]
    machine = json_data["params"]["machine"]
    machine_path = json_path / machine
    if not machine_path.exists():
        setup_machine_folder(json_data, machine_path)

    result_json_name = f"{sym}-{env_name}.json"
    full_json_path = json_path / machine / result_json_name
    return full_json_path


if __name__ == "__main__":
    # Add argparse to specify the path
    parser = ArgumentParser()
    parser.add_argument(
        "--results_path",
        help="Path to the asv json files",
        default="python/.asv/results",
    )
    parser.add_argument(
        "--arcticdb_client_override",
        help="Override the path to the arcticdb client to use for writing the results, used for testing",
        default=None,
    )
    parser.add_argument(
        "--arcticdb_library",
        help="Override the name of the library to use for writing the results, used for testing/getting results for branches other than master",
        default="asv_results",
    )
    parser.add_argument(
        "--mode",
        help="Mode to run the script in, either 'save' or 'extract', used to save or extract the results",
    )

    args = parser.parse_args()
    json_path = Path(args.results_path)
    results_lib = get_results_lib(args.arcticdb_client_override, args.arcticdb_library)

    if args.mode == "save":
        save_asv_results(results_lib, json_path)
    elif args.mode == "extract":
        extract_asv_results(results_lib, json_path)
    else:
        raise ValueError(f"Invalid mode {args.mode}, must be 'save' or 'extract'")
