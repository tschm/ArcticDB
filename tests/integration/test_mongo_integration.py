from pandas.testing import assert_frame_equal
import numpy as np
import pandas as pd


def test_mongo_write_read(mongo_version_store):
    arr = np.random.random(100000)
    df = pd.DataFrame({"xx": arr})
    mongo_version_store.write("test", df)
    test_df = mongo_version_store.read("test")
    assert_frame_equal(df, test_df.data)
