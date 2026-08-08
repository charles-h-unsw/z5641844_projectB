"""Look-ahead-safe sentiment fusion for the equity fund universe."""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np
import pandas as pd

from src import portfolios

ALPHA = 0.15
BASE_SECTOR_WEIGHT = 0.10
STOCKS_PER_SECTOR = 5
FUSION_FUND_IDS = {
    "equity_sentiment_naive",
    "equity_sentiment_coverage_gated",
}
COMPARISON_FUND_IDS = [
    "equity_equal_weight",
    "equity_sentiment_naive",
    "equity_sentiment_coverage_gated",
]


@dataclass(frozen=True)
class FusionSpec:
    fund_id: str
    fund_name: str
    method: str
    sector_weight_column: str


def fusion_specs() -> list[FusionSpec]:
    """Stable identities for the two sentiment-augmented equity funds."""

    return [
        FusionSpec(
            fund_id="equity_sentiment_naive",
            fund_name="Equity Naive Sentiment Tilt",
            method="Naive Sentiment Tilt",
            sector_weight_column="naive_sector_weight",
        ),
        FusionSpec(
            fund_id="equity_sentiment_coverage_gated",
            fund_name="Equity Coverage-Gated Sentiment Tilt",
            method="Coverage-Gated Sentiment Tilt",
            sector_weight_column="gated_sector_weight",
        ),
    ]


def build_rebalance_signals(
    sector_sentiment: pd.DataFrame,
    coverage_daily: pd.DataFrame,
    rebalance_dates: pd.DatetimeIndex | list[pd.Timestamp],
    sectors: list[str],
    *,
    alpha: float = ALPHA,
) -> pd.DataFrame:
    """Return rebalance-date sector signals and naive/gated sector weights."""

    dates = pd.DatetimeIndex(pd.to_datetime(rebalance_dates)).normalize()
    sector_grid = pd.MultiIndex.from_product(
        [dates, sorted(sectors)],
        names=["rebalance_date", "sector"],
    ).to_frame(index=False)

    sentiment = _prepare_sentiment(sector_sentiment)
    coverage = _prepare_lagged_coverage(coverage_daily)
    signals = (
        sector_grid.merge(
            sentiment,
            on=["rebalance_date", "sector"],
            how="left",
            validate="one_to_one",
        )
        .merge(
            coverage,
            on=["rebalance_date", "sector"],
            how="left",
            validate="one_to_one",
        )
    )
    signals["signal_available"] = signals["sentiment_signal"].notna()
    signals["coverage_available"] = (
        signals["coverage_share_21d_lag1"].notna()
        & signals["breadth_21d_lag1"].notna()
    )
    signals["coverage_quality"] = (
        signals["coverage_share_21d_lag1"] * signals["breadth_21d_lag1"]
    )
    signals["coverage_quality"] = signals["coverage_quality"].where(
        signals["coverage_available"],
        0.0,
    ).clip(lower=0.0, upper=1.0)
    signals = _add_cross_sectional_zscores(signals)
    signals["naive_multiplier"] = 1.0 + alpha * signals["sentiment_zscore"].fillna(0.0)
    signals["gated_multiplier"] = (
        1.0
        + alpha
        * signals["coverage_quality"].fillna(0.0)
        * signals["sentiment_zscore"].fillna(0.0)
    )
    signals["base_sector_weight"] = BASE_SECTOR_WEIGHT
    signals["naive_unnormalised"] = signals["base_sector_weight"] * signals["naive_multiplier"]
    signals["gated_unnormalised"] = signals["base_sector_weight"] * signals["gated_multiplier"]
    signals["naive_sector_weight"] = signals["naive_unnormalised"] / signals.groupby(
        "rebalance_date", observed=True
    )["naive_unnormalised"].transform("sum")
    signals["gated_sector_weight"] = signals["gated_unnormalised"] / signals.groupby(
        "rebalance_date", observed=True
    )["gated_unnormalised"].transform("sum")
    result = signals[
        [
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
        ]
    ].sort_values(["rebalance_date", "sector"], kind="stable").reset_index(drop=True)
    validate_rebalance_signals(result)
    return result


