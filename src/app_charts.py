"""Matplotlib chart helpers for the lightweight Signal Mosaic app.

All functions are pure presentation helpers over precomputed pandas frames. They
never load raw data or rebuild analytical results.
"""
from __future__ import annotations

from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OFFWHITE = "#f7f3eb"
NAVY = "#17233c"
BURGUNDY = "#9a3f5f"
TEAL = "#2f7f7a"
GOLD = "#b58b2b"
MUTED = "#6b7280"
FAMILY_COLOURS = {"Equity": BURGUNDY, "Crypto": GOLD, "Combined": TEAL}


def _figure(width: float = 8.8, height: float = 4.8):
    fig, ax = plt.subplots(figsize=(width, height), constrained_layout=True)
    fig.patch.set_facecolor(OFFWHITE)
    ax.set_facecolor(OFFWHITE)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(True, alpha=0.25)
    return fig, ax


def _fund_name_map(frame: pd.DataFrame) -> dict[str, str]:
    if {"fund_id", "fund_name"}.issubset(frame.columns):
        return frame.drop_duplicates("fund_id").set_index("fund_id")["fund_name"].to_dict()
    return {}


def growth_chart(fund_returns: pd.DataFrame, fund_ids: Sequence[str], title: str, source: str):
    fig, ax = _figure()
    frame = fund_returns.loc[fund_returns["fund_id"].isin(fund_ids)].copy()
    frame["date"] = pd.to_datetime(frame["date"])
    names = _fund_name_map(frame)
    for fund_id, group in frame.groupby("fund_id", sort=False):
        group = group.sort_values("date")
        ax.plot(group["date"], group["net_wealth"], linewidth=1.7, label=names.get(fund_id, fund_id))
    ax.set_title(title, loc="left", color=NAVY, fontweight="bold")
    ax.set_ylabel("Net growth of $1")
    ax.set_xlabel("Date")
    ax.legend(frameon=False, fontsize=8)
    fig.text(0.01, 0.005, f"Source: {source}", fontsize=7, color=MUTED)
    return fig


def drawdown_chart(fund_returns: pd.DataFrame, fund_ids: Sequence[str], title: str, source: str):
    fig, ax = _figure()
    frame = fund_returns.loc[fund_returns["fund_id"].isin(fund_ids)].copy()
    frame["date"] = pd.to_datetime(frame["date"])
    names = _fund_name_map(frame)
    for fund_id, group in frame.groupby("fund_id", sort=False):
        group = group.sort_values("date")
        ax.plot(group["date"], group["net_drawdown"] * 100.0, linewidth=1.6, label=names.get(fund_id, fund_id))
    ax.axhline(0.0, linewidth=0.8, color=NAVY, alpha=0.45)
    ax.set_title(title, loc="left", color=NAVY, fontweight="bold")
    ax.set_ylabel("Net drawdown (%)")
    ax.set_xlabel("Date")
    ax.legend(frameon=False, fontsize=8)
    fig.text(0.01, 0.005, f"Source: {source}", fontsize=7, color=MUTED)
    return fig


def risk_return_chart(metrics: pd.DataFrame, title: str):
    fig, ax = _figure()
    for family, group in metrics.groupby("asset_family", sort=False):
        ax.scatter(
            group["annualised_volatility_net"] * 100.0,
            group["annualised_return_net"] * 100.0,
            s=55,
            label=family,
            color=FAMILY_COLOURS.get(str(family), None),
            edgecolor="white",
            linewidth=0.6,
        )
        for _, row in group.iterrows():
            ax.annotate(
                str(row["fund_name"]),
                (row["annualised_volatility_net"] * 100.0, row["annualised_return_net"] * 100.0),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=7,
            )
    ax.set_title(title, loc="left", color=NAVY, fontweight="bold")
    ax.set_xlabel("Net annualised volatility (%)")
    ax.set_ylabel("Net annualised return (%)")
    ax.legend(frameon=False, fontsize=8)
    return fig


def metric_bar_chart(metrics: pd.DataFrame, metric: str, title: str, ylabel: str, percent: bool = False):
    fig, ax = _figure(height=max(3.8, 0.42 * len(metrics) + 1.5))
    frame = metrics.sort_values(metric).copy()
    values = pd.to_numeric(frame[metric], errors="coerce")
    plotted = values * 100.0 if percent else values
    colours = [FAMILY_COLOURS.get(str(family), TEAL) for family in frame["asset_family"]]
    ax.barh(frame["fund_name"], plotted, color=colours, alpha=0.88)
    ax.set_title(title, loc="left", color=NAVY, fontweight="bold")
    ax.set_xlabel(ylabel + (" (%)" if percent else ""))
    ax.grid(axis="x", alpha=0.25)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", labelsize=8)
    return fig


