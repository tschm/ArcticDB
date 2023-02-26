from arcticc.toolbox.storage import dissect_library, KeyType, Key
from arcticc.version_store.helper import get_arctic_native_lib as ganl
from ahl.mongo.mongoose import get_mongoose_lib

import pandas as pd
import numpy as np
from tqdm import tqdm
import logging

voltaetf = get_mongoose_lib("resvol.VOLTAETF@research")

voltaetf_syms = voltaetf.list_symbols()
from multiprocessing import Pool
from time import sleep
from tqdm._tqdm import tqdm
from collections import deque
from datetime import datetime

# from IPython.display import clear_output


def async_apply(func, symbols, proc_count):
    pool = Pool(proc_count)
    try:
        future_results_and_symbols = deque([(pool.apply_async(func, args=(symbol,)), symbol) for symbol in symbols])
        # progress=tqdm(total=len(future_results_and_symbols), leave=False, ascii=True)
        total_symbols = len(symbols)
        results_by_symbol = {}
        next_round_size = 1
        current_res_symbols = deque()
        start_dt = datetime.utcnow()
        errors = []
        while next_round_size:
            size = len(future_results_and_symbols)
            tmp = current_res_symbols
            current_res_symbols = future_results_and_symbols
            future_results_and_symbols = tmp
            while current_res_symbols:
                future_res, symbol = current_res_symbols.pop()
                if future_res.ready():
                    try:
                        results_by_symbol[symbol] = future_res.get()
                    except Exception as e:
                        print("error with symbol {}".format(symbol))
                        errors.append((symbol, "{}".format(e)))
                else:
                    future_results_and_symbols.appendleft((future_res, symbol))
            next_round_size = len(future_results_and_symbols)
            if next_round_size == size:
                sleep(1)
            else:
                print("{}/{}".format(len(results_by_symbol), total_symbols))
                # meter=tqdm.format_meter(len(results_by_symbol), total_symbols, (datetime.utcnow()-start_dt).total_seconds())
                # clear_output(wait=True)
        #                 progress.clear()
        #                 print(meter)
        # progress.update(size-next_round_size)
        #                 progress.refresh()
        return results_by_symbol, errors
    finally:
        pool.terminate()


def copy_symbol(symbol):
    src = ganl("resvol.voltaetf_3@~/.arctic/native/conf/envs.yaml")
    dst = ganl("resvol.voltaetf_copy@~/.arctic/native/conf/envs.yaml")
    t1 = pd.Timestamp.utcnow()
    vit = src.read(symbol)
    t2 = pd.Timestamp.utcnow()
    dst.write(symbol, vit.data, metadata=vit.metadata)
    t3 = pd.Timestamp.utcnow()
    return t1, t2, t3


timings, errors = async_apply(copy_symbol, voltaetf_syms, 24)

its = ((n, t1, t2, t3) for n, (t1, t2, t3) in timings.items())
df = pd.DataFrame(its, columns=["name", "t1", "t2", "t3"])
df.to_csv("./copy_voltaetf_with_reload.csv")
print(errors)