def sector_to_stock_weights(
    rebalance_signals: pd.DataFrame,
    ticker_sector_map: pd.DataFrame,
    *,
    sector_weight_column: str,
) -> pd.DataFrame:
    """Expand sector weights to equal stock weights within each sector."""

    required = {"rebalance_date", "sector", sector_weight_column}
    _require_columns(rebalance_signals, required, "rebalance signals")
    _require_columns(ticker_sector_map, {"ticker", "sector"}, "ticker sector map")
    tickers = ticker_sector_map.copy()
    tickers["ticker"] = tickers["ticker"].astype(str)
    tickers["sector"] = tickers["sector"].astype(str)
    counts = tickers.groupby("sector", observed=True)["ticker"].transform("count")
    if not counts.eq(STOCKS_PER_SECTOR).all():
        raise ValueError("each sector must contain five stocks")
    weights = rebalance_signals[["rebalance_date", "sector", sector_weight_column]].merge(
        tickers,
        on="sector",
        how="left",
        validate="many_to_many",
    )
    weights["target_weight"] = weights[sector_weight_column] / STOCKS_PER_SECTOR
    return (
        weights.rename(columns={"ticker": "asset"})
        [["rebalance_date", "asset", "sector", "target_weight"]]
        .sort_values(["rebalance_date", "asset"], kind="stable")
        .reset_index(drop=True)
    )


def backtest_exogenous_weights(
    returns: pd.DataFrame,
    target_weights: pd.DataFrame,
    spec: FusionSpec,
    *,
    transaction_cost_rate: float = portfolios.TRANSACTION_COST_RATE,
) -> dict[str, pd.DataFrame]:
    """Run buy-and-hold accounting for precomputed monthly target weights."""

    frame = portfolios.clean_return_matrix(returns)
    weights = target_weights.copy()
    weights["rebalance_date"] = _normalise_datetime(weights["rebalance_date"])
    weights["asset"] = weights["asset"].astype(str)
    weights["target_weight"] = pd.to_numeric(weights["target_weight"], errors="raise")
    if weights.duplicated(["rebalance_date", "asset"]).any():
        raise ValueError("target weights have duplicate rebalance-date asset rows")
    assets = frame.columns.astype(str).tolist()
    if set(weights["asset"].unique()) != set(assets):
        raise ValueError("target weights and return columns use different assets")
    rebalance_dates = pd.DatetimeIndex(sorted(weights["rebalance_date"].unique()))
    live_returns = frame.loc[frame.index >= rebalance_dates.min()].copy()
    current_weights: np.ndarray | None = None
    gross_wealth = 1.0
    net_wealth = 1.0
    return_rows: list[dict[str, object]] = []
    weight_rows: list[dict[str, object]] = []
    rebalance_set = set(rebalance_dates)

    for date, row in live_returns.iterrows():
        rebalance_flag = date in rebalance_set
        turnover = 0.0
        transaction_cost = 0.0
        if rebalance_flag:
            target = (
                weights.loc[weights["rebalance_date"].eq(date)]
                .set_index("asset")
                .loc[assets, "target_weight"]
                .to_numpy(dtype=float)
            )
            if not np.isclose(target.sum(), 1.0, atol=1e-10):
                raise ValueError(f"target weights do not sum to one on {date.date()}")
            if (target < -1e-12).any():
                raise ValueError(f"negative target weight on {date.date()}")
            pretrade = np.zeros(len(assets)) if current_weights is None else current_weights.copy()
            if current_weights is not None:
                turnover = float(0.5 * np.abs(target - pretrade).sum())
                transaction_cost = float(transaction_cost_rate * turnover)
            current_weights = target.copy()
            meta = weights.loc[weights["rebalance_date"].eq(date)].set_index("asset").loc[assets]
            for asset, pre_w, target_w in zip(assets, pretrade, target, strict=True):
                weight_rows.append(
                    {
                        "rebalance_date": date,
                        "fund_id": spec.fund_id,
                        "fund_name": spec.fund_name,
                        "asset_family": "Equity",
                        "method": spec.method,
                        "asset": asset,
                        "asset_class": "Equity",
                        "sector": meta.loc[asset, "sector"],
                        "pretrade_weight": float(pre_w),
                        "target_weight": float(target_w),
                        "is_latest_rebalance": False,
                    }
                )
        if current_weights is None:
            raise RuntimeError("live period started before first target weights")
        asset_returns = row.to_numpy(dtype=float)
        gross_return = float(current_weights @ asset_returns)
        net_return = float((1.0 - transaction_cost) * (1.0 + gross_return) - 1.0)
        gross_wealth *= 1.0 + gross_return
        net_wealth *= 1.0 + net_return
        denominator = 1.0 + gross_return
        if denominator <= 0:
            raise RuntimeError(f"portfolio wealth became non-positive on {date.date()}")
        current_weights = current_weights * (1.0 + asset_returns) / denominator
        current_weights = _normalise_weights(current_weights)
        return_rows.append(
            {
                "date": date,
                "fund_id": spec.fund_id,
                "fund_name": spec.fund_name,
                "asset_family": "Equity",
                "method": spec.method,
                "gross_return": gross_return,
                "net_return": net_return,
                "gross_wealth": gross_wealth,
                "net_wealth": net_wealth,
                "net_drawdown": np.nan,
                "rebalance_flag": rebalance_flag,
                "turnover": turnover,
                "transaction_cost": transaction_cost,
            }
        )
    fund_returns = pd.DataFrame(return_rows)
    fund_returns["net_drawdown"] = (
        fund_returns["net_wealth"] / fund_returns["net_wealth"].cummax() - 1.0
    )
    fund_weights = pd.DataFrame(weight_rows)
    latest = fund_weights["rebalance_date"].max()
    fund_weights["is_latest_rebalance"] = fund_weights["rebalance_date"].eq(latest)
    return {"returns": fund_returns, "weights": fund_weights}


