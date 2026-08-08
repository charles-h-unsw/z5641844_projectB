"""Out-of-sample fund tests for Project B."""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src import etl, features, portfolios  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE_FUND_IDS = {
    "equity_equal_weight",
    "equity_minimum_variance",
    "equity_risk_parity",
    "crypto_equal_weight",
    "crypto_minimum_variance",
    "crypto_risk_parity",
    "combined_equal_weight",
    "combined_minimum_variance",
    "combined_risk_parity",
}


@pytest.fixture(scope="session")
def fund_artifacts():
    paths = {
        "returns": ROOT / "results" / "data" / "fund_returns.csv",
        "weights": ROOT / "results" / "data" / "fund_weights.csv",
        "metrics": ROOT / "results" / "tables" / "performance_metrics.csv",
        "diagnostics": ROOT / "results" / "tables" / "fund_optimizer_diagnostics.csv",
        "design": ROOT / "results" / "tables" / "fund_backtest_design.csv",
        "latest": ROOT / "results" / "tables" / "fund_latest_holdings.csv",
    }
    missing = [str(path.relative_to(ROOT)) for path in paths.values() if not path.exists()]
    if missing:
        pytest.fail(f"run scripts/build_funds.py first; missing {missing}")
    return {
        "returns": pd.read_csv(paths["returns"], parse_dates=["date"]),
        "weights": pd.read_csv(paths["weights"], parse_dates=["rebalance_date"]),
        "metrics": pd.read_csv(paths["metrics"], parse_dates=["first_live_date", "end_date"]),
        "diagnostics": pd.read_csv(
            paths["diagnostics"],
            parse_dates=["rebalance_date", "next_rebalance_date", "training_start", "training_end"],
        ),
        "design": pd.read_csv(
            paths["design"],
            parse_dates=["initial_estimation_start", "initial_estimation_end", "first_live_date", "end_date"],
        ),
        "latest": pd.read_csv(paths["latest"], parse_dates=["rebalance_date"]),
    }


def _synthetic_returns(n_assets: int = 5) -> pd.DataFrame:
    dates_2020 = pd.bdate_range("2020-01-02", "2020-12-31")
    dates_2021 = pd.bdate_range("2021-01-01", "2021-03-15")
    dates = dates_2020.append(dates_2021)
    columns = [f"A{i}" for i in range(n_assets)]
    rng = np.random.default_rng(3645)
    market = rng.normal(0.0002, 0.006, size=len(dates))
    data = np.zeros((len(dates), n_assets))
    for i in range(n_assets):
        idiosyncratic = rng.normal(0.0, 0.002 + i * 0.0005, size=len(dates))
        data[:, i] = 0.0002 + (0.4 + i * 0.03) * market + idiosyncratic
    data[:, 0] += np.sin(np.arange(len(dates)) / 3.0) * 0.001
    data[:, 1] += np.cos(np.arange(len(dates)) / 5.0) * 0.0015
    return pd.DataFrame(data, index=dates, columns=columns)


def test_no_lookahead_diagnostics_and_first_live_dates(fund_artifacts):
    diagnostics = fund_artifacts["diagnostics"]
    design = fund_artifacts["design"]

    assert (diagnostics["training_end"] < diagnostics["rebalance_date"]).all()
    assert diagnostics["rebalance_date"].min() > pd.Timestamp("2020-12-31")
    assert set(design["first_live_date"].dt.year) == {2021}
    expected = {
        "Equity": pd.Timestamp("2021-01-04"),
        "Combined": pd.Timestamp("2021-01-04"),
        "Crypto": pd.Timestamp("2021-01-01"),
    }
    actual = design.groupby("asset_family", observed=True)["first_live_date"].min().to_dict()
    assert actual == expected


def test_future_returns_do_not_change_earlier_weights():
    returns = _synthetic_returns(5)
    spec = portfolios.FundSpec(
        "synthetic_minvar",
        "Synthetic Minimum Variance",
        "Synthetic",
        portfolios.METHOD_MIN_VARIANCE,
        252,
        "business-day synthetic",
    )
    base = portfolios.oos_backtest(
        returns,
        method=portfolios.METHOD_MIN_VARIANCE,
        fund_spec=spec,
        max_weight=0.5,
    )["weights"]
    changed = returns.copy()
    changed.loc[changed.index >= pd.Timestamp("2021-02-01"), "A0"] += 0.20
    altered = portfolios.oos_backtest(
        changed,
        method=portfolios.METHOD_MIN_VARIANCE,
        fund_spec=spec,
        max_weight=0.5,
    )["weights"]
    jan_base = base.loc[base["rebalance_date"].eq(pd.Timestamp("2021-01-01")), "target_weight"].to_numpy()
    jan_altered = altered.loc[altered["rebalance_date"].eq(pd.Timestamp("2021-01-01")), "target_weight"].to_numpy()
    assert np.allclose(jan_base, jan_altered, atol=1e-12)


