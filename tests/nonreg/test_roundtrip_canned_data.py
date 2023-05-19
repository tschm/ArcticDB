import pytest
import pandas as pd
from pandas.util.testing import assert_frame_equal, assert_series_equal
from functools import lru_cache

from arcticc.util.test import param_dict
from six import PY3

from ahl.mongo import Mongoose
import man.arctic.library_util


# In the following lines, the naming convention is
# test_rt_df stands for roundtrip dataframe (implicitly pandas given file name)
@pytest.fixture(scope="module")
def get_mongoose_lib():
    """Now a factory-like fixture to avoid bombarding Vault"""
    cached_mongo = lru_cache(maxsize=10)(Mongoose)
    return lambda l="arcticc.nonreg", h="research": cached_mongo(h)[l]


# In the following lines, the naming convention is
# test_rt_df stands for roundtrip dataframe (implicitly pandas given file name)
def get_native_lib(l="arcticc.nonreg", h="research"):
    return man.arctic.library_util.get_native_lib(h, l)


def convert_column(col):
    try:
        converted = col.str.decode("utf-8")
        return converted
    except AttributeError:
        return col


def convert_bytes_to_strings(df):
    idx = df.applymap(lambda x: isinstance(x, bytes)).all(0)
    str_df = df[df.columns[idx]]
    str_df = str_df.apply(lambda x: x.str.decode("utf-8"))
    for col in str_df:
        df[col] = str_df[col]

    return df


def compare_as_strings(left, right):
    left_conv = convert_bytes_to_strings(left)
    right_conv = convert_bytes_to_strings(right)

    assert_frame_equal(left_conv, right_conv)


# TODO fix commented tests once index refactoring pr has landed
@param_dict(
    "symbol",
    {
        "voltaetf_df": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/1027215/pnl_result",
        "voltaetf_weighted": "resvol.VOLTAETF__FSF_more_metadata/v1/simulation/toysim/signal/weighted",
        "voltaetf_y_hat_test": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/split/split_1/y_hat_test",
        ###    'voltaetf_trade_agg_data':'resvol.VOLTAETF__FSF_1m_25d_strangle/v1/trade_agg_data',
        "voltaetf_predictions": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/predictions",
        "voltaetf_pnl_result": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/1027215/pnl_result",
        "voltaetf_raw": "resvol.VOLTAETF__FSF_more_metadata/v1/simulation/toysim/acc_curve/raw",
        "voltaetf_cost": "resvol.VOLTAETF__FSF_more_metadata/v1/simulation/toysim/acc_curve/cost",
        "voltaetf_y_train": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/split/split_0/y_train",
        "voltaetf_greek_scaled_signal": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/greek_scaled_signal",
        "voltaetf_out": "resvol.VOLTAETF__FSF_more_metadata/v1/predictors/iosc_1/out",
        "voltaetf_total": "resvol.VOLTAETF__FSF_more_metadata/v1/simulation/toysim/pnl/total",
        "voltaetf_X_train": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/split/split_0/X_train",
        "voltaetf_mappings": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/mappings",
        "voltaetf_ast_group": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/AST153851/ast_group",
        "voltaetf_pweights": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/pweights",
        "voltaetf_pnl_frame": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/AST153851/pnl_frame",
        "voltaetf_pweighted_signal": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/pweighted_signal",
        ###    'voltaetf_trade_date_data':'resvol.VOLTAETF__FSF_1m_25d_strangle/v1/trade_date_data',
        "voltaetf_wgt": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/vol_scaler/wgt",
        "voltaetf_X_predict": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/X_predict",
        "voltaetf_simulated_pnl": "resvol.VOLTAETF__FSF_more_metadata/v1/target_pnl/simulated_pnl",
        "voltaetf_trades_df": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/1027215/trades_df",
        "voltaetf_trading_filter": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/trading_filter",
        "voltaetf_X_test": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/split/split_0/X_test",
        "voltaetf_sec_2_ast": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/sec_2_ast",
        "voltaetf_adjusted_pnl": "resvol.VOLTAETF__FSF_more_metadata/v1/target_pnl/adjusted_pnl",
        "voltaetf_X": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/Xy/X",
        "voltaetf_y_test": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/split/split_0/y_test",
        "voltaetf_pnl_filter": "resvol.VOLTAETF__FSF_more_metadata/v1/trading_filter/pnl_filter",
        "voltaetf_signal": "resvol.VOLTAETF__FSF_voltaetf_dynamic_volume_pweights_final/v1/simulation/signal",
        "voltaetf_y_hat_train": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/split/split_1/y_hat_train",
        "voltaetf_greek": "resvol.VOLTAETF__FSF_more_metadata/v1/target_pnl/greek",
        "voltaetf_y": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/Xy/y",
        "risk_pca": "glg.nclarke__pca_run_list",
        "option_risk": "rsee.sso_option_risk__AST166604",
        "vol_vega": "volatility.vega_AST166604",
        "sec_rtns": "glg.nclarke__sec_rtns_2014",
    },
)
def test_rt_df(lmdb_version_store, symbol, get_mongoose_lib):
    print("Doing {}".format(symbol))
    lib = get_mongoose_lib()
    vit = lib.read(symbol)
    meta = vit.metadata["wrapped_meta"]
    wit = lmdb_version_store.write(symbol, vit.data, metadata=None if not meta else meta)
    assert wit is not None
    d = lmdb_version_store.read(symbol)

    if len(vit.data.index) == 0 and len(d.data.index) == 0:
        # can't really rely on types with empty index
        assert d.data.index.name == vit.data.index.name
        d.data.index = vit.data.index

    assert_frame_equal(vit.data, d.data)
    if not vit.data.empty:
        native_lib = get_native_lib()
        stored = native_lib.read(symbol)
        assert_frame_equal(vit.data, stored.data)

        s3_native_lib = get_native_lib("arcticc.nonreg_s3")
        stored = s3_native_lib.read(symbol)
        assert_frame_equal(vit.data, stored.data)


