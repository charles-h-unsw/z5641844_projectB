"""Pure app-side calculations for Signal Mosaic."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd


class AllocationError(ValueError):
    """Raised when an illustrative allocation is not well defined."""


def format_percent(value: float | int | None, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value) * 100:.{digits}f}%"


def format_number(value: float | int | None, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def compact_month_range(start: pd.Timestamp, end: pd.Timestamp) -> str:
    """Format a dynamic date span for compact KPI cards."""
    start_ts = pd.to_datetime(start)
    end_ts = pd.to_datetime(end)
    return f"{start_ts.strftime('%b %Y')} to {end_ts.strftime('%b %Y')}"


def normalise_weights(weights: Mapping[str, float]) -> pd.Series:
    """Normalise non-negative user weights to sum to one."""
    series = pd.Series(weights, dtype=float)
    if series.empty:
        raise AllocationError("Select at least one fund.")
    if series.isna().any() or np.isinf(series.to_numpy()).any():
        raise AllocationError("Allocation weights must be finite numbers.")
    if (series < 0).any():
        raise AllocationError("Allocation weights cannot be negative.")
    total = float(series.sum())
    if total <= 0:
        raise AllocationError("At least one allocation weight must be above zero.")
    return series / total


def monthly_fund_returns(
    fund_returns: pd.DataFrame,
    fund_ids: Sequence[str],
    return_column: str = "net_return",
) -> pd.DataFrame:
    """Compound daily precomputed fund returns to common monthly returns."""
    if len(fund_ids) < 1:
        raise AllocationError("Select at least one fund.")
    required = {"date", "fund_id", return_column}
    missing = required.difference(fund_returns.columns)
    if missing:
        raise AllocationError(f"Fund returns are missing columns: {sorted(missing)}")

    returns = fund_returns.loc[fund_returns["fund_id"].isin(fund_ids), ["date", "fund_id", return_column]].copy()
    returns["date"] = pd.to_datetime(returns["date"])
    returns["month"] = returns["date"].dt.to_period("M").dt.to_timestamp("M")
    monthly = (
        returns.groupby(["month", "fund_id"], observed=True)[return_column]
        .apply(lambda values: float(np.prod(1.0 + values.to_numpy(dtype=float)) - 1.0))
        .unstack("fund_id")
        .sort_index()
    )
    monthly = monthly.reindex(columns=list(fund_ids))
    return monthly.dropna(how="any")


def allocation_return_history(
    monthly_returns: pd.DataFrame,
    weights: Mapping[str, float],
) -> pd.DataFrame:
    """Build monthly rebalanced fund-of-funds returns from monthly fund returns."""
    if monthly_returns.empty:
        raise AllocationError("Selected funds have no shared monthly sample.")
    norm = normalise_weights(weights)
    missing = set(norm.index).difference(monthly_returns.columns)
    if missing:
        raise AllocationError(f"Monthly return table is missing funds: {sorted(missing)}")

    aligned = monthly_returns.loc[:, norm.index].dropna(how="any")
    if aligned.empty:
        raise AllocationError("Selected funds have no overlapping monthly returns.")

    allocation_return = aligned.mul(norm, axis=1).sum(axis=1)
    wealth = (1.0 + allocation_return).cumprod()
    running_max = wealth.cummax()
    drawdown = wealth / running_max - 1.0
    return pd.DataFrame(
        {
            "month": aligned.index,
            "allocation_return": allocation_return.to_numpy(),
            "wealth": wealth.to_numpy(),
            "drawdown": drawdown.to_numpy(),
        }
    )


def allocation_metrics(history: pd.DataFrame, periods_per_year: int = 12) -> dict[str, float]:
    if history.empty:
        raise AllocationError("Allocation history is empty.")
    returns = history["allocation_return"].astype(float)
    n_obs = len(returns)
    cumulative_return = float(np.prod(1.0 + returns.to_numpy()) - 1.0)
    annualised_return = float((1.0 + cumulative_return) ** (periods_per_year / n_obs) - 1.0)
    volatility = float(returns.std(ddof=1) * np.sqrt(periods_per_year)) if n_obs > 1 else np.nan
    sharpe = float(returns.mean() / returns.std(ddof=1) * np.sqrt(periods_per_year)) if n_obs > 1 and returns.std(ddof=1) > 0 else np.nan
    max_drawdown = float(history["drawdown"].min())
    return {
        "number_of_months": float(n_obs),
        "cumulative_return": cumulative_return,
        "annualised_return": annualised_return,
        "annualised_volatility": volatility,
        "Sharpe": sharpe,
        "maximum_drawdown": max_drawdown,
    }


def calendar_label(asset_family: str) -> str:
    if asset_family == "Crypto":
        return "Native seven-day crypto calendar"
    if asset_family == "Combined":
        return "Equity trading calendar; same-date native crypto returns only"
    return "Equity trading calendar"


def selected_metric_table(metrics: pd.DataFrame, fund_ids: Sequence[str]) -> pd.DataFrame:
    cols = [
        "fund_name",
        "asset_family",
        "method",
        "annualised_return_net",
        "annualised_volatility_net",
        "Sharpe_net",
        "maximum_drawdown_net",
        "cumulative_return_net",
        "average_rebalance_turnover",
    ]
    table = metrics.loc[metrics["fund_id"].isin(fund_ids), ["fund_id", *cols]].copy()
    return table.set_index("fund_id").loc[list(fund_ids)].reset_index()


def latest_holdings_for_fund(holdings: pd.DataFrame, fund_id: str) -> pd.DataFrame:
    result = holdings.loc[holdings["fund_id"] == fund_id].copy()
    if result.empty:
        return result
    return result.sort_values("target_weight", ascending=False).reset_index(drop=True)


def return_history_for_fund(fund_returns: pd.DataFrame, fund_id: str) -> pd.DataFrame:
    result = fund_returns.loc[fund_returns["fund_id"] == fund_id].copy()
    return result.sort_values("date").reset_index(drop=True)


def overview_highlights(metrics: pd.DataFrame, fusion_before_after: pd.DataFrame) -> list[str]:
    highlights: list[str] = []
    if not metrics.empty:
        best_sharpe = metrics.loc[metrics["Sharpe_net"].idxmax()]
        low_vol = metrics.loc[metrics["annualised_volatility_net"].idxmin()]
        highlights.append(
            f"Strongest net Sharpe: {best_sharpe['fund_name']} at {best_sharpe['Sharpe_net']:.2f}."
        )
        highlights.append(
            f"Lowest net volatility: {low_vol['fund_name']} at {low_vol['annualised_volatility_net'] * 100:.1f}% annualised."
        )
        combined = metrics.loc[metrics["asset_family"] == "Combined"]
        if not combined.empty:
            best_combined = combined.loc[combined["Sharpe_net"].idxmax()]
            highlights.append(
                f"Best combined fund by net Sharpe: {best_combined['fund_name']} at {best_combined['Sharpe_net']:.2f}."
            )

    if {"fund_name", "Sharpe_net"}.issubset(fusion_before_after.columns):
        base = fusion_before_after.loc[fusion_before_after["fund_name"] == "Equity Equal Weight"]
        naive = fusion_before_after.loc[fusion_before_after["fund_name"] == "Equity Naive Sentiment Tilt"]
        gated = fusion_before_after.loc[fusion_before_after["fund_name"] == "Equity Coverage-Gated Sentiment Tilt"]
        if not base.empty and not naive.empty and not gated.empty:
            base_s = float(base.iloc[0]["Sharpe_net"])
            naive_s = float(naive.iloc[0]["Sharpe_net"])
            gated_s = float(gated.iloc[0]["Sharpe_net"])
            if base_s >= max(naive_s, gated_s):
                highlights.append(
                    "The current sentiment overlays did not beat Equity Equal Weight on net Sharpe; the coverage gate reduced some damage versus the naive tilt."
                )
            elif gated_s > naive_s:
                highlights.append(
                    "The coverage-gated sentiment overlay had the strongest net Sharpe among the three equity comparison funds."
                )
    return highlights


def fusion_summary(fusion_before_after: pd.DataFrame, predictive: pd.DataFrame) -> list[str]:
    lines: list[str] = []
    base = fusion_before_after.loc[fusion_before_after["fund_name"] == "Equity Equal Weight"]
    naive = fusion_before_after.loc[fusion_before_after["fund_name"] == "Equity Naive Sentiment Tilt"]
    gated = fusion_before_after.loc[fusion_before_after["fund_name"] == "Equity Coverage-Gated Sentiment Tilt"]
    if not base.empty and not naive.empty and not gated.empty:
        b = base.iloc[0]
        n = naive.iloc[0]
        g = gated.iloc[0]
        if float(n["Sharpe_net"]) < float(b["Sharpe_net"]) and float(g["Sharpe_net"]) < float(b["Sharpe_net"]):
            lines.append("Both sentiment tilts reduced net return and net Sharpe versus Equity Equal Weight.")
        if float(g["Sharpe_net"]) > float(n["Sharpe_net"]):
            lines.append("The Coverage-Gated Tilt performed better than the Naive Tilt, but it did not create positive predictive value in this sample.")
    pooled = predictive.loc[predictive["sample"] == "all_valid"] if "sample" in predictive.columns else pd.DataFrame()
    if not pooled.empty and "pooled_spearman" in pooled.columns:
        corr = float(pooled.iloc[0]["pooled_spearman"])
        direction = "negative" if corr < 0 else "positive" if corr > 0 else "near zero"
        lines.append(f"The pooled sentiment-return rank correlation was {direction} ({corr:.3f}); parameters were not retuned after observing it.")
    return lines


def table_to_csv_bytes(table: pd.DataFrame) -> bytes:
    return table.to_csv(index=False).encode("utf-8")
