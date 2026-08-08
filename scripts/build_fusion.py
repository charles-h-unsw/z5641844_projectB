"""Build the two equity sentiment-overlay funds and append them idempotently."""
from __future__ import annotations

import hashlib
import pathlib
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import etl, features, fusion, portfolios  # noqa: E402

DATA = ROOT / "results" / "data"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
OFFWHITE = "#f7f3eb"
NAVY = "#17233c"
BURGUNDY = "#9a3f5f"
TEAL = "#2f7f7a"
GOLD = "#b58b2b"
FUSION_IDS = {"equity_sentiment_naive", "equity_sentiment_coverage_gated"}
BASE_IDS = {spec.fund_id for spec in portfolios.fund_specs()}


def _write_csv(frame: pd.DataFrame, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, float_format="%.12g")


def _frame_hash(frame: pd.DataFrame, sort_cols: list[str]) -> str:
    ordered = frame.sort_values(sort_cols, kind="stable").reset_index(drop=True)
    payload = ordered.to_csv(index=False, float_format="%.12g", lineterminator="\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _style_axes(ax) -> None:
    ax.set_facecolor(OFFWHITE)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(True, alpha=0.25)


def _growth_figure(returns: pd.DataFrame) -> None:
    ids = ["equity_equal_weight", "equity_sentiment_naive", "equity_sentiment_coverage_gated"]
    fig, ax = plt.subplots(figsize=(9.5, 5.4), constrained_layout=True)
    fig.patch.set_facecolor(OFFWHITE)
    _style_axes(ax)
    colours = {ids[0]: "#2f7fbd", ids[1]: BURGUNDY, ids[2]: TEAL}
    for fund_id in ids:
        group = returns.loc[returns["fund_id"].eq(fund_id)].sort_values("date")
        ax.plot(pd.to_datetime(group["date"]), group["net_wealth"], linewidth=1.5, color=colours[fund_id], label=group["fund_name"].iloc[0])
    ax.set_title("Equity sentiment tilts are evaluated against equal weight", loc="left", color=NAVY, fontweight="bold")
    ax.set_ylabel("Net growth of $1")
    ax.set_xlabel("Date")
    ax.legend(frameon=False, fontsize=8)
    fig.text(0.01, 0.003, "Source: Project B equity backtests; sample 2021-01-04 to 2023-12-29; net of 10 bps turnover cost.", fontsize=7)
    fig.savefig(FIGURES / "fusion_growth_of_one.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def _metrics_figure(before_after: pd.DataFrame) -> None:
    metrics = [
        ("annualised_return_net", "Net annualised return (%)", 100.0),
        ("annualised_volatility_net", "Net volatility (%)", 100.0),
        ("Sharpe_net", "Net Sharpe", 1.0),
        ("maximum_drawdown_net", "Maximum drawdown (%)", 100.0),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(10.0, 7.2), constrained_layout=True)
    fig.patch.set_facecolor(OFFWHITE)
    for ax, (column, title, scale) in zip(axes.flat, metrics, strict=True):
        _style_axes(ax)
        values = before_after[column].to_numpy(dtype=float) * scale
        ax.bar(before_after["fund_name"], values, color=["#2f7fbd", BURGUNDY, TEAL])
        ax.set_title(title, loc="left", fontsize=9)
        ax.tick_params(axis="x", rotation=20, labelsize=7)
        ax.grid(axis="x", visible=False)
    fig.suptitle("Sentiment overlays change risk and return only modestly", x=0.01, ha="left", color=NAVY, fontweight="bold")
    fig.savefig(FIGURES / "fusion_before_after_metrics.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def _active_weights_figure(signals: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(10.0, 7.2), sharex=True, constrained_layout=True)
    fig.patch.set_facecolor(OFFWHITE)
    for ax, column, title in [
        (axes[0], "naive_sector_weight", "Naive sentiment active sector weights"),
        (axes[1], "gated_sector_weight", "Coverage-gated active sector weights"),
    ]:
        _style_axes(ax)
        for sector, group in signals.groupby("sector", sort=False):
            group = group.sort_values("rebalance_date")
            ax.plot(pd.to_datetime(group["rebalance_date"]), (group[column] - 0.10) * 100.0, linewidth=1.0, label=sector)
        ax.axhline(0.0, color=NAVY, linewidth=0.7)
        ax.set_title(title, loc="left", fontsize=9)
        ax.set_ylabel("Active weight (pp)")
    axes[0].legend(frameon=False, ncol=5, fontsize=7)
    axes[-1].set_xlabel("Rebalance date")
    fig.suptitle("Coverage quality attenuates active sector tilts", x=0.01, ha="left", color=NAVY, fontweight="bold")
    fig.savefig(FIGURES / "fusion_sector_active_weights.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def _attenuation_figure(signals: pd.DataFrame) -> None:
    naive = (signals["naive_sector_weight"] - signals["base_sector_weight"]).abs()
    gated = (signals["gated_sector_weight"] - signals["base_sector_weight"]).abs()
    fig, ax = plt.subplots(figsize=(8.5, 5.0), constrained_layout=True)
    fig.patch.set_facecolor(OFFWHITE)
    _style_axes(ax)
    ax.scatter(signals["coverage_quality"], (naive - gated) * 100.0, s=18, alpha=0.55, color=TEAL)
    ax.axhline(0.0, color=NAVY, linewidth=0.7)
    ax.set_title("The coverage gate reduces the size of most active tilts", loc="left", color=NAVY, fontweight="bold")
    ax.set_xlabel("Coverage quality")
    ax.set_ylabel("Naive minus gated absolute tilt (pp)")
    fig.text(0.01, 0.003, "Coverage is an evidence-breadth control, not proof of predictability.", fontsize=7)
    fig.savefig(FIGURES / "fusion_coverage_attenuation.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    required = [
        DATA / "fund_returns.csv",
        DATA / "fund_weights.csv",
        DATA / "sector_sentiment_index.csv",
        TABLES / "performance_metrics.csv",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise SystemExit(f"build base funds and sentiment first; missing: {missing}")

    base_returns_all = pd.read_csv(DATA / "fund_returns.csv", parse_dates=["date"])
    base_weights_all = pd.read_csv(DATA / "fund_weights.csv", parse_dates=["rebalance_date"])
    base_metrics_all = pd.read_csv(TABLES / "performance_metrics.csv", parse_dates=["first_live_date", "end_date"])
    # Idempotent reruns: strip any prior fusion rows and rebuild them from source artifacts.
    base_returns = base_returns_all.loc[~base_returns_all["fund_id"].isin(FUSION_IDS)].copy()
    base_weights = base_weights_all.loc[~base_weights_all["fund_id"].isin(FUSION_IDS)].copy()
    base_metrics = base_metrics_all.loc[~base_metrics_all["fund_id"].isin(FUSION_IDS)].copy()
    if set(base_metrics["fund_id"]) != BASE_IDS:
        raise SystemExit("base fund artifacts do not contain the exact nine required fund IDs")

    before_hashes = {
        "fund_returns": _frame_hash(base_returns, ["date", "fund_id"]),
        "fund_weights": _frame_hash(base_weights, ["rebalance_date", "fund_id", "asset"]),
        "performance_metrics": _frame_hash(base_metrics, ["fund_id"]),
    }

    equities = etl.load_clean_equities()
    sector_map = etl.ticker_sector_map(equities)
    equity_returns = features.daily_returns(equities)
    coverage = pd.read_csv(DATA / "sector_coverage_daily.csv", parse_dates=["trading_date"])
    sentiment_index = pd.read_csv(DATA / "sector_sentiment_index.csv", parse_dates=["date", "signal_source_date"])
    rebalance_dates = pd.DatetimeIndex(
        sorted(
            base_weights.loc[base_weights["fund_id"].eq("equity_equal_weight"), "rebalance_date"].unique()
        )
    )

    built = fusion.build_fusion_funds(
        equity_returns,
        sector_map,
        sentiment_index,
        coverage,
        rebalance_dates,
    )
    final_returns = pd.concat([base_returns, built["fund_returns"]], ignore_index=True)
    final_weights = pd.concat([base_weights, built["fund_weights"]], ignore_index=True)
    final_metrics = pd.concat([base_metrics, built["performance_metrics"]], ignore_index=True)

    if final_returns.duplicated(["date", "fund_id"]).any():
        raise SystemExit("duplicate date-fund rows after fusion append")
    if final_weights.duplicated(["rebalance_date", "fund_id", "asset"]).any():
        raise SystemExit("duplicate rebalance-fund-asset rows after fusion append")
    if final_metrics["fund_id"].nunique() != 11 or len(final_metrics) != 11:
        raise SystemExit("final metric artifact must contain exactly eleven funds")

    after_hashes = {
        "fund_returns": _frame_hash(final_returns.loc[final_returns["fund_id"].isin(BASE_IDS)], ["date", "fund_id"]),
        "fund_weights": _frame_hash(final_weights.loc[final_weights["fund_id"].isin(BASE_IDS)], ["rebalance_date", "fund_id", "asset"]),
        "performance_metrics": _frame_hash(final_metrics.loc[final_metrics["fund_id"].isin(BASE_IDS)], ["fund_id"]),
    }
    if before_hashes != after_hashes:
        raise SystemExit("original nine base fund records changed during fusion build")

    before_after = fusion.fusion_before_after(final_metrics)
    signal_diag = fusion.fusion_signal_diagnostics(built["fusion_rebalance_signals"])
    predictive = fusion.predictive_diagnostics(
        equity_returns,
        sector_map,
        built["fusion_rebalance_signals"],
    )
    latest = portfolios.latest_holdings(final_weights)
    fact_sheet = portfolios.make_fact_sheet_summary(final_metrics)
    fusion_latest = latest.loc[latest["fund_id"].isin(fusion.COMPARISON_FUND_IDS)].copy()
    integrity = pd.DataFrame(
        [
            {"artifact": key, "before_sha256": before_hashes[key], "after_sha256": after_hashes[key], "status": "PASS" if before_hashes[key] == after_hashes[key] else "FAIL"}
            for key in before_hashes
        ]
    )

    _write_csv(final_returns, DATA / "fund_returns.csv")
    _write_csv(final_weights, DATA / "fund_weights.csv")
    _write_csv(built["fusion_rebalance_signals"], DATA / "fusion_rebalance_signals.csv")
    _write_csv(final_metrics, TABLES / "performance_metrics.csv")
    _write_csv(before_after, TABLES / "fusion_before_after.csv")
    _write_csv(signal_diag, TABLES / "fusion_signal_diagnostics.csv")
    _write_csv(predictive, TABLES / "fusion_predictive_diagnostics.csv")
    _write_csv(latest, TABLES / "fund_latest_holdings.csv")
    _write_csv(fact_sheet, TABLES / "fund_fact_sheet_summary.csv")
    _write_csv(fusion_latest, TABLES / "fusion_latest_holdings.csv")
    _write_csv(integrity, TABLES / "fusion_base_integrity.csv")

    _growth_figure(final_returns)
    _metrics_figure(before_after)
    _active_weights_figure(built["fusion_rebalance_signals"])
    _attenuation_figure(built["fusion_rebalance_signals"])

    print(f"final fund count: {final_metrics['fund_id'].nunique()}")
    print(f"fund_returns rows: {len(final_returns)}")
    print(f"fund_weights rows: {len(final_weights)}")
    print(f"fusion signal rows: {len(built['fusion_rebalance_signals'])}")
    print(before_after[["fund_name", "annualised_return_net", "annualised_volatility_net", "Sharpe_net", "maximum_drawdown_net"]].to_string(index=False))
    print(predictive.to_string(index=False))
    print("original nine base funds unchanged: PASS")


if __name__ == "__main__":
    main()