def holdings_chart(holdings: pd.DataFrame, title: str, top_n: int = 15):
    fig, ax = _figure(height=5.0)
    frame = holdings.loc[holdings["target_weight"].gt(1e-12)].nlargest(top_n, "target_weight").sort_values("target_weight")
    ax.barh(frame["asset"], frame["target_weight"] * 100.0, color=TEAL, alpha=0.9)
    ax.set_title(title, loc="left", color=NAVY, fontweight="bold")
    ax.set_xlabel("Target weight (%)")
    ax.grid(axis="x", alpha=0.25)
    ax.grid(axis="y", visible=False)
    return fig


def correlation_heatmap(correlation: pd.DataFrame, title: str):
    fig, ax = _figure(width=7.2, height=5.8)
    values = correlation.to_numpy(dtype=float)
    image = ax.imshow(values, vmin=-1.0, vmax=1.0, cmap="RdBu_r")
    ax.set_xticks(np.arange(len(correlation.columns)), labels=correlation.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(np.arange(len(correlation.index)), labels=correlation.index, fontsize=8)
    ax.set_title(title, loc="left", color=NAVY, fontweight="bold")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Correlation")
    return fig


def sentiment_chart(frame: pd.DataFrame, sectors: Sequence[str], field: str, title: str):
    fig, ax = _figure()
    data = frame.loc[frame["sector"].isin(sectors)].copy()
    data["date"] = pd.to_datetime(data["date"])
    for sector, group in data.groupby("sector", sort=False):
        group = group.sort_values("date")
        ax.plot(group["date"], group[field], linewidth=1.4, label=sector)
    ax.axhline(0.0, color=NAVY, linewidth=0.8, alpha=0.55)
    ax.set_title(title, loc="left", color=NAVY, fontweight="bold")
    ax.set_ylabel("VADER compound")
    ax.set_xlabel("Date")
    ax.legend(frameon=False, fontsize=8, ncol=2)
    return fig


def coverage_chart(frame: pd.DataFrame, sectors: Sequence[str], title: str):
    data = frame.loc[frame["sector"].isin(sectors)].copy()
    data["date"] = pd.to_datetime(data["date"])
    fig, axes = plt.subplots(2, 1, figsize=(8.8, 6.4), sharex=True, constrained_layout=True)
    fig.patch.set_facecolor(OFFWHITE)
    for ax in axes:
        ax.set_facecolor(OFFWHITE)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.grid(True, alpha=0.25)
    for sector, group in data.groupby("sector", sort=False):
        group = group.sort_values("date")
        axes[0].plot(group["date"], group["coverage_share"], linewidth=1.25, label=sector)
        axes[1].plot(group["date"], group["breadth"], linewidth=1.25, label=sector)
    axes[0].set_title(title, loc="left", color=NAVY, fontweight="bold")
    axes[0].set_ylabel("Coverage share")
    axes[1].set_ylabel("Breadth")
    axes[1].set_xlabel("Date")
    axes[0].legend(frameon=False, fontsize=8, ncol=2)
    return fig


def active_weight_chart(signals: pd.DataFrame, title: str):
    fig, axes = plt.subplots(2, 1, figsize=(9.0, 7.0), sharex=True, constrained_layout=True)
    fig.patch.set_facecolor(OFFWHITE)
    frame = signals.copy()
    frame["rebalance_date"] = pd.to_datetime(frame["rebalance_date"])
    for ax, column, subtitle in [
        (axes[0], "naive_sector_weight", "Naive active sector weights"),
        (axes[1], "gated_sector_weight", "Coverage-gated active sector weights"),
    ]:
        ax.set_facecolor(OFFWHITE)
        for sector, group in frame.groupby("sector", sort=False):
            group = group.sort_values("rebalance_date")
            ax.plot(group["rebalance_date"], (group[column] - 0.10) * 100.0, linewidth=1.0, label=sector)
        ax.axhline(0.0, color=NAVY, linewidth=0.8)
        ax.set_ylabel("Active weight (pp)")
        ax.set_title(subtitle, loc="left", fontsize=10)
        ax.grid(True, alpha=0.25)
    axes[0].legend(frameon=False, ncol=5, fontsize=7)
    axes[1].set_xlabel("Rebalance date")
    fig.suptitle(title, x=0.01, ha="left", color=NAVY, fontweight="bold")
    return fig


def attenuation_chart(signals: pd.DataFrame, title: str):
    fig, ax = _figure()
    naive = (signals["naive_sector_weight"] - signals["base_sector_weight"]).abs()
    gated = (signals["gated_sector_weight"] - signals["base_sector_weight"]).abs()
    ax.scatter(signals["coverage_quality"], (naive - gated) * 100.0, s=18, alpha=0.55, color=TEAL)
    ax.axhline(0.0, color=NAVY, linewidth=0.8)
    ax.set_title(title, loc="left", color=NAVY, fontweight="bold")
    ax.set_xlabel("Coverage quality")
    ax.set_ylabel("Tilt attenuation (percentage points)")
    return fig
