import pandas as pd
import json
from pathlib import Path

from arcticdb.storage_fixtures.s3 import real_s3_from_environment_variables


def setup_machine_folder(json_data, machine_path):
    machine_path.mkdir()
    with open(machine_path / "machine.json", "w") as out:
        machine_data = json_data["params"]
        # machine_data.pop("python")
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


if __name__ == "__main__":
    json_path = Path("python/.asv/results")

    ac = (
        real_s3_from_environment_variables(shared_path=True)
        .create_fixture()
        .create_arctic()
    )
    lib = ac.get_library("test_asv_results", create_if_missing=True)
    syms = lib.list_symbols()

    for sym in syms:
        print(f"Processing {sym}...")
        results_df = lib.read(sym).data

        json_data = df_to_asv_json(results_df)

        env_name = json_data["env_name"]
        machine = json_data["params"]["machine"]
        machine_path = json_path / machine
        if not machine_path.exists():
            setup_machine_folder(json_data, machine_path)

        result_json_name = f"{sym}-{env_name}.json"
        full_json_path = json_path / machine / result_json_name
        print(f"Writing {full_json_path}...")

        with open(full_json_path, "w") as out:
            json.dump(json_data, out, indent=4, default=str)