def test_calendar_and_annualisation_contracts(fund_artifacts):
    design = fund_artifacts["design"]
    assert design.loc[design["asset_family"].eq("Equity"), "annualisation_factor"].eq(252).all()
    assert design.loc[design["asset_family"].eq("Combined"), "annualisation_factor"].eq(252).all()
    assert design.loc[design["asset_family"].eq("Crypto"), "annualisation_factor"].eq(365).all()

    equities = etl.load_clean_equities()
    crypto = etl.load_clean_crypto()
    equity_returns = features.daily_returns(equities)
    crypto_returns = features.daily_returns(crypto)
    combined = features.combined_returns_on_equity_calendar(equity_returns, crypto_returns)
    crypto_live = crypto_returns.loc[crypto_returns.index >= pd.Timestamp("2021-01-01")]
    combined_live = combined.loc[combined.index >= pd.Timestamp("2021-01-04")]

    assert any(date.weekday() >= 5 for date in crypto_live.index)
    assert not any(date.weekday() >= 5 for date in combined_live.index)
    assert combined.index.equals(equity_returns.index)
    date = combined_live.index[10]
    assert combined.loc[date, "CR_BTC-USD"] == pytest.approx(crypto_returns.loc[date, "BTC-USD"])


def test_weight_validity_and_method_distinction(fund_artifacts):
    weights = fund_artifacts["weights"]
    latest = fund_artifacts["latest"]
    target_sums = weights.groupby(["fund_id", "rebalance_date"], observed=True)["target_weight"].sum()
    assert np.allclose(target_sums.to_numpy(), 1.0, atol=1e-8)
    assert np.isfinite(weights[["pretrade_weight", "target_weight"]].to_numpy(dtype=float)).all()
    assert weights["target_weight"].ge(-1e-9).all()

    optimised = weights.loc[~weights["method"].eq(portfolios.METHOD_EQUAL_WEIGHT)]
    assert optimised["target_weight"].le(portfolios.MAX_TARGET_WEIGHT + 1e-8).all()

    equal = weights.loc[weights["method"].eq(portfolios.METHOD_EQUAL_WEIGHT)]
    counts = equal.groupby(["fund_id", "rebalance_date"], observed=True)["asset"].transform("count")
    assert np.allclose(equal["target_weight"].to_numpy(), 1.0 / counts.to_numpy(), atol=1e-12)

    assert set(latest["fund_id"]).issuperset(BASE_FUND_IDS)
    pivot = weights.pivot_table(
        index=["asset_family", "rebalance_date", "asset"],
        columns="method",
        values="target_weight",
    )
    identical_everywhere = np.allclose(
        pivot[portfolios.METHOD_EQUAL_WEIGHT].fillna(-1),
        pivot[portfolios.METHOD_MIN_VARIANCE].fillna(-1),
    ) and np.allclose(
        pivot[portfolios.METHOD_EQUAL_WEIGHT].fillna(-1),
        pivot[portfolios.METHOD_RISK_PARITY].fillna(-1),
    )
    assert not identical_everywhere


def test_optimizer_validity_on_synthetic_data():
    returns = _synthetic_returns(10)
    train = returns.loc[returns.index < pd.Timestamp("2021-01-01")]
    cov, _ = portfolios.covariance_matrix(train)
    minvar = portfolios.optimise_minimum_variance(train, max_weight=0.4)
    riskparity = portfolios.optimise_risk_parity(train, max_weight=0.4)
    equal = portfolios.equal_weight(train.shape[1])

    assert minvar.success
    assert minvar.weights.sum() == pytest.approx(1.0)
    assert (minvar.weights >= -1e-9).all()
    assert (minvar.weights <= 0.4 + 1e-8).all()
    assert minvar.weights @ cov @ minvar.weights <= equal @ cov @ equal + 1e-10

    assert riskparity.success
    assert riskparity.weights.sum() == pytest.approx(1.0)
    assert (riskparity.weights >= -1e-9).all()
    assert (riskparity.weights <= 0.4 + 1e-8).all()
    assert riskparity.max_risk_contribution_deviation < 0.15
    assert not np.allclose(minvar.weights, equal, atol=1e-8)


