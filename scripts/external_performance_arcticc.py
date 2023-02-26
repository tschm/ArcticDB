import argparse
import numpy as np
import sys
import logging
import time
import random
import string
import prettytable
from compare_arctic_parquet import generate_data

logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)


class SIZES:
    SMALL = (5, 10_000, 1)
    SMALL_LE = (5, 10_000, 10)

    MEDIUM = (50, 100_000, 1)
    MEDIUM_LE = (50, 100_000, 10)

    LARGE = (50, 1_000_000, 1)
    LARGE_LE = (50, 1_000_000, 10)

    HUGE = (50, 10_000_000, 1)
    HUGE_LE = (50, 10_000_000, 10)

    HUGE_COLUMNS = (500, 1_000_000, 1)
    HUGE_COLUMNS_LE = (500, 1_000_000, 10)


def create_data(size):
    columns, rows, repeats = size
    type_ = np.dtype(float)

    return generate_data(columns * rows * np.dtype(type_).itemsize, columns, repeats=repeats)


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


class Benchmark:
    def _write(self, df, name):
        raise NotImplementedError

    def _read(self, name):
        raise NotImplementedError

    def _size(self, name):
        raise NotImplementedError

    def _delete(self, name):
        raise NotImplementedError

    def cleanup(self):
        raise NotImplementedError

    def run(self, repeats=1):
        table = prettytable.PrettyTable()
        table.field_names = ["Name", "Operation", "Rows", "Columns", "Size", "Duration"]
        for size in ["small", "medium", "large", "huge", "huge_columns"]:
            for suffix in ("", "_le"):
                write_times = []
                read_times = []
                delete_times = []
                sizes = []
                config = getattr(SIZES, size.upper() + suffix.upper())
                data = create_data(config)
                for _run in range(repeats):
                    write_times.append(self._write(data, size + suffix))
                    read_times.append(self._read(size + suffix))
                    sizes.append(self._size(size + suffix))
                    delete_times.append(self._delete(size + suffix))
                del data

                table.add_row(
                    [
                        size + suffix,
                        "write",
                        config[0],
                        config[1],
                        sizeof_fmt(max(sizes)),
                        sum(write_times) / len(write_times),
                    ]
                )

                table.add_row(
                    [
                        size + suffix,
                        "read",
                        config[0],
                        config[1],
                        sizeof_fmt(max(sizes)),
                        sum(read_times) / len(read_times),
                    ]
                )

                table.add_row(
                    [
                        size + suffix,
                        "delete",
                        config[0],
                        config[1],
                        sizeof_fmt(max(sizes)),
                        sum(delete_times) / len(delete_times),
                    ]
                )
        self.cleanup()

        print(table)


class ArcticcBenchmark(Benchmark):
    def __init__(self, endpoint, key, secret_key, bucket, region, use_virtual_addressing, secure):
        import boto3
        from botocore.config import Config
        from arcticdb import Arctic

        conn_string = f"s3{'s' if secure else ''}://{endpoint}:{bucket}?access={key}&secret={secret_key}"

        if region or use_virtual_addressing:
            if region:
                conn_string += "&region=" + str(region)
            if use_virtual_addressing:
                conn_string += "&use_virtual_addressing=true"

        self._library_name = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        self._ac = Arctic(conn_string)
        self._ac.create_library(self._library_name)
        time.sleep(2)
        self._ac_library = self._ac[self._library_name]
        self._boto_client = boto3.client(
            service_name="s3",
            endpoint_url=f"http{'s' if secure else ''}://{endpoint}",
            aws_access_key_id=key,
            aws_secret_access_key=secret_key,
            verify=False,
            config=None if not use_virtual_addressing else Config(s3={"addressing_style": "virtual"}),
        )
        self._bucket = bucket

    def _write(self, df, name):
        logger.info(f"Writing {name}; ({len(df.columns)}x{len(df)})...")
        s = time.time()
        self._ac_library.write(name, df)
        e = time.time()
        logger.info(f"...took {e - s} seconds")
        return e - s

    def _read(self, name):
        logger.info(f"Reading {name}...")
        s = time.time()
        df = self._ac_library.read(name).data
        e = time.time()
        logger.info(f"...took {e - s}s.\t\t{len(df.columns)}x{len(df)}, {sizeof_fmt(self._size(name))}")
        return e - s

    def _delete(self, name):
        s = time.time()
        self._ac_library.delete(name)
        e = time.time()
        return e - s

    def _size(self, name):
        docs = []
        for obj in self._boto_client.list_objects(Bucket=self._bucket)["Contents"]:
            if name in obj["Key"]:
                docs.append(obj)

        return sum(doc["Size"] for doc in docs)

    def cleanup(self):
        for symbol in self._ac_library.list_symbols():
            self._ac_library.delete(symbol)
        self._ac.delete_library(self._library_name)


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

    benchmark = ArcticcBenchmark(
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
