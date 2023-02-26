from ahl.mongo import Mongoose

from ahl.professorjenkins import jenkins_stats_collector as jsc
import pandas as pd

BUILD_URL = "http://ci.res.ahl/build/api/json"
IGNORE_TEAMS = ["Adaero", "ADMIN", "Auto-Generated%20Jobs", "Execution", "Infra", "DATA", "RISK", "Man%20Risk", "AHLPA"]
FILTER_TEAMS = ["DATA"]
global overall_build_data
overall_build_data = []


def extract_and_store_build_data(parent_job_url, build_json):
    build_url = build_json["url"]
    if "arctic" in build_url:
        print("found arctic")
        overall_build_data.append(build_url)


jsc.extract_and_store_build_data = extract_and_store_build_data


def process_all_builds_in_job(job_json):
    job_url = job_json["url"]
    # Jenkins returns most recent builds first]. Process in this order and limit to a sensible number.
    for build in job_json["builds"][:20]:
        process_build(job_url, build["url"])


def process_build(parent_job_url, build_url):
    try:
        print("process build:", parent_job_url, build_url)
        jsc.process_new_build(parent_job_url, build_url)
    except Exception as e:
        jsc.print_trim(f"Could not process build ({build_url} due to {repr(e)}")
        raise e


def get_build_times(job_url):
    try:
        tests = {}
        print("job url=", job_url)
        test_report_url = job_url + "testReport/api/json"
        if "arctic" not in test_report_url:
            return {}
        test_report_json = jsc.get_as_json(test_report_url)
        tests = {}
        for suite in test_report_json.get("suites", []):
            for case in suite.get("cases", []):
                tests[case["name"]] = case["duration"]
        return tests
    except:
        return {}


res = process_all_builds_in_job(
    jsc.get_as_json("http://ci.res.ahl/build/job/DATA/job/arcticc_pipeline/job/master/api/json")
)

print("overall=", overall_build_data)
build_times = {x: get_build_times(x) for x in overall_build_data}
build_times = {k: [(k1, v1) for k1, v1 in v.items()] for k, v in build_times.items()}

build_times_list = []
for k, v in build_times.items():
    for k1, v1 in v:
        build_times_list.append((k, k1, v1))

df = pd.DataFrame(build_times_list)
df["build"] = df[0].apply(lambda x: "/".join(x.split("/")[:-2]))
df["team"] = df[0].apply(lambda x: x.split("/")[5])
df["time (mins)"] = df[2] / 60
# df = df[~df['team'].isin(IGNORE_TEAMS)]=
# df1 = df[df['team'].isin(FILTER_TEAMS)]
print("df1=", df)
# regression_df = df[df.build.str.startswith("http://ci.res.ahl/build/job/Signals/job/ahl.strategies-strategy-runs") | df.build.str.startswith("http://ci.res.ahl/build/job/Core%20Strategies/job/Strategy%20Regression%20Runs")]
# df = df[~df.build.str.startswith("http://ci.res.ahl/build/job/Signals/job/ahl.strategies-strategy-runs")]
# df = df[~df.build.str.startswith("http://ci.res.ahl/build/job/Core%20Strategies/job/Strategy%20Regression%20Runs")]
#
# pd.set_option('display.max_rows', 100)
df.groupby(["team", "build", 1]).mean().sort_values(by=2, ascending=False).head(100)

# regression_df.groupby(['team', 'build', 1]).mean().sort_values(by=2, ascending=False).head(100)

"""
                                                                                                    time (mins)
team build                                              1
DATA http://ci.res.ahl/build/job/DATA/job/arcticc_pi... test_random_scenario                                   4.633284
                                                        Wait                                                   2.034119
                                                        test_numeric_update_case2                              1.837362
                                                        test_many_version_store_mongo                          1.217132
                                                        test_delete_library_tool                               0.833500
                                                        test_append_stress                                     0.807383
                                                        test_numeric_update_case                               0.680937
                                                        test_delete_snapshot                                   0.680225
                                                        test_storage_sync_job                                  0.626434
                                                        test_backup_job                                        0.610793
                                                        test_rt_df[sec_rtns]                                   0.607246
                                                        test_rt_df[vol_vega]                                   0.593921
                                                        Compact                                                0.551947
                                                        test_stress[high_entropy]                              0.459853
                                                        test_read_write_flat_memory                            0.452681
                                                        Segment                                                0.365728
                                                        test_stress_version_map_compact                        0.346422
                                                        test_write_parallel_stress_schema_change_strings       0.296013
                                                        test_change_int_to_float                               0.282395
                                                        test_large_pickled_obj                                 0.244516
                                                        test_many_version_store                                0.223360
                                                        test_rt_df[voltaetf_pnl_frame]                         0.212906
                                                        test_filter_pre_epoch_date                             0.210163
                                                        StressBatchReadUncompressed                            0.145334
                                                        test_with_symbol_list                                  0.135384
                                                        test_storage_mover_symbol_tree                         0.135255
                                                        test_version_compaction_job                            0.129479
                                                        test_really_large_df                                   0.129429
                                                        Simple                                                 0.108372
                                                        test_stress[low_entropy]                               0.103070


"""
