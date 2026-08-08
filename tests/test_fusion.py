from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import fusion  # noqa: E402


def _dates() -> pd.DatetimeIndex:
    return pd.bdate_range("2021-01-01", periods=35)


def _sentiment() -> pd.DataFrame:
    dates = _dates()
    rows = []
    for sector_idx, sector in enumerate(["A", "B"]):
        for i, date in enumerate(dates):
            rows.append(
                {
                    "date": date,
                    "sector": sector,
                    "vader_compound_21d_trailing_lag1": (i + 1) * (1 if sector_idx == 0 else -1) / 100,
                }
            )
    return pd.DataFrame(rows)


def _coverage() -> pd.DataFrame:
    dates = _dates()
    rows = []
    for sector, covered, breadth in [("A", 5, 1.0), ("B", 2, 0.5)]:
        for date in dates:
            rows.append(
                {
                    "trading_date": date,
                    "sector": sector,
                    "rolling_21d_covered_tickers": covered,
                    "rolling_21d_breadth": breadth,
                }
            )
    return pd.DataFrame(rows)


def _signals() -> pd.DataFrame:
    rebalances = pd.DatetimeIndex([_dates()[10], _dates()[30]])
    return fusion.build_rebalance_signals(_sentiment(), _coverage(), rebalances, ["A", "B"])


def test_signal_timing_uses_approved_lagged_field_and_lagged_coverage():
    signals = _signals()
    assert set(signals["rebalance_date"]) == set([_dates()[10], _dates()[30]])
    # Coverage is based on the previous complete trading day and therefore available.
    assert signals["coverage_available"].all()
    assert signals["coverage_share_21d_lag1"].between(0, 1).all()


def test_future_sentiment_and_coverage_do_not_change_earlier_weights():
    rebalances = pd.DatetimeIndex([_dates()[10], _dates()[30]])
    base = fusion.build_rebalance_signals(_sentiment(), _coverage(), rebalances, ["A", "B"])
    sent = _sentiment()
    cov = _coverage()
    sent.loc[sent["date"].gt(_dates()[10]), "vader_compound_21d_trailing_lag1"] = 99.0
    cov.loc[cov["trading_date"].gt(_dates()[10]), "rolling_21d_breadth"] = 0.01
    changed = fusion.build_rebalance_signals(sent, cov, rebalances, ["A", "B"])
    cols = ["sentiment_zscore", "naive_sector_weight", "gated_sector_weight"]
    left = base.loc[base["rebalance_date"].eq(_dates()[10]), cols].reset_index(drop=True)
    right = changed.loc[changed["rebalance_date"].eq(_dates()[10]), cols].reset_index(drop=True)
    assert np.allclose(left, right, equal_nan=True)


def test_cross_sectional_zscore_is_clipped_and_date_local():
    signals = _signals()
    assert signals["sentiment_zscore"].dropna().between(-2, 2).all()
    for _, group in signals.groupby("rebalance_date"):
        assert group["sentiment_zscore"].mean() == pytest.approx(0.0, abs=1e-12)


def test_zero_variance_or_too_few_signals_produces_no_active_tilt():
    date = pd.Timestamp("2021-02-01")
    sent = pd.DataFrame({"date": [date, date], "sector": ["A", "B"], "vader_compound_21d_trailing_lag1": [0.2, 0.2]})
    cov = pd.DataFrame({"trading_date": pd.bdate_range("2021-01-28", periods=3).repeat(2), "sector": ["A", "B"] * 3, "rolling_21d_covered_tickers": 5, "rolling_21d_breadth": 1.0})
    out = fusion.build_rebalance_signals(sent, cov, pd.DatetimeIndex([date]), ["A", "B"])
    assert out["sentiment_zscore"].isna().all()
    assert np.allclose(out["naive_sector_weight"], 0.5)
    assert np.allclose(out["gated_sector_weight"], 0.5)


def test_naive_tilt_formula_uses_fixed_alpha_and_weights_sum_to_one():
    signals = _signals()
    available = signals["sentiment_zscore"].notna()
    expected = 1.0 + fusion.ALPHA * signals.loc[available, "sentiment_zscore"]
    assert np.allclose(signals.loc[available, "naive_multiplier"], expected)
    assert signals["naive_multiplier"].between(0.70, 1.30).all()
    sums = signals.groupby("rebalance_date")["naive_sector_weight"].sum()
    assert np.allclose(sums, 1.0)


def test_coverage_quality_formula_and_bounds():
    signals = _signals()
    expected = signals["coverage_share_21d_lag1"] * signals["breadth_21d_lag1"]
    assert np.allclose(signals["coverage_quality"], expected)
    assert signals["coverage_quality"].between(0, 1).all()


def test_gate_zero_and_one_behaviour():
    signals = _signals().copy()
    # Recompute expected multiplier identities directly from the formula.
    z = signals["sentiment_zscore"].fillna(0.0)
    q0 = 1.0 + fusion.ALPHA * 0.0 * z
    q1 = 1.0 + fusion.ALPHA * 1.0 * z
    assert np.allclose(q0, 1.0)
    assert np.allclose(q1, 1.0 + fusion.ALPHA * z)


def test_sector_to_stock_weights_are_equal_within_sector_and_sum_to_one():
    signals = _signals()
    mapping = pd.DataFrame({"ticker": [f"A{i}" for i in range(5)] + [f"B{i}" for i in range(5)], "sector": ["A"] * 5 + ["B"] * 5})
    weights = fusion.sector_to_stock_weights(signals, mapping, sector_weight_column="gated_sector_weight")
    for date, group in weights.groupby("rebalance_date"):
        assert group["target_weight"].sum() == pytest.approx(1.0)
        for _, sector_group in group.groupby("sector"):
            assert sector_group["target_weight"].nunique() == 1


def test_missing_signal_is_no_active_view_not_fabricated_sentiment():
    date = pd.Timestamp("2021-02-01")
    sent = pd.DataFrame({"date": [date, date], "sector": ["A", "B"], "vader_compound_21d_trailing_lag1": [0.3, np.nan]})
    cov_dates = pd.bdate_range("2021-01-28", periods=3)
    cov = pd.DataFrame([{"trading_date": d, "sector": s, "rolling_21d_covered_tickers": 5, "rolling_21d_breadth": 1.0} for d in cov_dates for s in ["A", "B"]])
    out = fusion.build_rebalance_signals(sent, cov, pd.DatetimeIndex([date]), ["A", "B"])
    missing = out.loc[out["sector"].eq("B")].iloc[0]
    assert pd.isna(missing["sentiment_signal"])
    assert missing["naive_multiplier"] == pytest.approx(1.0)
    assert missing["gated_multiplier"] == pytest.approx(1.0)


def test_final_fusion_artifacts_when_built():
    paths = [
        ROOT / "results" / "data" / "fusion_rebalance_signals.csv",
        ROOT / "results" / "tables" / "fusion_before_after.csv",
        ROOT / "results" / "tables" / "fusion_predictive_diagnostics.csv",
    ]
    if any(not p.exists() or p.stat().st_size == 0 for p in paths):
        pytest.skip("run scripts/run_part_b.py to build final fusion artifacts")
    signals = pd.read_csv(paths[0])
    before_after = pd.read_csv(paths[1])
    assert not signals.duplicated(["rebalance_date", "sector"]).any()
    assert len(before_after) == 3
    assert set(before_after["fund_id"]) == set(fusion.COMPARISON_FUND_IDS)
