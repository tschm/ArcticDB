from ahl.mongo.mongoose import NativeMongoose
import time

nm = NativeMongoose("research")
lib = nm.get_library("wdealtry.s3_perftest")

total = 0
num_tests = 10

for x in range(num_tests):
    start = time.time()
    df = lib.read("perftest_{}".format(x))
    elapsed = time.time() - start
    total = total + elapsed
    print("Data frame of length {} in {}".format(len(df), elapsed))

print("Average time {}".format(total / num_tests))
