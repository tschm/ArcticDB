import functools
from ahl.mongo.mongoose.mongoose import NativeMongoose
from arcticc.config import set_log_level

m = NativeMongoose("research")
set_log_level("DEBUG")
lib_name = "skhare.dummyt"
import multiprocessing


def mp_worker(lib, worker_idx):
    print("getting lib in worker", worker_idx)
    print("syms=", lib.list_symbols())
    print("exiting worker", worker_idx)


def mp_handler():
    lib2 = m[lib_name]
    p = multiprocessing.Pool(20)
    lister = functools.partial(mp_worker, lib2)
    p.map(lister, range(20))


if __name__ == "__main__":
    mp_handler()
