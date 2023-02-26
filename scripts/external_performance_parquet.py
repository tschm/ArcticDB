import argparse
import os
import s3fs
import numpy as np
import sys
import logging
import time
import pyarrow
import pyarrow.parquet as pq
import prettytable
from external_performance_arcticc import Benchmark, sizeof_fmt
from compare_arctic_parquet import generate_data

logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)


class ParquetBenchmark(Benchmark):
    def __init__(self, endpoint, key, secret_key, bucket, region, use_virtual_addressing, secure):
        self._s3fs = s3fs.S3FileSystem(
            anon=False,
            key=key,
            secret=secret_key,
            client_kwargs={"verify": False, "endpoint_url": endpoint},
            config_kwargs=None if use_virtual_addressing is False else {"s3": {"addressing_style": "virtual"}},
        )
        self._bucket = bucket

    def _write(self, df, name):
        logger.info(f"Writing {name}; ({len(df.columns)}x{len(df)})...")
        df_to_write = pyarrow.Table.from_pandas(df)
        s = time.time()
        pq.write_to_dataset(df_to_write, f"s3://{self._bucket}/pq_test/{name}", filesystem=self._s3fs)
        e = time.time()
        logger.info(f"...took {e - s} seconds")
        return e - s

    def _read(self, name):
        logger.info(f"Reading {name}...")
        s = time.time()
        df = pq.ParquetDataset(f"s3://{self._bucket}/pq_test/{name}", filesystem=self._s3fs).read_pandas()
        e = time.time()
        logger.info(f"...took {e - s}s.\t\t{df.num_columns}x{df.num_rows}, {sizeof_fmt(self._size(name))}")
        return e - s

    def _delete(self, name):
        s = time.time()
        self._s3fs.rm(f"{self._bucket}/pq_test/{name}", recursive=True)
        e = time.time()
        return e - s

    def _size(self, name):
        size = 0
        for dirpath, dirname, filenames in self._s3fs.walk(f"{self._bucket}/pq_test/{name}"):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                size += self._s3fs.size(full_path)

        logger.info(f"{name} is of size {size}")
        return size

    def cleanup(self):
        try:
            self._s3fs.rm(f"{self._bucket}/pq_test/", recursive=True)
        except Exception as _e:
            pass


def main():
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--secret-key", required=True)
    parser.add_argument("--bucket", required=True)

    parser.add_argument("--region", required=False)
    parser.add_argument("--secure", action="store_true")
    parser.add_argument("--use-virtual-addressing", action="store_true")

    parser.add_argument("--repeats", default=1, type=int)
    opts = parser.parse_args()

    if not opts.endpoint.startswith("http"):
        raise ValueError("Endpoint must start with http(s)")

    benchmark = ParquetBenchmark(
        endpoint=opts.endpoint,
        key=opts.key,
        secret_key=opts.secret_key,
        bucket=opts.bucket,
        region=opts.region,
        secure=opts.secure,
        use_virtual_addressing=opts.use_virtual_addressing,
    )
    logger.setLevel(logging.INFO)
    benchmark.run(repeats=opts.repeats)


if __name__ == "__main__":
    sys.exit(main())
