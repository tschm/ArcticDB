# coding: utf-8

# Requires volatility.research installed. This pulls all other dependencies
from arcticc import log
from arcticc.config import load_loggers_config

log.configure(load_loggers_config(), force=True)

import volatility.sso.data.universe as universe

from datetime import datetime
from volatility.spark import pool, run_experiments, set_runner_defaults, Experiment, _make_metadata
from volatility.research.single_stocks.names import WEIGHTS, PWEIGHTS
from volatility.research.single_stocks.scripts.run_voltaetf_final import *
from volatility.research.single_stocks.scripts.run_voltaetf_final import (
    _make,
    _diag_filename,
    _set_runner_defaults,
    _set_experiment_defaults,
)


from volatility.tree_utils import run_tree, log_tree_results

metadata = _make_metadata(_make)


def _run(tree, name, diag_filename, write_lib, trading_mode, use_pandas, metadata=None, **kwargs):
    """
    Run tree

    Parameters
    ----------
    cf. Experiment

    Returns
    -------
    str
        Diagnostic filename
    """
    import ahl.diags
    import ahl.pandas
    import ahl.marketdata

    with ahl.marketdata.features.set_trading_mode(trading_mode):

        if use_pandas:
            ahl.pandas.io.use_pandas()
        kwargs["workers"] = 24
        kwargs["save_graph_yaml"] = False
        tree_results, store = run_tree(tree, name, write_lib, **kwargs)
    #         with ahl.diags.to_diagsfile(diag_filename):
    #             # log tree
    #             log_tree_results(tree_results, store)
    #             # log metadata
    #             with ahl.diags.prefix('__metadata'):
    #                 ahl.diags.log('user', getpass.getuser())
    #                 ahl.diags.log('timestamp', datetime.now())
    #                 if metadata is not None:
    #                     for key, val in metadata.iteritems():
    #                         ahl.diags.log(key, val)

    return diag_filename


def run_experiment(experiment):
    """
    Make and run experiment

    Parameters
    ----------
    name: str
        Experiment name
    write_lib: str
        Library connection string
    experiment_config: dict
        Experiment config
    runner_config: dict
        Runner config

    Returns
    -------
    str
        Diag filename
    """
    # make and run
    metadata.update(experiment.to_dict())
    tree = _make(experiment.name, **experiment.experiment_config)
    return _run(
        tree,
        experiment.name,
        experiment.diag_filename,
        experiment.write_lib,
        metadata=metadata,
        **experiment.runner_config,
    )


def run_one(name, write_lib, experiment_config=None, runner_config=None, debug=False, spark_conf_dict=None):
    if runner_config is None:
        runner_config = {}

    if experiment_config is None:
        experiment_config = {}

    if spark_conf_dict is None:
        spark_conf_dict = {}

    # defaults
    diag_filename = _diag_filename(name)
    _set_runner_defaults(runner_config)
    _set_experiment_defaults(experiment_config)
    # spark_conf_dict.setdefault("spark.executor.memory", "20g")  # for toysim

    return run_experiment(
        Experiment(
            name=name,
            write_lib=write_lib,
            diag_filename=diag_filename,
            runner_config=runner_config,
            experiment_config=experiment_config,
        )
    )


from arcticc.version_store.helper import load_envs_config, arctic_native_path, ArcticcMemConf
from arcticc.config import load_loggers_config
import arcticc.log as loggers

conf_path = arctic_native_path("conf/envs.yaml")

loggers.configure(load_loggers_config(), force=True)

# Save ephemeral config
cfg = load_envs_config()
lib = ArcticcMemConf(cfg)["vol.test1"]
voltaetf = ArcticcMemConf(cfg)["resvol.voltaetf_3"]


from mock import patch

runner_config = dict(
    read_libs=(
        "resvol.VOLTAETF@research",  # pnl simulation graph
        "resvol.vetf_graph@research=RESEARCH-20181224",  # data graph
    )
)

from ahl.mongo.mongoose import get_mongoose_lib


def get_lib(name):
    if name == "some.lib":
        return lib
    # elif name ==  'resvol.VOLTAETF@research':
    #     return voltaetf
    else:
        return get_mongoose_lib(name)


with patch("volatility.network._get_lib", get_lib):
    diag_filename = run_one("xxx", "some.lib", runner_config=runner_config)
