"""Foundation ETL for Project B.

Raw data is loaded only through :mod:`src.data_access`. Cleaning is conservative:
mechanical data issues are quantified, exact-key duplicates are removed, and real
extreme market observations are retained for later modelling.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src import data_access

SAMPLE_START = pd.Timestamp("2020-01-01")
SAMPLE_END = pd.Timestamp("2023-12-31")
PRICE_FIELDS = ["open", "high", "low", "close", "adjClose", "volume"]


@dataclass(frozen=True)
class CleaningSummary:
    """Mechanical changes made to one source dataset."""

    dataset: str
    raw_rows: int
    sample_rows: int
    clean_rows: int
    rows_outside_sample: int
    duplicate_rows_removed: int
    blank_publisher_rows: int = 0


def normalise_date(series: pd.Series) -> pd.Series:
    """Return timezone-naive midnight timestamps without changing UTC dates."""

    parsed = pd.to_datetime(series, utc=True)
    return parsed.dt.tz_convert(None).dt.normalize().astype("datetime64[ns]")


def _require_columns(frame: pd.DataFrame, required: set[str], dataset: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{dataset} is missing required columns: {sorted(missing)}")


def clean_price_panel(
    raw: pd.DataFrame,
    *,
    dataset: str,
    has_sector: bool,
) -> tuple[pd.DataFrame, CleaningSummary]:
    """Clean an equity or crypto OHLCV panel without deleting outliers."""

    required = {"ticker", "date", *PRICE_FIELDS}
    if has_sector:
        required.add("sector")
    _require_columns(raw, required, dataset)

    frame = raw.copy()
    raw_rows = len(frame)
    frame["date"] = normalise_date(frame["date"])

    in_sample = frame["date"].between(SAMPLE_START, SAMPLE_END)
    rows_outside = int((~in_sample).sum())
    frame = frame.loc[in_sample].copy()
    sample_rows = len(frame)

    for column in PRICE_FIELDS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    duplicate_mask = frame.duplicated(["ticker", "date"], keep="first")
    duplicate_rows = int(duplicate_mask.sum())
    frame = frame.loc[~duplicate_mask].copy()

    frame["ticker"] = frame["ticker"].astype("string")
    if has_sector:
        frame["sector"] = frame["sector"].astype("string")

    columns = ["ticker", "date", *PRICE_FIELDS]
    if has_sector:
        columns.append("sector")
    frame = (
        frame[columns]
        .sort_values(["ticker", "date"], kind="stable")
        .reset_index(drop=True)
    )
    summary = CleaningSummary(
        dataset=dataset,
        raw_rows=raw_rows,
        sample_rows=sample_rows,
        clean_rows=len(frame),
        rows_outside_sample=rows_outside,
        duplicate_rows_removed=duplicate_rows,
    )
    return frame, summary


def clean_news_panel(raw: pd.DataFrame) -> tuple[pd.DataFrame, CleaningSummary]:
    """Normalise headline dates and remove exact ticker-date-title duplicates."""

    required = {"date", "ticker", "sector", "title", "url", "publisher"}
    _require_columns(raw, required, "news_headlines")

    frame = raw.copy()
    raw_rows = len(frame)
    frame["source_timestamp"] = pd.to_datetime(frame["date"], utc=True)
    frame["source_date"] = normalise_date(frame["date"])

    in_sample = frame["source_date"].between(SAMPLE_START, SAMPLE_END)
    rows_outside = int((~in_sample).sum())
    frame = frame.loc[in_sample].copy()
    sample_rows = len(frame)

    duplicate_mask = frame.duplicated(
        ["ticker", "source_date", "title"], keep="first"
    )
    duplicate_rows = int(duplicate_mask.sum())
    frame = frame.loc[~duplicate_mask].copy()

    frame["ticker"] = frame["ticker"].astype("string")
    frame["sector"] = frame["sector"].astype("string")
    blank_publishers = int(frame["publisher"].fillna("").str.strip().eq("").sum())

    frame = (
        frame[
            [
                "source_timestamp",
                "source_date",
                "ticker",
                "sector",
                "title",
                "url",
                "publisher",
            ]
        ]
        .sort_values(["source_date", "ticker", "title"], kind="stable")
        .reset_index(drop=True)
    )
    summary = CleaningSummary(
        dataset="news_headlines",
        raw_rows=raw_rows,
        sample_rows=sample_rows,
        clean_rows=len(frame),
        rows_outside_sample=rows_outside,
        duplicate_rows_removed=duplicate_rows,
        blank_publisher_rows=blank_publishers,
    )
    return frame, summary


def load_clean_equities(
    *, return_summary: bool = False
) -> pd.DataFrame | tuple[pd.DataFrame, CleaningSummary]:
    """Load and conservatively clean the equity price panel."""

    result = clean_price_panel(
        data_access.load_equity_prices(),
        dataset="equity_prices",
        has_sector=True,
    )
    return result if return_summary else result[0]


def load_clean_crypto(
    *, return_summary: bool = False
) -> pd.DataFrame | tuple[pd.DataFrame, CleaningSummary]:
    """Load and clean crypto prices, including the 2023 sample cap."""

    result = clean_price_panel(
        data_access.load_crypto_prices(),
        dataset="crypto_prices",
        has_sector=False,
    )
    return result if return_summary else result[0]


def load_clean_news(
    *, return_summary: bool = False
) -> pd.DataFrame | tuple[pd.DataFrame, CleaningSummary]:
    """Load and clean the headline panel without scoring sentiment."""

    result = clean_news_panel(data_access.load_news_headlines())
    return result if return_summary else result[0]


def price_integrity_metrics(prices: pd.DataFrame, *, calendar: str) -> dict[str, int]:
    """Quantify nulls, OHLCV consistency, duplicate keys, and missing dates."""

    _require_columns(prices, {"ticker", "date", *PRICE_FIELDS}, "prices")
    null_cells = int(prices[["ticker", "date", *PRICE_FIELDS]].isna().sum().sum())
    duplicate_keys = int(prices.duplicated(["ticker", "date"]).sum())
    nonpositive_price_rows = int(
        (prices[["open", "high", "low", "close", "adjClose"]] <= 0)
        .any(axis=1)
        .sum()
    )
    negative_volume_rows = int((prices["volume"] < 0).sum())
    high_violations = int(
        (prices["high"] < prices[["open", "low", "close"]].max(axis=1)).sum()
    )
    low_violations = int(
        (prices["low"] > prices[["open", "high", "close"]].min(axis=1)).sum()
    )

    if calendar == "equity":
        expected_dates = pd.DatetimeIndex(sorted(prices["date"].dropna().unique()))
    elif calendar == "daily":
        expected_dates = pd.date_range(SAMPLE_START, SAMPLE_END, freq="D")
    else:
        raise ValueError("calendar must be 'equity' or 'daily'")

    observed = prices.groupby("ticker", observed=True)["date"].nunique()
    missing_by_ticker = len(expected_dates) - observed
    return {
        "null_critical_cells": null_cells,
        "duplicate_ticker_date_rows": duplicate_keys,
        "nonpositive_price_rows": nonpositive_price_rows,
        "negative_volume_rows": negative_volume_rows,
        "high_consistency_violations": high_violations,
        "low_consistency_violations": low_violations,
        "missing_ticker_dates": int(missing_by_ticker.clip(lower=0).sum()),
        "expected_dates_per_ticker": int(len(expected_dates)),
    }


def news_integrity_metrics(news: pd.DataFrame) -> dict[str, int]:
    """Quantify the cleaned headline key and required-field state."""

    _require_columns(
        news,
        {"source_date", "ticker", "sector", "title", "url", "publisher"},
        "news_headlines",
    )
    return {
        "duplicate_ticker_source_date_title_rows": int(
            news.duplicated(["ticker", "source_date", "title"]).sum()
        ),
        "missing_source_date_rows": int(news["source_date"].isna().sum()),
        "missing_ticker_rows": int(news["ticker"].isna().sum()),
        "missing_sector_rows": int(news["sector"].isna().sum()),
        "missing_title_rows": int(news["title"].isna().sum()),
        "missing_url_rows": int(news["url"].isna().sum()),
        "missing_publisher_rows": int(news["publisher"].isna().sum()),
    }


def ticker_sector_map(equities: pd.DataFrame) -> pd.DataFrame:
    """Return the deterministic one-sector-per-equity ticker map."""

    _require_columns(equities, {"ticker", "sector"}, "equity_prices")
    mapping = (
        equities[["ticker", "sector"]]
        .drop_duplicates()
        .sort_values(["sector", "ticker"], kind="stable")
        .reset_index(drop=True)
    )
    ticker_counts = mapping.groupby("ticker", observed=True)["sector"].nunique()
    if ticker_counts.gt(1).any():
        bad = ticker_counts.loc[ticker_counts.gt(1)].index.tolist()
        raise ValueError(f"tickers mapped to multiple sectors: {bad}")
    return mapping


def sector_mapping_issues(
    equities: pd.DataFrame,
    news: pd.DataFrame,
) -> dict[str, int]:
    """Check whether cleaned headline sectors agree with the equity universe."""

    universe = ticker_sector_map(equities).rename(
        columns={"sector": "expected_sector"}
    )
    mapped = news.merge(universe, on="ticker", how="left", validate="many_to_one")
    return {
        "news_unknown_ticker_rows": int(mapped["expected_sector"].isna().sum()),
        "news_sector_mismatch_rows": int(
            (
                mapped["expected_sector"].notna()
                & mapped["sector"].ne(mapped["expected_sector"])
            ).sum()
        ),
    }


def robust_outlier_flags(returns: pd.Series, threshold: float = 8.0) -> pd.Series:
    """Flag extreme returns using a robust MAD z-score without dropping them."""

    values = pd.to_numeric(returns, errors="coerce")
    median = values.median()
    mad = np.median(np.abs(values.dropna() - median))
    if not np.isfinite(mad) or mad == 0:
        return pd.Series(False, index=returns.index)
    robust_z = 0.67448975 * (values - median) / mad
    return robust_z.abs() > threshold