def build_fusion_funds(
    equity_returns: pd.DataFrame,
    ticker_sector_map: pd.DataFrame,
    sector_sentiment: pd.DataFrame,
    coverage_daily: pd.DataFrame,
    base_rebalance_dates: pd.DatetimeIndex,
) -> dict[str, pd.DataFrame]:
    """Build both sentiment-augmented equity funds and diagnostics."""

    sectors = sorted(ticker_sector_map["sector"].astype(str).unique())
    signals = build_rebalance_signals(
        sector_sentiment,
        coverage_daily,
        base_rebalance_dates,
        sectors,
    )
    return_parts: list[pd.DataFrame] = []
    weight_parts: list[pd.DataFrame] = []
    specs = fusion_specs()
    for spec in specs:
        targets = sector_to_stock_weights(
            signals,
            ticker_sector_map,
            sector_weight_column=spec.sector_weight_column,
        )
        bt = backtest_exogenous_weights(equity_returns, targets, spec)
        return_parts.append(bt["returns"])
        weight_parts.append(bt["weights"])
    fund_returns = pd.concat(return_parts, ignore_index=True)
    fund_weights = pd.concat(weight_parts, ignore_index=True)
    metrics = portfolios.calculate_metrics(
        fund_returns,
        fund_weights,
        [
            portfolios.FundSpec(
                spec.fund_id,
                spec.fund_name,
                "Equity",
                spec.method,
                252,
                "equity trading calendar",
            )
            for spec in specs
        ],
    )
    return {
        "fund_returns": fund_returns,
        "fund_weights": fund_weights,
        "performance_metrics": metrics,
        "fusion_rebalance_signals": signals,
    }


def fusion_before_after(metrics: pd.DataFrame) -> pd.DataFrame:
    """Compare base, naive, and gated net metrics."""

    comparison = metrics.loc[metrics["fund_id"].isin(COMPARISON_FUND_IDS)].copy()
    if set(comparison["fund_id"]) != set(COMPARISON_FUND_IDS):
        raise ValueError("missing comparison fund metric rows")
    base = comparison.loc[comparison["fund_id"].eq("equity_equal_weight")].iloc[0]
    for metric, output in [
        ("annualised_return_net", "change_in_return_vs_base"),
        ("annualised_volatility_net", "change_in_volatility_vs_base"),
        ("Sharpe_net", "change_in_Sharpe_vs_base"),
        ("maximum_drawdown_net", "change_in_max_drawdown_vs_base"),
    ]:
        comparison[output] = comparison[metric].astype(float) - float(base[metric])
    columns = [
        "fund_id",
        "fund_name",
        "annualised_return_net",
        "annualised_volatility_net",
        "Sharpe_net",
        "maximum_drawdown_net",
        "cumulative_return_net",
        "average_rebalance_turnover",
        "total_transaction_cost",
        "number_of_rebalances",
        "change_in_return_vs_base",
        "change_in_volatility_vs_base",
        "change_in_Sharpe_vs_base",
        "change_in_max_drawdown_vs_base",
    ]
    return comparison[columns].sort_values("fund_id", kind="stable").reset_index(drop=True)


