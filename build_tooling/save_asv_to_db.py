import pandas as pd
from arcticdb.storage_fixtures.s3 import real_s3_from_environment_variables
import json
from pathlib import Path


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


def save_asv_to_arcticdb(df: pd.DataFrame, sym_name: str):
    # TODO: Make this more reusable
    ac = (
        real_s3_from_environment_variables(shared_path=True)
        .create_fixture()
        .create_arctic()
    )
    lib = ac.get_library("test_asv_results", create_if_missing=True)
    # pickled_df = df.to_pickle()
    lib.write(sym_name, df)


if __name__ == "__main__":
    json_path = Path("python/.asv/results")

    for file_path in json_path.glob("**/*.json"):
        if "benchmark" in file_path.name or "machine" in file_path.name:
            continue
        full_path = str(file_path)
        commit_hash = file_path.name.split("-")[0]
        print(f"Processing {full_path}")
        df = asv_json_to_df(full_path)
        save_asv_to_arcticdb(df, commit_hash)
