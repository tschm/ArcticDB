# coding: utf-8

# In[1]:


import pandas as pd

import arcticc.pb2.storage_pb2 as storage
import arcticc.pb2.lmdb_storage as lmdb_storage

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
from arcticc.pb2.encoding import VariantCodec as CodecOpt
from arcticc.pb2.ticks_meta_pb2 import TickStreamsGeneration


# In[2]:


envs = storage.MultiEnvConf()

conf = lmdb_storage.Config()
conf.path = "/users/is/agonnay/nobackup/arcticcxx/lmdb01"
conf.recreate_if_exists = True

env = envs.env_by_id["research"]
storage = env.storage_by_id["local_01"]
storage.config.Pack(conf, type_url_prefix="cxx.arctic.org")

lib_desc = env.lib_by_path["/a/b"]
lib_desc.name = "Great lib for A / B"
lib_desc.storage_ids.append("local_01")


# In[3]:


sched = TaskScheduler(thread_count=16)


class SpaceConf(object):
    def __init__(self, envs, env_id):
        self.envs = envs
        self.env_id = env_id


spaces = Spaces(sched, lib_space=SpaceConf(envs, "research"))
codec = CodecOpt()
# codec.lz4.acceleration= 0

space = spaces.open("/a/b", OpenMode.WRITE, "my_user", codec)

# In[4]:

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


# In[5]:


# res = {}
# with stopwatch(res):
#     row_count = 1000000
#     for i in range(row_count):
#         ts = tr.start_nanos_utc + i
#         with stream_writer.start_row(ts) as rb:
#             rb.set_scalar_uint64(1, i*777)
#     res['item_count']=row_count
# gen_writer.seal(SealWaitPolicy.COLLECT_WAIT_GROUP, 100000000)
# print("write {:.3f} row/sec".format(thrpt(res)))


# In[6]:


from kestrel.engine.persistence_v2.shortcuts import get_gen_finder_v1 as get_gen_finder

gen_finder = get_gen_finder("equities.kestrelv2_statarbpeb@mktdatas")
gen = gen_finder.by_id(6469141568340233341).slice()


# In[7]:


kes_read = {}
data = []
with stopwatch(kes_read):
    c = 0
    for tsv in gen.tree.core.sample.px.mids:
        c += 1
        data.append(tsv)
    kes_read["item_count"] = len(data)

print(thrpt(kes_read))


# In[8]:


kes_read


# In[13]:


# tr = TimestampRange(data[0].timestamp, data[-1].timestamp)
tr = TimestampRange(1391418180000000000, 1539011400000000000)
gen = TickStreamsGeneration()
gen.creation_us_utc = pd.Timestamp.utcnow().value
gen_writer = space.create_generation(gen, tr)
group_writer = gen_writer.create_group_writer(tr)
stream_desc = create_timestamp_index_stream_descriptor(999, [fd(FLOAT64, Dim1, "val"), fd(ASCII_FIXED64, Dim1, "idx")])
stream_writer = group_writer.create_writer(stream_desc, 256)


# In[14]:


import numpy as np


# In[15]:
import os

press_enter = raw_input("press enter once perf is attached. pid={}".format(os.getpid()))

res = {}
with stopwatch(res):
    rb = stream_writer.row_builder
    try:
        for tsv in data:
            rb.start_row(tsv.timestamp.value)
            rb.set_array_double(1, tsv.value.values)
            rb.set_string_array(2, tsv.value.index.values.astype("S"))
            rb.end_row()
    except:
        rb.rollback_row()
        raise
    res["item_count"] = len(data)
gen_writer.seal(SealWaitPolicy.COLLECT_WAIT_GROUP, 100000000)
print("write {:.3f} row/sec".format(thrpt(res)))


# In[16]:
import os

press_enter = raw_input("stop perf")

gen_reader = space.open_read(0)
sr_by_tsid = gen_reader.open_stream_readers([999], tr)
sr = sr_by_tsid[999]

press_enter = raw_input("press enter once perf is attached. pid={}".format(os.getpid()))
read_res = {}
with stopwatch(read_res):
    row_count = 0
    for r in sr:
        row_count += 1

read_res["item_count"] = row_count
print("read {:.3f} row/sec".format(thrpt(read_res)))


# In[77]:
