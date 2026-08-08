"""Foundation feature engineering for Project B.

This module builds return matrices, headline trading-day alignment, ticker-day
news panels, and coverage-breadth inputs. It does not score sentiment, optimise
portfolios, run backtests, or construct investable sentiment signals.
"""
from __future__ import annotations

import json
from collections.abc import Iterable

import numpy as np
import pandas as pd

HEADLINE_SEPARATOR = " ||| "


def _as_datetime_index(values: Iterable[pd.Timestamp]) -> pd.DatetimeIndex:
    dates = pd.DatetimeIndex(pd.to_datetime(list(values))).tz_localize(None)
    return dates.normalize().astype("datetime64[ns]").sort_values().unique()


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")


def daily_returns(
    prices: pd.DataFrame,
    price_col: str = "adjClose",
    *,
    prefix: str | None = None,
) -> pd.DataFrame:
    """Return a wide simple-return matrix computed within each ticker.

    The first all-missing return row is dropped. Individual missing values are
    not imputed.
    """

    _require_columns(prices, {"ticker", "date", price_col}, "prices")
    if prices.duplicated(["ticker", "date"]).any():
        raise ValueError("prices must be unique by ticker-date before returns")

    frame = prices[["date", "ticker", price_col]].copy()
    frame["date"] = (
        pd.to_datetime(frame["date"])
        .dt.tz_localize(None)
        .dt.normalize()
        .astype("datetime64[ns]")
    )
    frame[price_col] = pd.to_numeric(frame[price_col], errors="coerce")
    frame = frame.sort_values(["ticker", "date"], kind="stable")
    wide_prices = frame.pivot(index="date", columns="ticker", values=price_col)
    returns = wide_prices.pct_change(fill_method=None)
    returns = returns.loc[~returns.isna().all(axis=1)].sort_index()
    returns.index.name = "date"
    if returns.columns.duplicated().any():
        raise ValueError("duplicate ticker columns in return matrix")
    if prefix:
        returns = returns.rename(columns={col: f"{prefix}{col}" for col in returns.columns})
    return returns


def combined_returns_on_equity_calendar(
    equity_returns: pd.DataFrame,
    crypto_returns_native: pd.DataFrame,
    *,
    equity_prefix: str = "EQ_",
    crypto_prefix: str = "CR_",
) -> pd.DataFrame:
    """Left-join native crypto returns onto the equity-return calendar."""

    eq = equity_returns.copy()
    cr = crypto_returns_native.copy()
    eq.index = pd.DatetimeIndex(pd.to_datetime(eq.index)).normalize().astype("datetime64[ns]")
    cr.index = pd.DatetimeIndex(pd.to_datetime(cr.index)).normalize().astype("datetime64[ns]")
    if not eq.index.is_unique or not cr.index.is_unique:
        raise ValueError("return indexes must be unique dates")
    if eq.columns.duplicated().any() or cr.columns.duplicated().any():
        raise ValueError("return matrices must not contain duplicate columns")

    eq = eq.rename(columns={col: f"{equity_prefix}{col}" for col in eq.columns})
    cr = cr.rename(columns={col: f"{crypto_prefix}{col}" for col in cr.columns})
    combined = eq.join(cr, how="left").sort_index()
    combined.index.name = "date"
    return combined


def align_headlines_to_trading_days(
    headlines: pd.DataFrame,
    trading_dates: Iterable[pd.Timestamp],
) -> pd.DataFrame:
    """Map each source day to the same or next available equity trading day."""

    _require_columns(headlines, {"source_date", "ticker", "sector", "title"}, "headlines")
    dates = _as_datetime_index(trading_dates)
    if dates.empty:
        raise ValueError("trading_dates must not be empty")

    frame = headlines.copy()
    frame["source_date"] = (
        pd.to_datetime(frame["source_date"])
        .dt.tz_localize(None)
        .dt.normalize()
        .astype("datetime64[ns]")
    )
    positions = dates.searchsorted(pd.DatetimeIndex(frame["source_date"]), side="left")
    valid = positions < len(dates)

    frame["trading_date"] = pd.NaT
    frame.loc[valid, "trading_date"] = dates.take(positions[valid]).to_numpy()
    frame["alignment_lag_days"] = (
        frame["trading_date"] - frame["source_date"]
    ).dt.days.astype("Int64")
    frame["alignment_status"] = "outside_available_calendar"
    same_day = frame["trading_date"].notna() & frame["alignment_lag_days"].eq(0)
    shifted = frame["trading_date"].notna() & ~same_day
    frame.loc[same_day, "alignment_status"] = "same_day"
    frame.loc[shifted, "alignment_status"] = "shifted_forward"
    return frame.sort_values(["source_date", "ticker", "title"], kind="stable").reset_index(drop=True)


def assemble_headline_panel(
    headlines: pd.DataFrame,
    trading_dates: Iterable[pd.Timestamp] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the full ticker-trading-day news panel while preserving titles.

    `headline_titles_json` stores title boundaries losslessly for later
    per-headline sentiment scoring. `combined_headlines` is display-oriented only.
    """

    if trading_dates is None:
        if "trading_date" not in headlines.columns:
            raise ValueError("trading_dates are required unless headlines are aligned")
        aligned = headlines.copy()
    else:
        aligned = align_headlines_to_trading_days(headlines, trading_dates)

    usable = aligned.dropna(subset=["trading_date"]).copy()
    usable["trading_date"] = (
        pd.to_datetime(usable["trading_date"])
        .dt.normalize()
        .astype("datetime64[ns]")
    )

    def titles_json(values: pd.Series) -> str:
        return json.dumps([str(value) for value in values], ensure_ascii=True)

    def publisher_count(values: pd.Series) -> int:
        cleaned = values.dropna().astype(str).str.strip()
        return int(cleaned.loc[cleaned.ne("")].nunique())

    panel = (
        usable.groupby(["trading_date", "ticker", "sector"], observed=True, sort=True)
        .agg(
            headline_count=("title", "size"),
            headline_titles_json=("title", titles_json),
            combined_headlines=("title", lambda values: HEADLINE_SEPARATOR.join(map(str, values))),
            source_date_min=("source_date", "min"),
            source_date_max=("source_date", "max"),
            max_alignment_lag_days=("alignment_lag_days", "max"),
            publisher_count=("publisher", publisher_count),
        )
        .reset_index()
        .sort_values(["trading_date", "ticker"], kind="stable")
        .reset_index(drop=True)
    )
    return panel, aligned


def monthly_coverage_lens(
    aligned_headlines: pd.DataFrame,
    ticker_sector_map: pd.DataFrame,
    trading_dates: Iterable[pd.Timestamp],
) -> pd.DataFrame:
    """Return monthly Signal Mosaic Coverage Lens by sector.

    Breadth is ``1 / (5 * sum_i(p_i**2))`` for sector-months with headlines and
    remains NaN when a sector-month has no headlines.
    """

    _require_columns(ticker_sector_map, {"ticker", "sector"}, "ticker_sector_map")
    dates = _as_datetime_index(trading_dates)
    months = pd.Index(dates.to_period("M").astype(str).unique(), name="month")
    sectors = pd.Index(sorted(ticker_sector_map["sector"].dropna().astype(str).unique()), name="sector")
    grid = pd.MultiIndex.from_product([months, sectors], names=["month", "sector"]).to_frame(index=False)

    usable = aligned_headlines.dropna(subset=["trading_date"]).copy()
    usable["trading_date"] = (
        pd.to_datetime(usable["trading_date"])
        .dt.normalize()
        .astype("datetime64[ns]")
    )
    usable["month"] = usable["trading_date"].dt.to_period("M").astype(str)
    counts = (
        usable.groupby(["month", "sector", "ticker"], observed=True)
        .size()
        .rename("ticker_article_count")
        .reset_index()
    )
    if counts.empty:
        result = grid.copy()
        result["article_count"] = 0
        result["covered_tickers"] = 0
        result["hhi"] = np.nan
        result["breadth"] = np.nan
        return result

    counts["share"] = counts["ticker_article_count"] / counts.groupby(
        ["month", "sector"], observed=True
    )["ticker_article_count"].transform("sum")
    breadth = (
        counts.groupby(["month", "sector"], observed=True)
        .agg(
            article_count=("ticker_article_count", "sum"),
            covered_tickers=("ticker", "nunique"),
            hhi=("share", lambda values: float(np.square(values).sum())),
        )
        .reset_index()
    )
    result = grid.merge(breadth, on=["month", "sector"], how="left")
    result["article_count"] = result["article_count"].fillna(0).astype(int)
    result["covered_tickers"] = result["covered_tickers"].fillna(0).astype(int)
    result["breadth"] = np.where(
        result["article_count"].gt(0),
        1.0 / (5.0 * result["hhi"]),
        np.nan,
    )
    return result.sort_values(["month", "sector"], kind="stable").reset_index(drop=True)


def daily_sector_coverage_panel(
    aligned_headlines: pd.DataFrame,
    ticker_sector_map: pd.DataFrame,
    trading_dates: Iterable[pd.Timestamp],
    *,
    window: int = 21,
) -> pd.DataFrame:
    """Return daily sector coverage on the equity calendar with backward rolls."""

    _require_columns(ticker_sector_map, {"ticker", "sector"}, "ticker_sector_map")
    if window < 1:
        raise ValueError("window must be positive")

    dates = _as_datetime_index(trading_dates)
    sectors = pd.Index(sorted(ticker_sector_map["sector"].dropna().astype(str).unique()), name="sector")
    tickers = ticker_sector_map.copy()
    tickers["ticker"] = tickers["ticker"].astype(str)
    tickers["sector"] = tickers["sector"].astype(str)

    usable = aligned_headlines.dropna(subset=["trading_date"]).copy()
    usable["trading_date"] = (
        pd.to_datetime(usable["trading_date"])
        .dt.normalize()
        .astype("datetime64[ns]")
    )
    ticker_counts = (
        usable.groupby(["trading_date", "sector", "ticker"], observed=True)
        .size()
        .rename("article_count")
        .reset_index()
    )

    full_ticker_grid = (
        pd.MultiIndex.from_product(
            [dates, tickers["ticker"].tolist()],
            names=["trading_date", "ticker"],
        )
        .to_frame(index=False)
        .merge(tickers, on="ticker", how="left", validate="many_to_one")
    )
    ticker_daily = full_ticker_grid.merge(
        ticker_counts,
        on=["trading_date", "sector", "ticker"],
        how="left",
    )
    ticker_daily["article_count"] = ticker_daily["article_count"].fillna(0).astype(int)

    sector_daily = (
        ticker_daily.groupby(["trading_date", "sector"], observed=True)
        .agg(
            article_count=("article_count", "sum"),
            covered_tickers=("article_count", lambda values: int((values > 0).sum())),
        )
        .reset_index()
    )
    sector_daily["coverage_share"] = sector_daily["covered_tickers"] / 5.0
    sector_daily["has_news"] = sector_daily["article_count"].gt(0)

    def breadth_from_counts(values: pd.Series) -> float:
        total = values.sum()
        if total <= 0:
            return np.nan
        shares = values / total
        return float(1.0 / (5.0 * np.square(shares).sum()))

    same_day = (
        ticker_daily.groupby(["trading_date", "sector"], observed=True)["article_count"]
        .apply(breadth_from_counts)
        .rename("breadth")
        .reset_index()
    )
    sector_daily = sector_daily.merge(same_day, on=["trading_date", "sector"], how="left")

    rolled_parts = []
    for sector, group in ticker_daily.sort_values(["sector", "ticker", "trading_date"]).groupby(
        "sector", observed=True
    ):
        pivot = group.pivot(index="trading_date", columns="ticker", values="article_count").reindex(dates).fillna(0)
        rolling_counts = pivot.rolling(window=window, min_periods=1).sum()
        rolling_total = rolling_counts.sum(axis=1)
        rolling_covered = rolling_counts.gt(0).sum(axis=1)
        rolling_breadth = rolling_counts.apply(breadth_from_counts, axis=1)
        rolled_parts.append(
            pd.DataFrame(
                {
                    "trading_date": dates,
                    "sector": sector,
                    "rolling_21d_article_count": rolling_total.to_numpy(dtype=float),
                    "rolling_21d_covered_tickers": rolling_covered.to_numpy(dtype=int),
                    "rolling_21d_breadth": rolling_breadth.to_numpy(dtype=float),
                }
            )
        )
    rolled = pd.concat(rolled_parts, ignore_index=True)
    result = sector_daily.merge(rolled, on=["trading_date", "sector"], how="left")
    return result.sort_values(["trading_date", "sector"], kind="stable").reset_index(drop=True)
