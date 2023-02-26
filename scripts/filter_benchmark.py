from ahl.dateutil import DateRange
import sys

sys.path.append("/users/is/wdealtry/workspace/arcticc")
from ahl.mongo import NativeMongoose
from arcticc.version_store.processing import QueryBuilder
from datetime import datetime
import time

DATE_RANGE = DateRange(datetime(2021, 1, 1), datetime(2021, 12, 31))
COLUMNS = [
    "NotionalUSD",
    "SecurityClass",
    "ParentOrderSourceSystem",
    "BenchmarkNotionalUSDIMDecision",
    "SlippageUSDIMDecision",
]
GROUPBY_COLS = ["NotionalUSD", "SecurityClass"]
AGGS = {"NotionalUSD": "sum", "BenchmarkNotionalUSDIMDecision": "sum", "SlippageUSDIMDecision": "sum"}
EQ_CLASSES = [
    "Ordinary Share",
    "Exchange Traded Fund",
    "Depository Receipt",
    "Preference Share",
    "Convertible Preference Share",
]

nm = NativeMongoose("research")
LIB = NativeMongoose("mktdatad")["wdealtry.cta"]


def query_arctic(query, cols=COLUMNS):
    return LIB.read("cta_alloc_cached_dfindex", date_range=DATE_RANGE, columns=cols, query_builder=query).data


def test_stuff():
    q = QueryBuilder()
    q = q[q.SecurityClass.isin(EQ_CLASSES)]
    start = time.time()
    cpu_start = time.process_time()
    df = query_arctic(q)
    cpu_end = time.process_time()
    end = time.time()
    wall_time = end - start
    cpu_time = cpu_end - cpu_start
    print("Wall time: {}, CPU Time: {}".format(wall_time, cpu_time))


test_stuff()
