"""Build the standalone equity-sector plain-VADER sentiment index."""
from __future__ import annotations

import pathlib
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import etl, features, sentiment  # noqa: E402

DATA = ROOT / "results" / "data"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
OFFWHITE = "#f7f3eb"
NAVY = "#17233c"


def _write_csv(frame: pd.DataFrame, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, float_format="%.12g")


def _style_axes(ax) -> None:
    ax.set_facecolor(OFFWHITE)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(True, alpha=0.22)


def _sentiment_timeseries_figure(index: pd.DataFrame) -> None:
    sectors = sorted(index["sector"].unique())
    fig, axes = plt.subplots(5, 2, figsize=(11.0, 12.0), sharex=True, sharey=True, constrained_layout=True)
    fig.patch.set_facecolor(OFFWHITE)
    for ax, sector_name in zip(axes.flat, sectors, strict=True):
        _style_axes(ax)
        group = index.loc[index["sector"].eq(sector_name)].sort_values("date")
        ax.plot(pd.to_datetime(group["date"]), group["vader_compound_21d_trailing"], linewidth=1.0)
        ax.axhline(0.0, color=NAVY, linewidth=0.7, alpha=0.55)
        ax.set_title(sector_name, loc="left", fontsize=8)
        ax.set_ylim(-0.45, 0.45)
    for ax in axes[:, 0]:
        ax.set_ylabel("VADER compound")
    for ax in axes[-1, :]:
        ax.set_xlabel("Headline-aligned date")
    fig.suptitle("Sector sentiment shown as 21-trading-day trailing raw VADER compound", x=0.01, ha="left", color=NAVY, fontweight="bold")
    fig.text(0.01, 0.003, "Source: Project B equity headlines scored with plain NLTK VADER; dates are headline-aligned, not investable dates.", fontsize=7)
    fig.savefig(FIGURES / "sector_sentiment_timeseries.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def _neutrality_figure(scored_headlines: pd.DataFrame) -> None:
    """Plot the share of individually scored headlines classed as neutral by sector."""

    required = {"sector", "vader_category"}
    missing = required.difference(scored_headlines.columns)
    if missing:
        raise ValueError(f"scored_headlines is missing columns: {sorted(missing)}")

    frame = (
        scored_headlines.assign(
            neutral_headline=scored_headlines["vader_category"].eq("neutral")
        )
        .groupby("sector", observed=True, sort=True)["neutral_headline"]
        .mean()
        .rename("neutral_headline_share")
        .reset_index()
        .sort_values("neutral_headline_share", kind="stable")
    )
    fig, ax = plt.subplots(figsize=(9.0, 5.2), constrained_layout=True)
    fig.patch.set_facecolor(OFFWHITE)
    _style_axes(ax)
    ax.barh(frame["sector"], frame["neutral_headline_share"] * 100.0, color="#9a3f5f", alpha=0.85)
    ax.set_title("Plain VADER leaves a large neutral share in finance headlines", loc="left", color=NAVY, fontweight="bold")
    ax.set_xlabel("VADER-neutral headline share (%)")
    ax.grid(axis="x", alpha=0.25)
    ax.grid(axis="y", visible=False)
    fig.text(0.01, 0.003, "Neutral-scored headlines are distinct from missing-news observations.", fontsize=7)
    fig.savefig(FIGURES / "vader_neutrality_by_sector.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def _coverage_context_figure(index: pd.DataFrame) -> None:
    frame = index.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame["month"] = frame["date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        frame.groupby(["month", "sector"], observed=True)
        .agg(sentiment=("vader_compound_raw", "mean"), coverage=("coverage_share", "mean"))
        .reset_index()
    )
    sectors = sorted(monthly["sector"].unique())
    months = sorted(monthly["month"].unique())
    sent = monthly.pivot(index="sector", columns="month", values="sentiment").reindex(index=sectors, columns=months)
    cov = monthly.pivot(index="sector", columns="month", values="coverage").reindex(index=sectors, columns=months)

    fig, axes = plt.subplots(2, 1, figsize=(11.0, 6.2), constrained_layout=True)
    fig.patch.set_facecolor(OFFWHITE)
    im1 = axes[0].imshow(sent.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=-0.35, vmax=0.35)
    axes[0].set_title("Monthly average raw sector sentiment", loc="left", fontsize=9)
    axes[0].set_yticks(np.arange(len(sectors)), labels=sectors, fontsize=7)
    axes[0].set_xticks([])
    fig.colorbar(im1, ax=axes[0], fraction=0.02, pad=0.01, label="VADER compound")
    im2 = axes[1].imshow(cov.to_numpy(), aspect="auto", cmap="YlGnBu", vmin=0.0, vmax=1.0)
    axes[1].set_title("Average coverage share", loc="left", fontsize=9)
    axes[1].set_yticks(np.arange(len(sectors)), labels=sectors, fontsize=7)
    ticks = np.linspace(0, max(0, len(months) - 1), min(8, len(months))).astype(int)
    axes[1].set_xticks(ticks, labels=[pd.Timestamp(months[i]).strftime("%Y-%m") for i in ticks], rotation=45, ha="right", fontsize=7)
    fig.colorbar(im2, ax=axes[1], fraction=0.02, pad=0.01, label="Coverage share")
    fig.suptitle("Signal Mosaic sentiment should be read with coverage context", x=0.01, ha="left", color=NAVY, fontweight="bold")
    fig.text(0.01, 0.003, "Source: Project B equity headlines and foundation coverage panel; coverage is descriptive, not proof of predictability.", fontsize=7)
    fig.savefig(FIGURES / "sentiment_coverage_context.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    equities = etl.load_clean_equities()
    news = etl.load_clean_news()
    trading_dates = equities["date"].drop_duplicates()
    sector_map = etl.ticker_sector_map(equities)
    _, aligned = features.assemble_headline_panel(news, trading_dates)

    coverage_path = DATA / "sector_coverage_daily.csv"
    if coverage_path.exists() and coverage_path.stat().st_size > 0:
        coverage = pd.read_csv(coverage_path, parse_dates=["trading_date"])
    else:
        coverage = features.daily_sector_coverage_panel(aligned, sector_map, trading_dates)
        _write_csv(coverage, coverage_path)

    scored = sentiment.score_headlines(aligned)
    ticker_day = sentiment.ticker_day_sentiment(scored)
    index = sentiment.build_sector_sentiment_index(ticker_day, coverage)
    diagnostics = sentiment.model_diagnostics(
        total_clean_headlines=len(news),
        scored_headlines=scored,
        ticker_day=ticker_day,
        sector_index=index,
    )
    summary = sentiment.sector_summary(scored, ticker_day, index)
    extreme = sentiment.extreme_headline_sample(scored, n=25)
    zero_sample = sentiment.zero_score_headline_sample(scored, n=100)

    sentiment.assert_no_lookahead(index)
    _write_csv(index, DATA / "sector_sentiment_index.csv")
    _write_csv(diagnostics, TABLES / "sentiment_model_diagnostics.csv")
    _write_csv(summary, TABLES / "sentiment_sector_summary.csv")
    _write_csv(extreme, TABLES / "sentiment_extreme_headlines.csv")
    _write_csv(zero_sample, TABLES / "vader_zero_score_headline_sample.csv")

    _sentiment_timeseries_figure(index)
    _neutrality_figure(scored)
    _coverage_context_figure(index)

    row = diagnostics.iloc[0]
    print(f"scored headlines: {int(row['total_scored_headlines'])}")
    print(f"exact-zero share: {float(row['exact_zero_compound_share']):.6f}")
    print(f"VADER-neutral share: {float(row['vader_neutral_share']):.6f}")
    print(f"positive share: {float(row['positive_share']):.6f}")
    print(f"negative share: {float(row['negative_share']):.6f}")
    print(f"ticker-days: {int(row['ticker_days'])}")
    print(f"sector sentiment rows: {len(index)}")
    print(f"sector-days without news: {int(row['sector_days_without_news'])}")
    print("lag validation: passed")


if __name__ == "__main__":
    main()
