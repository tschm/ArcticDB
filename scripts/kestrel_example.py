import pandas as pd

# from IPython.display import display
from numpy.random import RandomState
import os.path as osp


import numpy as np
import arcticc.pb2.storage_pb2 as storage
import arcticc.pb2.lmdb_storage_pb2 as lmdb_storage

envs = storage.MultiEnvConf()

conf = lmdb_storage.Config()
conf.path = "/tmp/lmdb01"
conf.recreate_if_exists = True

env = envs.env_by_id["research"]
storage = env.storage_by_id["local_01"]
storage.config.Pack(conf, type_url_prefix="cxx.arctic.org")

lib_desc = env.lib_by_path["/a/b"]
lib_desc.name = "Great lib for A / B"
lib_desc.storage_ids.append("local_01")

from arcticc.supported_types import field_desc as fd
from arcticcxx.types import (
    TimestampRange,
    create_timestamp_index_stream_descriptor,
    FieldDescriptor as FD,
    TypeDescriptor as TD,
)
from arcticcxx.types import DataType, Dimension

for k, v in DataType.__members__.iteritems():
    globals()[k] = v
for k, v in Dimension.__members__.iteritems():
    globals()[k] = v
from arcticcxx.stream import Spaces, SealWaitPolicy
from arcticcxx.storage import OpenMode
from arcticcxx.cpp_async import TaskScheduler
from arcticc.pb2.ticks_encoding_meta_pb2 import VariantCodecMeta as CodecOpt
from arcticc.pb2.ticks_meta_pb2 import TickStreamsGeneration

sched = TaskScheduler(thread_count=16)


class SpaceConf(object):
    def __init__(self, envs, env_id):
        self.envs = envs
        self.env_id = env_id


spaces = Spaces(sched, lib_space=SpaceConf(envs, "research"))

codec = CodecOpt()
codec.lz4.acceleration = 0

space = spaces.open("/a/b", OpenMode.WRITE, "my_user", codec)

tr = TimestampRange(pd.Timestamp("2016-01-12 09:12"), pd.Timestamp("2018-01-15 16:34"))

gen = TickStreamsGeneration()
gen.creation_us_utc = pd.Timestamp.utcnow().value

gen_writer = space.create_generation(gen, tr)
group_writer = gen_writer.create_group_writer(tr)
stream_desc = create_timestamp_index_stream_descriptor(999, [fd(UINT64, Dim1, "qty"), fd(FLOAT64, Dim1, "val")])
stream_writer = group_writer.create_writer(stream_desc, 1024)

indexes = np.arange(600, dtype=np.uint64)
np.random.shuffle(indexes)
vals = np.linspace(14.0, 16.0, 600)

from contextlib import contextmanager

res = {}


@contextmanager
def stopwatch(data):
    start = pd.Timestamp.utcnow().value
    yield
    stop = pd.Timestamp.utcnow().value
    data["start"] = start
    data["stop"] = stop
    data["duration"] = stop - start


def thrpt(data):
    data["thrpt"] = data["item_count"] * 1e9 / float(data["duration"])
    return data["thrpt"]


import os

# press_enter = raw_input("press enter once perf is attached. pid={}".format(os.getpid()))

start = pd.Timestamp.utcnow().value
row_count = 1000000
rb = stream_writer.row_builder
with stopwatch(res):
    for i in range(row_count):
        ts = tr.start_nanos_utc + i
        try:
            rb.start_row(ts)
            # rb.set_tuple((indexes, vals))
            rb.set_array_uint64(1, indexes)
            rb.set_array_double(2, vals)
            rb.end_row()
        except:
            rb.rollback_row()
            raise
    gen_writer.seal(SealWaitPolicy.COLLECT_WAIT_GROUP, 100000000)

end = pd.Timestamp.utcnow().value
thpt = row_count * 1e9 / float(end - start)
res["item_count"] = row_count
thrpt(res)
print(res)
print("write {:.3f} row/sec".format(thpt))
press_enter = raw_input("stop perf")


gen_reader = space.open_read(0)

sr_by_tsid = gen_reader.open_stream_readers([999], tr)

sr = sr_by_tsid[999]

start = pd.Timestamp.utcnow().value
row_count = 0
for r in sr:
    row_count += 1
end = pd.Timestamp.utcnow().value
thpt = row_count * 1e9 / float(end - start)
print("read {:.3f} row/sec".format(thpt))