def fusion_signal_diagnostics(signals: pd.DataFrame) -> pd.DataFrame:
    """Return one-row diagnostics for rebalance-sector signals and tilts."""

    valid_z = signals.loc[signals["signal_available"], "sentiment_zscore"].dropna()
    naive_active = signals["naive_sector_weight"] - BASE_SECTOR_WEIGHT
    gated_active = signals["gated_sector_weight"] - BASE_SECTOR_WEIGHT
    reduced = gated_active.abs() < naive_active.abs()
    return pd.DataFrame(
        [
            {
                "total_rebalance_sector_observations": len(signals),
                "valid_sentiment_observations": int(signals["signal_available"].sum()),
                "missing_sentiment_observations": int((~signals["signal_available"]).sum()),
                "mean_zscore": float(valid_z.mean()),
                "std_zscore": float(valid_z.std(ddof=0)),
                "share_clipped_at_minus_2": float(valid_z.eq(-2.0).mean()),
                "share_clipped_at_plus_2": float(valid_z.eq(2.0).mean()),
                "mean_coverage_quality": float(signals["coverage_quality"].mean()),
                "minimum_coverage_quality": float(signals["coverage_quality"].min()),
                "maximum_coverage_quality": float(signals["coverage_quality"].max()),
                "mean_absolute_naive_active_sector_weight": float(naive_active.abs().mean()),
                "mean_absolute_gated_active_sector_weight": float(gated_active.abs().mean()),
                "share_gate_reduced_absolute_tilt": float(reduced.mean()),
                "maximum_naive_sector_weight": float(signals["naive_sector_weight"].max()),
                "minimum_naive_sector_weight": float(signals["naive_sector_weight"].min()),
                "maximum_gated_sector_weight": float(signals["gated_sector_weight"].max()),
                "minimum_gated_sector_weight": float(signals["gated_sector_weight"].min()),
            }
        ]
    )


def predictive_diagnostics(
    equity_returns: pd.DataFrame,
    ticker_sector_map: pd.DataFrame,
    signals: pd.DataFrame,
) -> pd.DataFrame:
    """Non-parametric monthly sector-return diagnostic for the fixed signal."""

    returns = portfolios.clean_return_matrix(equity_returns)
    sectors = sorted(ticker_sector_map["sector"].astype(str).unique())
    mapping = ticker_sector_map.copy()
    mapping["ticker"] = mapping["ticker"].astype(str)
    mapping["sector"] = mapping["sector"].astype(str)
    sector_returns = pd.DataFrame(index=returns.index)
    for sector in sectors:
        tickers = mapping.loc[mapping["sector"].eq(sector), "ticker"].tolist()
        sector_returns[sector] = returns[tickers].mean(axis=1)

    rebalances = pd.DatetimeIndex(sorted(signals["rebalance_date"].unique()))
    rows: list[dict[str, object]] = []
    for i, date in enumerate(rebalances):
        next_date = rebalances[i + 1] if i + 1 < len(rebalances) else returns.index.max() + pd.Timedelta(days=1)
        period = sector_returns.loc[(sector_returns.index >= date) & (sector_returns.index < next_date)]
        if period.empty:
            continue
        period_return = (1.0 + period).prod(axis=0) - 1.0
        signal_slice = signals.loc[signals["rebalance_date"].eq(date)]
        for sector in sectors:
            signal_row = signal_slice.loc[signal_slice["sector"].eq(sector)].iloc[0]
            if pd.notna(signal_row["sentiment_zscore"]):
                rows.append(
                    {
                        "rebalance_date": date,
                        "sector": sector,
                        "sentiment_zscore": float(signal_row["sentiment_zscore"]),
                        "coverage_quality": float(signal_row["coverage_quality"]),
                        "next_period_sector_return": float(period_return[sector]),
                    }
                )
    panel = pd.DataFrame(rows)
    if panel.empty:
        return pd.DataFrame(columns=["sample", "pooled_spearman", "average_cross_sectional_spearman", "valid_monthly_observations", "valid_pair_observations", "median_coverage_quality"])
    median_q = float(panel["coverage_quality"].median())
    samples = {
        "all_valid": panel,
        "above_median_coverage_quality": panel.loc[panel["coverage_quality"].gt(median_q)],
        "at_or_below_median_coverage_quality": panel.loc[panel["coverage_quality"].le(median_q)],
    }
    out = []
    for name, sample in samples.items():
        monthly_corr = (
            sample.groupby("rebalance_date", observed=True)
            .apply(lambda group: group["sentiment_zscore"].corr(group["next_period_sector_return"], method="spearman") if len(group) >= 2 else np.nan)
            .dropna()
        )
        out.append(
            {
                "sample": name,
                "pooled_spearman": float(sample["sentiment_zscore"].corr(sample["next_period_sector_return"], method="spearman")) if len(sample) >= 2 else np.nan,
                "average_cross_sectional_spearman": float(monthly_corr.mean()) if not monthly_corr.empty else np.nan,
                "valid_monthly_observations": int(monthly_corr.count()),
                "valid_pair_observations": len(sample),
                "median_coverage_quality": median_q,
            }
        )
    return pd.DataFrame(out)


