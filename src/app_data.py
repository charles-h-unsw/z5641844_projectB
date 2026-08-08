"""Read-only app artifact loading and validation for Signal Mosaic."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src.app_copy import BASE_FUND_IDS, FUSION_FUND_IDS


class AppDataError(RuntimeError):
    """Raised when a precomputed app artifact is missing or malformed."""


APP_ARTIFACTS: dict[str, dict[str, object]] = {
    "fund_returns": {
        "path": "results/data/fund_returns.csv",
        "date_cols": ["date"],
        "required_cols": {
            "date",
            "fund_id",
            "fund_name",
            "asset_family",
            "method",
            "gross_return",
            "net_return",
            "gross_wealth",
            "net_wealth",
            "net_drawdown",
            "rebalance_flag",
            "turnover",
            "transaction_cost",
        },
    },
    "fund_weights": {
        "path": "results/data/fund_weights.csv",
        "date_cols": ["rebalance_date"],
        "required_cols": {
            "rebalance_date",
            "fund_id",
            "fund_name",
            "asset_family",
            "method",
            "asset",
            "asset_class",
            "sector",
            "pretrade_weight",
            "target_weight",
            "is_latest_rebalance",
        },
    },
    "sector_sentiment": {
        "path": "results/data/sector_sentiment_index.csv",
        "date_cols": ["date", "signal_source_date"],
        "required_cols": {
            "date",
            "sector",
            "vader_compound_raw",
            "vader_compound_lag1",
            "vader_compound_21d_trailing",
            "vader_compound_21d_trailing_lag1",
            "positive_ticker_share",
            "neutral_ticker_share",
            "negative_ticker_share",
            "article_count",
            "covered_tickers",
            "coverage_share",
            "breadth",
            "has_news",
            "signal_source_date",
            "signal_available",
        },
    },
    "fusion_signals": {
        "path": "results/data/fusion_rebalance_signals.csv",
        "date_cols": ["rebalance_date"],
        "required_cols": {
            "rebalance_date",
            "sector",
            "sentiment_signal",
            "sentiment_zscore",
            "coverage_share_21d_lag1",
            "breadth_21d_lag1",
            "coverage_quality",
            "naive_multiplier",
            "gated_multiplier",
            "base_sector_weight",
            "naive_sector_weight",
            "gated_sector_weight",
            "signal_available",
            "coverage_available",
        },
    },
    "metrics": {
        "path": "results/tables/performance_metrics.csv",
        "date_cols": ["first_live_date", "end_date"],
        "required_cols": {
            "fund_id",
            "fund_name",
            "asset_family",
            "method",
            "first_live_date",
            "end_date",
            "number_of_observations",
            "annualisation_factor",
            "cumulative_return_net",
            "annualised_return_net",
            "annualised_volatility_net",
            "Sharpe_net",
            "maximum_drawdown_net",
            "average_rebalance_turnover",
            "total_transaction_cost",
            "number_of_rebalances",
            "current_number_of_holdings",
            "largest_current_weight",
        },
    },
    "latest_holdings": {
        "path": "results/tables/fund_latest_holdings.csv",
        "date_cols": ["rebalance_date"],
        "required_cols": {
            "rebalance_date",
            "fund_id",
            "fund_name",
            "asset_family",
            "method",
            "asset",
            "asset_class",
            "sector",
            "target_weight",
        },
    },
    "fact_sheet": {
        "path": "results/tables/fund_fact_sheet_summary.csv",
        "date_cols": ["first_live_date", "end_date"],
        "required_cols": {
            "fund_id",
            "fund_name",
            "asset_family",
            "method",
            "first_live_date",
            "end_date",
            "annualised_return_net",
            "annualised_volatility_net",
            "Sharpe_net",
            "maximum_drawdown_net",
        },
    },
    "backtest_design": {
        "path": "results/tables/fund_backtest_design.csv",
        "date_cols": ["first_live_date"],
        "required_cols": {"fund_id", "fund_name", "asset_family", "first_live_date", "calendar", "rebalance_rule"},
    },
    "fusion_before_after": {
        "path": "results/tables/fusion_before_after.csv",
        "date_cols": [],
        "required_cols": {
            "fund_name",
            "annualised_return_net",
            "annualised_volatility_net",
            "Sharpe_net",
            "maximum_drawdown_net",
            "cumulative_return_net",
            "change_in_return_vs_base",
            "change_in_Sharpe_vs_base",
        },
    },
    "fusion_predictive": {
        "path": "results/tables/fusion_predictive_diagnostics.csv",
        "date_cols": [],
        "required_cols": {
            "sample",
            "pooled_spearman",
            "average_cross_sectional_spearman",
            "valid_monthly_observations",
            "valid_pair_observations",
        },
    },
    "app_inventory": {
        "path": "results/tables/app_artifact_inventory.csv",
        "date_cols": [],
        "required_cols": {"path", "exists", "row_count", "schema_status", "readiness_status"},
    },
    "pipeline_validation": {
        "path": "results/tables/pipeline_validation.csv",
        "date_cols": [],
        "required_cols": {"validation_name", "expected", "observed", "status", "notes"},
    },
    "sentiment_diagnostics": {
        "path": "results/tables/sentiment_model_diagnostics.csv",
        "date_cols": [],
        "required_cols": {
            "total_scored_headlines",
            "exact_zero_compound_count",
            "vader_neutral_count",
            "positive_count",
            "negative_count",
            "exact_zero_compound_share",
            "vader_neutral_share",
            "positive_share",
            "negative_share",
        },
    },
}


def _read_artifact(project_root: Path, spec: dict[str, object]) -> pd.DataFrame:
    path = project_root / str(spec["path"])
    if not path.exists():
        raise AppDataError(f"Missing precomputed artifact: {spec['path']}")
    frame = pd.read_csv(path)
    required_cols = set(spec["required_cols"])
    missing = required_cols.difference(frame.columns)
    if missing:
        raise AppDataError(f"{spec['path']} is missing columns: {sorted(missing)}")
    for column in spec.get("date_cols", []):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce")
    return frame


def _reject_infinite(name: str, frame: pd.DataFrame) -> None:
    numeric = frame.select_dtypes(include=[np.number])
    if not numeric.empty and np.isinf(numeric.to_numpy()).any():
        raise AppDataError(f"{name} contains positive or negative infinity.")


def validate_app_data(data: dict[str, pd.DataFrame]) -> None:
    fund_returns = data["fund_returns"]
    fund_weights = data["fund_weights"]
    sentiment = data["sector_sentiment"]
    metrics = data["metrics"]
    latest = data["latest_holdings"]
    pipeline = data["pipeline_validation"]
    inventory = data["app_inventory"]

    for name, frame in data.items():
        _reject_infinite(name, frame)

    expected_funds = set(BASE_FUND_IDS + FUSION_FUND_IDS)
    funds = set(metrics["fund_id"].unique())
    if funds != expected_funds:
        raise AppDataError(f"Expected 11 known funds, observed {len(funds)}.")
    if len(metrics) != 11:
        raise AppDataError(f"Expected 11 performance metric rows, observed {len(metrics)}.")
    if fund_returns["fund_id"].nunique() != 11:
        raise AppDataError("Fund return artifact does not contain all 11 funds.")
    if latest["fund_id"].nunique() != 11:
        raise AppDataError("Latest holdings artifact does not contain all 11 funds.")
    if sentiment["sector"].nunique() != 10:
        raise AppDataError("Sector sentiment artifact must contain ten equity sectors.")
    if fund_returns.duplicated(["date", "fund_id"]).any():
        raise AppDataError("Duplicate date-fund rows exist in fund_returns.csv.")
    if fund_weights.duplicated(["rebalance_date", "fund_id", "asset"]).any():
        raise AppDataError("Duplicate rebalance-fund-asset rows exist in fund_weights.csv.")
    if sentiment.duplicated(["date", "sector"]).any():
        raise AppDataError("Duplicate date-sector rows exist in sector_sentiment_index.csv.")
    if (pipeline["status"] != "PASS").any():
        raise AppDataError("Pipeline validation contains a non-PASS row.")
    if not (inventory["readiness_status"] == "READY").all():
        raise AppDataError("App artifact inventory contains a non-READY row.")

    wealth_cols = ["gross_wealth", "net_wealth"]
    if (fund_returns[wealth_cols] <= 0).any().any():
        raise AppDataError("Fund wealth values must be positive.")
    if (fund_returns["net_drawdown"] > 1e-12).any():
        raise AppDataError("Net drawdowns must be zero or negative.")
    if (fund_returns["transaction_cost"] < -1e-12).any():
        raise AppDataError("Transaction costs cannot be negative.")

    sentiment_cols = [
        "vader_compound_raw",
        "vader_compound_lag1",
        "vader_compound_21d_trailing",
        "vader_compound_21d_trailing_lag1",
    ]
    for column in sentiment_cols:
        valid = sentiment[column].dropna()
        if ((valid < -1.0) | (valid > 1.0)).any():
            raise AppDataError(f"{column} contains values outside [-1, 1].")


def _load_app_data_uncached(project_root: Path) -> dict[str, pd.DataFrame]:
    data = {name: _read_artifact(project_root, spec) for name, spec in APP_ARTIFACTS.items()}
    validate_app_data(data)
    return data


@st.cache_data(show_spinner=False)
def load_app_data(project_root: str) -> dict[str, pd.DataFrame]:
    """Load validated app artifacts from project-local CSV files."""
    return _load_app_data_uncached(Path(project_root))
