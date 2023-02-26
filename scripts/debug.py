from ahl.mongo import NativeMongoose
import pandas as pd


if __name__ == "__main__":
    nm = NativeMongoose("research")

    data = pd.DataFrame({"Hello": [1, 2, 3]}, index=pd.date_range(start="2022-01-01", end="2022-01-03"))

    lib = nm["mhertz.test_123"]
    lib.write("test_data", data)
    print(lib.read("test_data").data)