def apply_sentiment(weights: pd.DataFrame, sentiment: pd.DataFrame):
    """Backward-compatible wrapper returning rebalance signal diagnostics."""

    if "rebalance_date" not in weights.columns:
        raise ValueError("weights require rebalance_date")
    sectors = sorted(sentiment["sector"].dropna().astype(str).unique())
    coverage = sentiment.rename(columns={"date": "trading_date"}).copy()
    coverage["rolling_21d_covered_tickers"] = coverage["covered_tickers"]
    coverage["rolling_21d_breadth"] = coverage["breadth"]
    return build_rebalance_signals(
        sentiment,
        coverage,
        pd.DatetimeIndex(pd.to_datetime(weights["rebalance_date"].drop_duplicates())),
        sectors,
    )


def validate_rebalance_signals(signals: pd.DataFrame) -> None:
    """Validate formulas, timing fields, and sector-weight totals."""

    required = {
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
    }
    _require_columns(signals, required, "fusion rebalance signals")
    if signals.duplicated(["rebalance_date", "sector"]).any():
        raise ValueError("duplicate rebalance-date sector signals")
    if not signals["coverage_quality"].between(0, 1).all():
        raise ValueError("coverage quality must lie in [0, 1]")
    valid_z = signals["sentiment_zscore"].dropna()
    if not valid_z.between(-2, 2).all():
        raise ValueError("z-scores must be clipped to [-2, 2]")
    for column in ["naive_sector_weight", "gated_sector_weight"]:
        sums = signals.groupby("rebalance_date", observed=True)[column].sum()
        if not np.allclose(sums.to_numpy(dtype=float), 1.0, atol=1e-10):
            raise ValueError(f"{column} does not sum to one by rebalance")
        if (signals[column] < -1e-12).any():
            raise ValueError(f"{column} contains negative weights")


def _prepare_sentiment(sector_sentiment: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        sector_sentiment,
        {"date", "sector", "vader_compound_21d_trailing_lag1"},
        "sector sentiment",
    )
    frame = sector_sentiment.copy()
    frame["rebalance_date"] = _normalise_datetime(frame["date"])
    frame["sector"] = frame["sector"].astype(str)
    frame["sentiment_signal"] = pd.to_numeric(
        frame["vader_compound_21d_trailing_lag1"],
        errors="coerce",
    )
    return frame[["rebalance_date", "sector", "sentiment_signal"]]


def _prepare_lagged_coverage(coverage_daily: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        coverage_daily,
        {"trading_date", "sector", "rolling_21d_covered_tickers", "rolling_21d_breadth"},
        "daily coverage",
    )
    frame = coverage_daily.copy()
    frame["trading_date"] = _normalise_datetime(frame["trading_date"])
    frame["sector"] = frame["sector"].astype(str)
    pieces = []
    for _, group in frame.sort_values(["sector", "trading_date"]).groupby("sector", observed=True):
        group = group.sort_values("trading_date", kind="stable").copy()
        group["coverage_share_21d_lag1"] = (
            pd.to_numeric(group["rolling_21d_covered_tickers"], errors="coerce").shift(1)
            / STOCKS_PER_SECTOR
        )
        group["breadth_21d_lag1"] = pd.to_numeric(group["rolling_21d_breadth"], errors="coerce").shift(1)
        pieces.append(group)
    out = pd.concat(pieces, ignore_index=True)
    out = out.rename(columns={"trading_date": "rebalance_date"})
    return out[["rebalance_date", "sector", "coverage_share_21d_lag1", "breadth_21d_lag1"]]


def _add_cross_sectional_zscores(signals: pd.DataFrame) -> pd.DataFrame:
    pieces = []
    for _, group in signals.groupby("rebalance_date", observed=True, sort=True):
        group = group.copy()
        valid = group["sentiment_signal"].notna()
        group["sentiment_zscore"] = np.nan
        if valid.sum() >= 2:
            values = group.loc[valid, "sentiment_signal"].astype(float)
            std = float(values.std(ddof=0))
            if np.isfinite(std) and std > 0:
                z = (values - float(values.mean())) / std
                group.loc[valid, "sentiment_zscore"] = z.clip(-2.0, 2.0)
        pieces.append(group)
    return pd.concat(pieces, ignore_index=True)


def _normalise_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.tz_localize(None).dt.normalize().astype("datetime64[ns]")


def _normalise_weights(weights: np.ndarray) -> np.ndarray:
    weights = np.asarray(weights, dtype=float)
    total = float(weights.sum())
    if not np.isfinite(total) or abs(total) < 1e-14:
        raise ValueError("weights cannot be normalised")
    return weights / total


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")