@param_dict(
    "symbol",
    cases={
        "voltaetf_more_metadata_status": "resvol.VOLTAETF__more_metadata_status",
        "voltaetf_top_market_cap": "resvol.VOLTAETF__FSF_more_metadata/v1/trading_filter/params/top_market_cap",
        "voltaetf_voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_v2_status_graph_yaml": "resvol.VOLTAETF__voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_v2_status_graph_yaml",
        "voltaetf_pnl_result": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/11632/pnl_result",
        "voltaetf_lot_size": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/lot_size",
        "voltaetf_voltaetf_voltaetf_static_volume_pweights_final_status_nx_graph_yaml": "resvol.VOLTAETF__voltaetf_voltaetf_static_volume_pweights_final_status_nx_graph_yaml",
        "voltaetf_voltaetf_dynamic_volume_pweights_final_status_nx_graph_yaml": "resvol.VOLTAETF__voltaetf_dynamic_volume_pweights_final_status_nx_graph_yaml",
        "voltaetf_voltaetf_extension_status": "resvol.VOLTAETF__voltaetf_extension_status",
        "voltaetf_init_vol_scaler": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/vol_scaler/init_vol_scaler",
        "voltaetf_use_full_trading_filter": "resvol.VOLTAETF__FSF_more_metadata/v1/predictors/params/use_full_trading_filter",
        "voltaetf_greek_scaling": "resvol.VOLTAETF__FSF_more_metadata/v1/target_pnl/params/greek_scaling",
        "voltaetf_lower": "resvol.VOLTAETF__FSF_more_metadata/v1/predictors/iosc_1/params/lower",
        "voltaetf_pnl_frame_args_0": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/AST153851/pnl_frame_args_0",
        "voltaetf_1m_25d_strangle_status": "resvol.VOLTAETF__1m_25d_strangle_status",
        "voltaetf_voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_v2_status_nx_graph_yaml": "resvol.VOLTAETF__voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_v2_status_nx_graph_yaml",
        "voltaetf_vendor": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/vendor",
        "voltaetf_min_value": "resvol.VOLTAETF__FSF_more_metadata/v1/predictors/iosc_1/params/min_value",
        "voltaetf_generic_30d_atm_strangle_bs_20181115_status_nx_graph_yaml": "resvol.VOLTAETF__generic_30d_atm_strangle_bs_20181115_status_nx_graph_yaml",
        "voltaetf_via_type": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/via_type",
        "voltaetf_apply_pweights": "resvol.VOLTAETF__FSF_voltaetf_dynamic_volume_pweights_final/v1/simulation/params/apply_pweights",
        "voltaetf_voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_v2_status": "resvol.VOLTAETF__voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_v2_status",
        "voltaetf_from_dt": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/from_dt",
        "voltaetf_X": "resvol.VOLTAETF__FSF_test/v1/X",
        "voltaetf_voltaetf_dynamic_volume_pweights_final_status_graph_yaml": "resvol.VOLTAETF__voltaetf_dynamic_volume_pweights_final_status_graph_yaml",
        "voltaetf_1m_25d_strangle_bs_20181115_status_nx_graph_yaml": "resvol.VOLTAETF__1m_25d_strangle_bs_20181115_status_nx_graph_yaml",
        "voltaetf_partitions": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/AST153851/partitions",
        "voltaetf_voltaetf_bs_extension_status_graph_yaml": "resvol.VOLTAETF__voltaetf_bs_extension_status_graph_yaml",
        "voltaetf_name": "resvol.VOLTAETF__FSF_more_metadata/v1/name",
        "voltaetf_voltaetf_gics10_status_nx_graph_yaml": "resvol.VOLTAETF__voltaetf_gics10_status_nx_graph_yaml",
        "voltaetf_y_hat_train": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/split/split_0/y_hat_train",
        "voltaetf_rolling_window": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/rolling_window",
        "voltaetf_to_dt": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/to_dt",
        "voltaetf_test_status_nx_graph_yaml": "resvol.VOLTAETF__test_status_nx_graph_yaml",
        "voltaetf_pnl_graph_version": "resvol.VOLTAETF__FSF_more_metadata/v1/simulation/params/pnl_graph_version",
        "voltaetf_voltaetf_voltaetf_dynamic_volume_pweights_final_status_graph_yaml": "resvol.VOLTAETF__voltaetf_voltaetf_dynamic_volume_pweights_final_status_graph_yaml",
        "voltaetf_voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_status": "resvol.VOLTAETF__voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_status",
        "voltaetf_voltaetf_etf_gics1_sector_static_volume_pweights_vol_target_0d1_status_graph_yaml": "resvol.VOLTAETF__voltaetf_etf_gics1_sector_static_volume_pweights_vol_target_0d1_status_graph_yaml",
        "voltaetf_more_metadata_status_graph_yaml": "resvol.VOLTAETF__more_metadata_status_graph_yaml",
        "voltaetf_old_dataset_status_graph_yaml": "resvol.VOLTAETF__old_dataset_status_graph_yaml",
        "voltaetf_last_predict_datetime": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/params/last_predict_datetime",
        "voltaetf_generic_30d_smile_status": "resvol.VOLTAETF__generic_30d_smile_status",
        "voltaetf_voltaetf_dynamic_volume_pweights_final_status": "resvol.VOLTAETF__voltaetf_dynamic_volume_pweights_final_status",
        "voltaetf_y_hat_test": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/split/split_0/y_hat_test",
        "voltaetf_voltaetf_bs_extension_status_nx_graph_yaml": "resvol.VOLTAETF__voltaetf_bs_extension_status_nx_graph_yaml",
        "voltaetf_sec_id": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/1027215/sec_id",
        "voltaetf_market_stress_limit_beta": "resvol.VOLTAETF__FSF_more_metadata/v1/simulation/params/market_stress_limit_beta",
        "voltaetf_pweight_by": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/pweight_by",
        "voltaetf_max_group_stress_limit": "resvol.VOLTAETF__FSF_more_metadata/v1/simulation/params/max_group_stress_limit",
        "voltaetf_index_constituents": "resvol.VOLTAETF__FSF_more_metadata/v1/trading_filter/params/index_constituents",
        "voltaetf_pnl_frame": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/AST5582/pnl_frame",
        "voltaetf_resample_periods": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/resample_periods",
        "voltaetf_ast_list": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/ast_list",
        "voltaetf_more_metadata_status_nx_graph_yaml": "resvol.VOLTAETF__more_metadata_status_nx_graph_yaml",
        "voltaetf_pnl_library": "resvol.VOLTAETF__FSF_more_metadata/v1/simulation/params/pnl_library",
        "voltaetf_backfill": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/backfill",
        "voltaetf_test_volta_status_graph_yaml": "resvol.VOLTAETF__test_volta_status_graph_yaml",
        "voltaetf_voltaetf_static_volume_pweights_final_status": "resvol.VOLTAETF__voltaetf_static_volume_pweights_final_status",
        "voltaetf_voltaetf_static_volume_pweights_final_status_graph_yaml": "resvol.VOLTAETF__voltaetf_static_volume_pweights_final_status_graph_yaml",
        "voltaetf_pnl_graph_name": "resvol.VOLTAETF__FSF_more_metadata/v1/simulation/params/pnl_graph_name",
        "voltaetf_ast_id": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/AST153851/ast_id",
        "voltaetf_slow": "resvol.VOLTAETF__FSF_more_metadata/v1/predictors/iosc_1/params/slow",
        "voltaetf_generic_30d_atm_strangle_bs_status": "resvol.VOLTAETF__generic_30d_atm_strangle_bs_status",
        "voltaetf_toysim": "resvol.VOLTAETF__FSF_more_metadata/v1/simulation/toysim",
        "voltaetf_generic_30d_atm_strangle_bs_20181115_status_graph_yaml": "resvol.VOLTAETF__generic_30d_atm_strangle_bs_20181115_status_graph_yaml",
        "voltaetf_amount": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/amount",
        "voltaetf_lead_lag": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/lead_lag",
        "voltaetf_exclude_ast": "resvol.VOLTAETF__FSF_more_metadata/v1/trading_filter/params/exclude_ast",
        "voltaetf_first_predict_datetime": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/params/first_predict_datetime",
        "voltaetf_take_abs": "resvol.VOLTAETF__FSF_more_metadata/v1/predictors/iosc_1/params/take_abs",
        "voltaetf_test_volta_status": "resvol.VOLTAETF__test_volta_status",
        "voltaetf_graph_version": "resvol.VOLTAETF__FSF_more_metadata/v1/data/graph_version",
        "voltaetf_ast_ids": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/ast_ids",
        "voltaetf_static_pweights": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/static_pweights",
        "voltaetf_tradable_dates": "resvol.VOLTAETF__FSF_1m_25d_strangle_20181115/v1/1027215/tradable_dates",
        "voltaetf_sec_ids": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/sec_ids",
        "voltaetf_voltaetf_voltaetf_static_volume_pweights_final_status_graph_yaml": "resvol.VOLTAETF__voltaetf_voltaetf_static_volume_pweights_final_status_graph_yaml",
        "voltaetf_to_date": "resvol.VOLTAETF__FSF_1m_25d_strangle_20181115/v1/to_date",
        "voltaetf_wgt_args_0": "resvol.VOLTAETF__FSF_voltaetf_dynamic_volume_pweights_final/v1/simulation/params/vol_scaler/wgt_args_0",
        "voltaetf_wgt_args_1": "resvol.VOLTAETF__FSF_voltaetf_dynamic_volume_pweights_final/v1/simulation/params/vol_scaler/wgt_args_1",
        "voltaetf_vol_adjust": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/vol_adjust",
        "voltaetf_voltaetf_bs_extension_status": "resvol.VOLTAETF__voltaetf_bs_extension_status",
        "voltaetf_unit": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/unit",
        "voltaetf_fast": "resvol.VOLTAETF__FSF_more_metadata/v1/predictors/iosc_1/params/fast",
        "voltaetf_fit_intercept": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/params/fit_intercept",
        "voltaetf_trades_df": "resvol.VOLTAETF__FSF_generic_1m_25d_strangle/v1/11632/trades_df",
        "voltaetf_predictions": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/split/split_0/predictions",
        "voltaetf_winsorize_quantile": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/params/winsorize_quantile",
        "voltaetf_30d_atm_strangle_status": "resvol.VOLTAETF__30d_atm_strangle_status",
        "voltaetf_from_date": "resvol.VOLTAETF__FSF_1m_25d_strangle_20181115/v1/from_date",
        "voltaetf_vehicle": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/vehicle",
        "voltaetf_start_date": "resvol.VOLTAETF__FSF_more_metadata/v1/simulation/params/start_date",
        "voltaetf_voltaetf_voltaetf_dynamic_volume_pweights_final_status_nx_graph_yaml": "resvol.VOLTAETF__voltaetf_voltaetf_dynamic_volume_pweights_final_status_nx_graph_yaml",
        "voltaetf_voltaetf_static_volume_pweights_final_status_nx_graph_yaml": "resvol.VOLTAETF__voltaetf_static_volume_pweights_final_status_nx_graph_yaml",
        "voltaetf_end_date": "resvol.VOLTAETF__FSF_more_metadata/v1/simulation/params/end_date",
        "voltaetf_voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_status_graph_yaml": "resvol.VOLTAETF__voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_status_graph_yaml",
        "voltaetf_switching_cycle_params": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/switching_cycle_params",
        "voltaetf_pricer": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/pricer",
        "voltaetf_graph_name": "resvol.VOLTAETF__FSF_more_metadata/v1/data/graph_name",
        "voltaetf_keep_ast": "resvol.VOLTAETF__FSF_more_metadata/v1/trading_filter/params/keep_ast",
        "voltaetf_trades_df_args_0": "resvol.VOLTAETF__FSF_1m_25d_strangle_20181115/v1/1027215/trades_df_args_0",
        "voltaetf_voltaetf_extension_status_graph_yaml": "resvol.VOLTAETF__voltaetf_extension_status_graph_yaml",
        "voltaetf_old_dataset_status": "resvol.VOLTAETF__old_dataset_status",
        "voltaetf_Xy": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/Xy",
        "voltaetf_simple_norm": "resvol.VOLTAETF__FSF_more_metadata/v1/predictors/iosc_1/params/simple_norm",
        "voltaetf_generic_1m_25d_strangle_status": "resvol.VOLTAETF__generic_1m_25d_strangle_status",
        "voltaetf_fum": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/1027215/fum",
        "voltaetf_1m_25d_strangle_bs_20181115_status_graph_yaml": "resvol.VOLTAETF__1m_25d_strangle_bs_20181115_status_graph_yaml",
        "voltaetf_vol_target": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/vol_target",
        "voltaetf_log_scale": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/log_scale",
        "voltaetf_safety_gap": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/params/safety_gap",
        "voltaetf_split_amount": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/split_amount",
        "voltaetf_adjusted_pnl_args_0": "resvol.VOLTAETF__FSF_more_metadata/v1/target_pnl/adjusted_pnl_args_0",
        "voltaetf_trading_delay": "resvol.VOLTAETF__FSF_voltaetf_dynamic_volume_pweights_final/v1/simulation/params/trading_delay",
        "voltaetf_voltaetf_gics10_status": "resvol.VOLTAETF__voltaetf_gics10_status",
        "voltaetf_voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_status_nx_graph_yaml": "resvol.VOLTAETF__voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_status_nx_graph_yaml",
        "voltaetf_assert_fum": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/AST153851/assert_fum",
        "voltaetf_hedge_policy": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/hedge_policy",
        "voltaetf_test_status_graph_yaml": "resvol.VOLTAETF__test_status_graph_yaml",
        "voltaetf_voltaetf_extension_status_nx_graph_yaml": "resvol.VOLTAETF__voltaetf_extension_status_nx_graph_yaml",
        "voltaetf_signal_cap": "resvol.VOLTAETF__FSF_voltaetf_dynamic_volume_pweights_final/v1/simulation/params/signal_cap",
        "voltaetf_is_classifier": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/params/is_classifier",
        "voltaetf_voltaetf_etf_gics1_sector_static_volume_pweights_vol_target_0d1_status_nx_graph_yaml": "resvol.VOLTAETF__voltaetf_etf_gics1_sector_static_volume_pweights_vol_target_0d1_status_nx_graph_yaml",
        "voltaetf_oscnorm_limit": "resvol.VOLTAETF__FSF_more_metadata/v1/predictors/iosc_1/params/oscnorm_limit",
        "voltaetf_test_volta_status_nx_graph_yaml": "resvol.VOLTAETF__test_volta_status_nx_graph_yaml",
        "voltaetf_max_market_stress_limit": "resvol.VOLTAETF__FSF_more_metadata/v1/simulation/params/max_market_stress_limit",
        "voltaetf_out": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/vol_scaler/out",
        "voltaetf_standardize": "resvol.VOLTAETF__FSF_voltaetf_dynamic_volume_pweights_final/v1/simulation/params/standardize",
        "voltaetf_old_dataset_status_nx_graph_yaml": "resvol.VOLTAETF__old_dataset_status_nx_graph_yaml",
        "voltaetf_max_value": "resvol.VOLTAETF__FSF_more_metadata/v1/predictors/iosc_1/params/max_value",
        "voltaetf_pnl_field": "resvol.VOLTAETF__FSF_more_metadata/v1/target_pnl/params/pnl_field",
        "voltaetf_voltaetf_etf_gics1_sector_static_volume_pweights_vol_target_0d1_status": "resvol.VOLTAETF__voltaetf_etf_gics1_sector_static_volume_pweights_vol_target_0d1_status",
        "voltaetf_skip_trade_error": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/skip_trade_error",
        "voltaetf_voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_vmaster_status_graph_yaml": "resvol.VOLTAETF__voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_vmaster_status_graph_yaml",
        "voltaetf_trading_offset": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/trading_offset",
        "voltaetf_test_status": "resvol.VOLTAETF__test_status",
        "voltaetf_voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_vmaster_status": "resvol.VOLTAETF__voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_vmaster_status",
        "voltaetf_voltaetf_gics10_status_graph_yaml": "resvol.VOLTAETF__voltaetf_gics10_status_graph_yaml",
        "voltaetf_generic_30d_atm_strangle_status": "resvol.VOLTAETF__generic_30d_atm_strangle_status",
        "voltaetf_sec_ast_ids": "resvol.VOLTAETF__FSF_1m_25d_strangle_20181115/v1/sec_ast_ids",
        "voltaetf_30d_smile_status": "resvol.VOLTAETF__30d_smile_status",
        "voltaetf_mask": "resvol.VOLTAETF__FSF_more_metadata/v1/simulation/params/mask",
        "voltaetf_voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_vmaster_status_nx_graph_yaml": "resvol.VOLTAETF__voltaetf_etf_gics1_sector_dynamic_volume_pweights_final_vmaster_status_nx_graph_yaml",
        "voltaetf_greek": "resvol.VOLTAETF__FSF_more_metadata/v1/weights/params/greek",
        "voltaetf_y": "resvol.VOLTAETF__FSF_test/v1/y",
        "voltaetf_Xy_preprocessed_args_0": "resvol.VOLTAETF__FSF_test/v1/FSF_test/v1/signals/ols/fit/Xy_preprocessed_args_0",
        "voltaetf_refit_frequency": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/params/refit_frequency",
    },
    py2only={
        "voltaetf_json": "resvol.VOLTAETF__1m_25d_strangle_bs_20181115_status",
        "voltaetf_1m_25d_strangle_20181115_status": "resvol.VOLTAETF__1m_25d_strangle_20181115_status",
        "voltaetf_1m_25d_strangle_bs_20181115_status": "resvol.VOLTAETF__1m_25d_strangle_bs_20181115_status",
        "voltaetf_generic_30d_atm_strangle_bs_20181115_status": "resvol.VOLTAETF__generic_30d_atm_strangle_bs_20181115_status",
        "voltaetf_voltaetf_voltaetf_static_volume_pweights_final_status": "resvol.VOLTAETF__voltaetf_voltaetf_static_volume_pweights_final_status",
        "voltaetf_voltaetf_voltaetf_dynamic_volume_pweights_final_status": "resvol.VOLTAETF__voltaetf_voltaetf_dynamic_volume_pweights_final_status",
        "voltaetf_train": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/split/split_0/train",
        "voltaetf_toysim_insample_args_0": "resvol.VOLTAETF__FSF_voltaetf_dynamic_volume_pweights_final/v1/simulation/params/vol_scaler/toysim_insample_args_0",
        "voltaetf_test": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/fit/split/split_0/test",
        "voltaetf_insample_dateranges": "resvol.VOLTAETF__FSF_voltaetf_dynamic_volume_pweights_final/v1/simulation/params/vol_scaler/insample_dateranges",
        "voltaetf_out_args_0": "resvol.VOLTAETF__FSF_voltaetf_voltaetf_dynamic_volume_pweights_final/v1/simulation/params/vol_adjust/out_args_0",
        "voltaetf_calendar": "resvol.VOLTAETF__FSF_1m_25d_strangle/v1/calendar",
    },
)
def test_rt_non_df(lmdb_version_store, symbol, get_mongoose_lib):
    print("Doing {}".format(symbol))
    lib = get_mongoose_lib()
    vit = lib.read(symbol)
    meta = vit.metadata["wrapped_meta"]
    wit = lmdb_version_store.write(symbol, vit.data, metadata=None if not meta else meta)
    assert wit is not None
    d = lmdb_version_store.read(symbol)
    assert d.data == vit.data

    if not PY3:
        native_lib = get_native_lib()
        stored = native_lib.read(symbol)
        assert stored.data == vit.data

    s3_native_lib = get_native_lib("arcticc.nonreg_s3")
    stored = s3_native_lib.read(symbol)
    assert stored.data == vit.data


