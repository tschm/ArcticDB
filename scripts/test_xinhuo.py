from arcticc.config import load_loggers_config
from ahl.mongo.mongoose import NativeMongoose
import time


from arcticc import log

log_config = load_loggers_config()
# log.configure(log_config)

nm = NativeMongoose("research")
lib = nm["ice.GBMI_DAILY_BY_LABEL"]
start = time.time()

lib.read("Description").data
elapse = time.time() - start
print("Elapsed: {}".format(elapse))
