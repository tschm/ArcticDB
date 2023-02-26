import pandas as pd
from ahl.mongo.mongoose import NativeMongoose
import ahl.dateutil as adu

big_data_db = NativeMongoose("research").get_library("example.big_data")
now = pd.Timestamp("now")
sub_range = big_data_db.read(
    "many_floats", columns=["c0", "c400", "c10000"], date_range=adu.DateRange(20200101, 20200201)
).data
print("Read time: {}".format(pd.Timestamp("now") - now))