def test_portfolio_accounting_on_synthetic_data():
    returns = _synthetic_returns(5)
    live_dates = returns.loc[returns.index >= pd.Timestamp("2021-01-01")].index
    returns.loc[live_dates[:3]] = np.array(
        [
            [0.01, 0.00, 0.00, 0.00, 0.00],
            [0.00, 0.02, 0.00, 0.00, 0.00],
            [0.00, 0.00, -0.01, 0.00, 0.00],
        ]
    )
    spec = portfolios.FundSpec("synthetic_ew", "Synthetic Equal Weight", "Synthetic", portfolios.METHOD_EQUAL_WEIGHT, 252, "business-day synthetic")
    result = portfolios.oos_backtest(
        returns,
        method=portfolios.METHOD_EQUAL_WEIGHT,
        fund_spec=spec,
        transaction_cost_rate=0.001,
    )
    fund_returns = result["returns"].sort_values("date").reset_index(drop=True)
    weights = result["weights"]

    assert fund_returns.loc[0, "date"] == pd.Timestamp("2021-01-01")
    assert fund_returns.loc[0, "gross_return"] == pytest.approx(0.002)
    first_post = np.repeat(0.2, 5) * (1.0 + returns.loc[pd.Timestamp("2021-01-01")].to_numpy()) / 1.002
    second_return = float(first_post @ returns.loc[pd.Timestamp("2021-01-04")].to_numpy())
    assert fund_returns.loc[1, "gross_return"] == pytest.approx(second_return)
    assert fund_returns.loc[0, "transaction_cost"] == 0
    subsequent_costs = fund_returns.loc[fund_returns["rebalance_flag"], "transaction_cost"].iloc[1:]
    assert subsequent_costs.ge(0).all()
    assert fund_returns["net_return"].le(fund_returns["gross_return"] + 1e-12).all()

    zero = portfolios.oos_backtest(
        returns,
        method=portfolios.METHOD_EQUAL_WEIGHT,
        fund_spec=spec,
        transaction_cost_rate=0.0,
    )["returns"]
    assert np.allclose(zero["gross_wealth"], zero["net_wealth"], atol=1e-12)
    first_feb = weights.loc[weights["rebalance_date"].eq(pd.Timestamp("2021-02-01"))]
    assert not np.allclose(first_feb["pretrade_weight"], first_feb["target_weight"], atol=1e-12)


def test_metric_formulas_and_rows(fund_artifacts):
    metrics = fund_artifacts["metrics"]
    returns = fund_artifacts["returns"]
    base_metrics = metrics.loc[metrics["fund_id"].isin(BASE_FUND_IDS)]
    assert len(base_metrics) == 9
    for _, row in base_metrics.iterrows():
        group = returns.loc[returns["fund_id"].eq(row["fund_id"])].sort_values("date")
        net = group["net_return"].astype(float)
        gross = group["gross_return"].astype(float)
        ann = int(row["annualisation_factor"])
        expected_ann = float(np.prod(1.0 + net) ** (ann / len(net)) - 1.0)
        expected_vol = float(net.std(ddof=1) * np.sqrt(ann))
        expected_sharpe = float(net.mean() / net.std(ddof=1) * np.sqrt(ann))
        assert row["annualised_return_net"] == pytest.approx(expected_ann)
        assert row["annualised_volatility_net"] == pytest.approx(expected_vol)
        assert row["Sharpe_net"] == pytest.approx(expected_sharpe)
        assert row["cumulative_return_gross"] == pytest.approx(group["gross_wealth"].iloc[-1] - 1.0)
        assert row["maximum_drawdown_net"] == pytest.approx(group["net_drawdown"].min())
        assert group["net_drawdown"].le(1e-12).all()


def test_artifact_schemas_and_keys(fund_artifacts):
    returns = fund_artifacts["returns"]
    weights = fund_artifacts["weights"]
    metrics = fund_artifacts["metrics"]
    required_files = [
        ROOT / "results" / "data" / "fund_returns.csv",
        ROOT / "results" / "data" / "fund_weights.csv",
        ROOT / "results" / "tables" / "performance_metrics.csv",
        ROOT / "results" / "tables" / "fund_backtest_design.csv",
        ROOT / "results" / "tables" / "fund_optimizer_diagnostics.csv",
        ROOT / "results" / "tables" / "fund_latest_holdings.csv",
        ROOT / "results" / "tables" / "fund_fact_sheet_summary.csv",
        ROOT / "results" / "figures" / "fund_growth_of_one_by_family.png",
        ROOT / "results" / "figures" / "fund_drawdowns_combined.png",
        ROOT / "results" / "figures" / "fund_weights_over_time_combined.png",
        ROOT / "results" / "figures" / "fund_risk_return_comparison.png",
    ]
    for path in required_files:
        assert path.exists()
    assert set(returns["fund_id"]).issuperset(BASE_FUND_IDS)
    assert set(returns["fund_id"]) == set(weights["fund_id"]) == set(metrics["fund_id"])
    assert not returns.duplicated(["date", "fund_id"]).any()
    assert not weights.duplicated(["rebalance_date", "fund_id", "asset"]).any()
    assert pd.api.types.is_datetime64_any_dtype(returns["date"])
    assert pd.api.types.is_datetime64_any_dtype(weights["rebalance_date"])
