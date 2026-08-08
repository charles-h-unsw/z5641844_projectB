"""Build the nine base out-of-sample funds and their app/report artifacts."""
from __future__ import annotations

import pathlib
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import etl, features, portfolios  # noqa: E402

DATA = ROOT / "results" / "data"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
OFFWHITE = "#f7f3eb"
NAVY = "#17233c"
TEAL = "#2f7f7a"
BURGUNDY = "#9a3f5f"
GOLD = "#b58b2b"


def _write_csv(frame: pd.DataFrame, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, float_format="%.12g")


def _style_axes(ax) -> None:
    ax.set_facecolor(OFFWHITE)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(True, alpha=0.25)


def _metadata(
    equity_returns: pd.DataFrame,
    crypto_returns: pd.DataFrame,
    combined_returns: pd.DataFrame,
    sector_map: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    eq = sector_map.rename(columns={"ticker": "asset"}).copy()
    eq["asset"] = eq["asset"].astype(str)
    eq["asset_class"] = "Equity"
    eq = eq[["asset", "asset_class", "sector"]]

    cr = pd.DataFrame(
        {
            "asset": crypto_returns.columns.astype(str),
            "asset_class": "Crypto",
            "sector": pd.NA,
        }
    )

    combined_rows: list[dict[str, object]] = []
    sector_lookup = sector_map.set_index("ticker")["sector"].to_dict()
    for asset in combined_returns.columns.astype(str):
        if asset.startswith("EQ_"):
            ticker = asset.removeprefix("EQ_")
            combined_rows.append(
                {
                    "asset": asset,
                    "asset_class": "Equity",
                    "sector": sector_lookup[ticker],
                }
            )
        elif asset.startswith("CR_"):
            combined_rows.append(
                {"asset": asset, "asset_class": "Crypto", "sector": pd.NA}
            )
        else:
            raise ValueError(f"unexpected combined asset name: {asset}")
    combined = pd.DataFrame(combined_rows)
    return {"Equity": eq, "Crypto": cr, "Combined": combined}


def _growth_figure(fund_returns: pd.DataFrame) -> None:
    families = ["Equity", "Crypto", "Combined"]
    fig, axes = plt.subplots(3, 1, figsize=(10.5, 11.0), constrained_layout=True)
    fig.patch.set_facecolor(OFFWHITE)
    for ax, family in zip(axes, families, strict=True):
        _style_axes(ax)
        subset = fund_returns.loc[fund_returns["asset_family"].eq(family)]
        for _, group in subset.groupby("method", sort=False):
            group = group.sort_values("date")
            ax.plot(pd.to_datetime(group["date"]), group["net_wealth"], label=group["method"].iloc[0], linewidth=1.5)
        ax.set_title(f"{family}: net growth of $1 from first 2021 rebalance", loc="left", fontsize=10)
        ax.set_ylabel("Net wealth ($)")
        ax.legend(frameon=False, ncol=3, fontsize=8)
    axes[-1].set_xlabel("Date")
    fig.suptitle("Net fund growth varies by universe and optimisation method", x=0.01, ha="left", color=NAVY, fontweight="bold")
    fig.text(0.01, 0.003, "Source: Project B fund backtests; sample 2021-01-01 to 2023-12-31; net of 10 bps turnover cost.", fontsize=7)
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / "fund_growth_of_one_by_family.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def _drawdown_figure(fund_returns: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10.0, 5.6), constrained_layout=True)
    fig.patch.set_facecolor(OFFWHITE)
    _style_axes(ax)
    subset = fund_returns.loc[fund_returns["asset_family"].eq("Combined")]
    for _, group in subset.groupby("method", sort=False):
        group = group.sort_values("date")
        ax.plot(pd.to_datetime(group["date"]), group["net_drawdown"] * 100.0, label=group["method"].iloc[0], linewidth=1.5)
    ax.set_title("Combined funds: net drawdowns remain below prior wealth peaks", loc="left", color=NAVY, fontweight="bold")
    ax.set_ylabel("Net drawdown (%)")
    ax.set_xlabel("Date")
    ax.legend(frameon=False)
    fig.text(0.01, 0.003, "Source: Project B fund backtests; sample 2021-01-04 to 2023-12-29.", fontsize=7)
    fig.savefig(FIGURES / "fund_drawdowns_combined.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def _risk_return_figure(metrics: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.0, 5.5), constrained_layout=True)
    fig.patch.set_facecolor(OFFWHITE)
    _style_axes(ax)
    colours = {"Equity": BURGUNDY, "Crypto": GOLD, "Combined": TEAL}
    for family, group in metrics.groupby("asset_family", sort=False):
        ax.scatter(
            group["annualised_volatility_net"] * 100.0,
            group["annualised_return_net"] * 100.0,
            s=60,
            color=colours.get(str(family)),
            label=family,
            edgecolor="white",
            linewidth=0.6,
        )
        for _, row in group.iterrows():
            short = str(row["fund_name"]).replace("Minimum Variance", "Min Var").replace("Risk Parity", "RP").replace("Equal Weight", "EW")
            ax.annotate(short, (row["annualised_volatility_net"] * 100.0, row["annualised_return_net"] * 100.0), xytext=(4, 4), textcoords="offset points", fontsize=7)
    ax.set_title("Net risk-return profile across the nine base funds", loc="left", color=NAVY, fontweight="bold")
    ax.set_xlabel("Net annualised volatility (%)")
    ax.set_ylabel("Net annualised return (%)")
    ax.legend(frameon=False)
    fig.text(0.01, 0.003, "Source: Project B fund metrics; sample 2021-01-01 to 2023-12-31; Sharpe assumes rf = 0.", fontsize=7)
    fig.savefig(FIGURES / "fund_risk_return_comparison.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def _weights_figure(fund_weights: pd.DataFrame) -> None:
    combined = fund_weights.loc[fund_weights["asset_family"].eq("Combined")].copy()
    grouped = (
        combined.groupby(["method", "rebalance_date", "asset_class"], observed=True)["target_weight"]
        .sum()
        .reset_index()
    )
    methods = [portfolios.METHOD_EQUAL_WEIGHT, portfolios.METHOD_MIN_VARIANCE, portfolios.METHOD_RISK_PARITY]
    fig, axes = plt.subplots(3, 1, figsize=(10.0, 9.0), sharex=True, constrained_layout=True)
    fig.patch.set_facecolor(OFFWHITE)
    for ax, method in zip(axes, methods, strict=True):
        _style_axes(ax)
        pivot = grouped.loc[grouped["method"].eq(method)].pivot(index="rebalance_date", columns="asset_class", values="target_weight").fillna(0.0)
        dates = pd.to_datetime(pivot.index)
        crypto = pivot.get("Crypto", pd.Series(0.0, index=pivot.index)).to_numpy()
        equity = pivot.get("Equity", pd.Series(0.0, index=pivot.index)).to_numpy()
        ax.stackplot(dates, crypto, equity, labels=["Crypto", "Equity"], colors=["#9a7ac0", "#3d8cbe"], alpha=0.95)
        ax.set_ylim(0, 1)
        ax.set_ylabel("Weight")
        ax.set_title(f"{method}: combined target weights by asset class", loc="left", fontsize=10)
        ax.legend(frameon=False, ncol=2, fontsize=8, loc="upper left")
    axes[-1].set_xlabel("Rebalance date")
    fig.suptitle("Combined fund allocations show the equity-crypto mix at each rebalance", x=0.01, ha="left", color=NAVY, fontweight="bold")
    fig.text(0.01, 0.003, "Source: Project B target weights; detailed asset weights are in fund_weights.csv.", fontsize=7)
    fig.savefig(FIGURES / "fund_weights_over_time_combined.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    equities = etl.load_clean_equities()
    crypto = etl.load_clean_crypto()
    sector_map = etl.ticker_sector_map(equities)
    equity_returns = features.daily_returns(equities)
    crypto_returns = features.daily_returns(crypto)
    combined_returns = features.combined_returns_on_equity_calendar(equity_returns, crypto_returns)

    universes = {"Equity": equity_returns, "Crypto": crypto_returns, "Combined": combined_returns}
    metadata = _metadata(equity_returns, crypto_returns, combined_returns, sector_map)
    suite = portfolios.build_fund_suite(universes, metadata)

    _write_csv(suite["fund_returns"], DATA / "fund_returns.csv")
    _write_csv(suite["fund_weights"], DATA / "fund_weights.csv")
    _write_csv(suite["performance_metrics"], TABLES / "performance_metrics.csv")
    _write_csv(suite["fund_backtest_design"], TABLES / "fund_backtest_design.csv")
    _write_csv(suite["fund_optimizer_diagnostics"], TABLES / "fund_optimizer_diagnostics.csv")
    _write_csv(suite["fund_latest_holdings"], TABLES / "fund_latest_holdings.csv")
    _write_csv(suite["fund_fact_sheet_summary"], TABLES / "fund_fact_sheet_summary.csv")

    _growth_figure(suite["fund_returns"])
    _drawdown_figure(suite["fund_returns"])
    _risk_return_figure(suite["performance_metrics"])
    _weights_figure(suite["fund_weights"])

    diagnostics = suite["fund_optimizer_diagnostics"]
    if not diagnostics["solver_success"].all():
        raise SystemExit("one or more fund optimisers failed")
    if not np.allclose(diagnostics["weight_sum"], 1.0, atol=1e-8):
        raise SystemExit("fund weights do not sum to one")
    if diagnostics["maximum_weight"].max() > portfolios.MAX_TARGET_WEIGHT + 1e-8:
        raise SystemExit("optimised maximum weight exceeded the 20% cap")

    print("built nine base funds")
    print(suite["performance_metrics"][["fund_name", "annualised_return_net", "annualised_volatility_net", "Sharpe_net", "maximum_drawdown_net"]].to_string(index=False))
    print(f"fund_returns rows: {len(suite['fund_returns'])}")
    print(f"fund_weights rows: {len(suite['fund_weights'])}")
    print(f"optimizer diagnostics rows: {len(diagnostics)}; failures: {(~diagnostics['solver_success']).sum()}")


if __name__ == "__main__":
    main()
