# requires fastparquet, which requires pytest-runner


import sys

# print(sys.path)
sys.path.append("/opt/arcticc")
from arcticc.version_store.helper import (
    ArcticcMemConf,
    add_lmdb_library_to_env,
    EnvironmentConfigsMap,
    arctic_native_path,
)


import pandas as pd
import time
from pandas.util.testing import assert_frame_equal

cfg = EnvironmentConfigsMap()
add_lmdb_library_to_env(cfg, lib_name="my.lib", description="Great lib")
arcticc = ArcticcMemConf(cfg)
version_store = arcticc["my.lib"]

pq_read_start = time.time()
test_df = pd.io.parquet.read_parquet("/scratch/user/wdealtry/pnl_vectors.parquet")
# test_df = pd.read_pickle('/opt/arcticc/.nogit/pnl_vectors.pkl')
pq_read_end = time.time()
print("Parquet read time taken %f" % (pq_read_end - pq_read_start))
start = time.time()
stream_id = "test_stream"
# raw_input('Press enter to continue: ')
version = version_store.write(stream_id, test_df)
end = time.time()
print("Arctic write time  %f" % (end - start))

pq_start = time.time()
test_df.to_parquet("/scratch/user/wdealtry/pnl_vectors_out.parquet", engine="fastparquet")
# test_df.to_parquet('/opt/arcticc/.nogit/pnl_vectors_out.parquet', engine='fastparquet')
pq_end = time.time()
print("Parquet write time %f" % (pq_end - pq_start))


us_read_start = time.time()
read_df = version_store.read(stream_id)
us_read_end = time.time()

print("Arctic read time %f" % (us_read_end - us_read_start))

assert_frame_equal(test_df, read_df)