def convert_series_bytes(series):
    rs = series.reset_index()
    cv = convert_bytes_to_strings(rs)
    if isinstance(series.index, pd.MultiIndex):
        index_vals = cv.values[:, :-1]
        tuples = [tuple(x) for x in index_vals]
        index = pd.MultiIndex.from_tuples(tuples, names=series.index.names)
    else:
        index = pd.Index(cv.values[:, 0], name=series.index.name)

    ret = pd.Series(cv.values[:, -1].astype(series.values.dtype), index=index, name=series.index.name)
    ret = ret.rename(series.name)
    return ret


def compare_series_as_string(left, right):
    left_conv = convert_series_bytes(left)
    right_conv = convert_series_bytes(right)
    assert_series_equal(left_conv, right_conv)


@param_dict(
    "symbol",
    {
        # "voltaetf_fweights": "resvol.VOLTAETF__FSF_more_metadata/v1/predictors/params/fweights",
        "voltaetf_out": "resvol.VOLTAETF__FSF_more_metadata/v1/signals/ols/out"
    },
)
def test_rt_series(lmdb_version_store, symbol, get_mongoose_lib):
    print("Doing {}".format(symbol))
    lib = get_mongoose_lib()
    vit = lib.read(symbol)
    meta = vit.metadata["wrapped_meta"]
    wit = lmdb_version_store.write(symbol, vit.data, metadata=None if not meta else meta)
    assert wit is not None
    d = lmdb_version_store.read(symbol)
    compare_series_as_string(d.data, vit.data)

    native_lib = get_native_lib()
    stored = native_lib.read(symbol)
    compare_series_as_string(stored.data, vit.data)

    s3_native_lib = get_native_lib("arcticc.nonreg_s3")
    stored = s3_native_lib.read(symbol)
    compare_series_as_string(stored.data, vit.data)
