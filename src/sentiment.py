"""Standalone equity-sector sentiment index construction.

Sentiment is scored at the individual equity-headline level with plain NLTK
VADER, aggregated first to ticker-day observations, and then equal-weighted
across available tickers within each sector. Missing news remains missing, not
neutral.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd

POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05
REQUIRED_SCORE_COLUMNS = {
    "source_date",
    "trading_date",
    "ticker",
    "sector",
    "title",
    "article_id",
    "vader_compound",
    "vader_positive",
    "vader_neutral",
    "vader_negative",
    "vader_category",
}
SECTOR_INDEX_COLUMNS = [
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
]


@dataclass(frozen=True)
class SentimentDiagnostics:
    """Top-level counts from the headline and sector sentiment pipeline."""

    total_clean_headlines: int
    total_scored_headlines: int
    unscored_or_missing_title_count: int
    exact_zero_compound_count: int
    vader_neutral_count: int
    positive_count: int
    negative_count: int
    compound_mean: float
    compound_std: float
    compound_min: float
    compound_max: float
    ticker_days: int
    sector_days_with_news: int
    sector_days_without_news: int


def get_vader_analyzer(*, allow_download: bool = True):
    """Return NLTK's official VADER analyzer, with a controlled local download.

    The Streamlit app must not call this helper; it is for local build scripts
    that precompute `results/` artifacts.
    """

    try:
        import nltk
        from nltk.sentiment import SentimentIntensityAnalyzer
    except ImportError as exc:
        raise RuntimeError(
            "nltk is not installed in the active environment. Install the "
            "declared requirements-dev.txt dependency with the project venv."
        ) from exc

    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
    except LookupError:
        if allow_download:
            ok = nltk.download("vader_lexicon", quiet=True)
            if not ok:
                raise RuntimeError("nltk could not download the official vader_lexicon")
        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError as exc:
            raise RuntimeError(
                "official NLTK vader_lexicon is unavailable after the controlled "
                "download attempt"
            ) from exc
    return SentimentIntensityAnalyzer()


def score_headlines(
    panel: pd.DataFrame,
    *,
    analyzer=None,
    allow_download: bool = True,
) -> pd.DataFrame:
    """Score aligned equity headlines one title at a time with plain VADER."""

    required = {"source_date", "trading_date", "ticker", "sector", "title"}
    _require_columns(panel, required, "headlines")
    scorer = analyzer if analyzer is not None else get_vader_analyzer(allow_download=allow_download)

    frame = panel.copy()
    frame["source_date"] = _normalise_datetime(frame["source_date"])
    frame["trading_date"] = _normalise_datetime(frame["trading_date"])
    frame = frame.loc[frame["trading_date"].notna()].copy()
    frame = frame.loc[frame["title"].notna()].copy()
    frame["title"] = frame["title"].astype(str)
    frame = frame.loc[frame["title"].str.len().gt(0)].copy()
    frame["ticker"] = frame["ticker"].astype(str)
    frame["sector"] = frame["sector"].astype(str)
    if "url" in frame.columns:
        frame["article_id"] = frame["url"].fillna("").astype(str)
    else:
        frame["article_id"] = ""
    empty_id = frame["article_id"].str.len().eq(0)
    if empty_id.any():
        frame.loc[empty_id, "article_id"] = frame.loc[empty_id].apply(_fallback_article_id, axis=1)

    unique_titles = frame["title"].drop_duplicates()
    score_map = {title: scorer.polarity_scores(title) for title in unique_titles}
    frame["vader_compound"] = frame["title"].map(lambda title: score_map[title]["compound"])
    frame["vader_positive"] = frame["title"].map(lambda title: score_map[title]["pos"])
    frame["vader_neutral"] = frame["title"].map(lambda title: score_map[title]["neu"])
    frame["vader_negative"] = frame["title"].map(lambda title: score_map[title]["neg"])
    frame["vader_category"] = frame["vader_compound"].map(compound_category)
    columns = [
        "source_date",
        "trading_date",
        "ticker",
        "sector",
        "title",
        "article_id",
        "vader_compound",
        "vader_positive",
        "vader_neutral",
        "vader_negative",
        "vader_category",
    ]
    return frame[columns].sort_values(["trading_date", "sector", "ticker", "title"], kind="stable").reset_index(drop=True)


def ticker_day_sentiment(scores: pd.DataFrame) -> pd.DataFrame:
    """Aggregate scored headlines to one equal-headline-weight ticker-day row."""

    _require_columns(scores, REQUIRED_SCORE_COLUMNS, "headline scores")
    frame = scores.copy()
    frame["trading_date"] = _normalise_datetime(frame["trading_date"])

    grouped = (
        frame.groupby(["trading_date", "ticker", "sector"], observed=True, sort=True)
        .agg(
            headline_count=("vader_compound", "size"),
            mean_compound=("vader_compound", "mean"),
            median_compound=("vader_compound", "median"),
            mean_positive=("vader_positive", "mean"),
            mean_neutral=("vader_neutral", "mean"),
            mean_negative=("vader_negative", "mean"),
            positive_headline_share=("vader_category", lambda values: float((values == "positive").mean())),
            neutral_headline_share=("vader_category", lambda values: float((values == "neutral").mean())),
            negative_headline_share=("vader_category", lambda values: float((values == "negative").mean())),
            minimum_compound=("vader_compound", "min"),
            maximum_compound=("vader_compound", "max"),
        )
        .reset_index()
        .sort_values(["trading_date", "sector", "ticker"], kind="stable")
        .reset_index(drop=True)
    )
    if grouped.duplicated(["trading_date", "ticker"]).any():
        raise ValueError("ticker-day sentiment keys are not unique")
    return grouped


def sector_sentiment_index(
    scores: pd.DataFrame,
    coverage_daily: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build the daily equal-ticker-weight sector sentiment index.

    For backward compatibility, `scores` may be either per-headline scores or an
    already aggregated ticker-day sentiment frame.
    """

    if coverage_daily is None:
        raise ValueError("coverage_daily is required to build the complete sector grid")
    ticker_day = (
        scores.copy()
        if {"mean_compound", "headline_count"}.issubset(scores.columns)
        else ticker_day_sentiment(scores)
    )
    return build_sector_sentiment_index(ticker_day, coverage_daily)


def build_sector_sentiment_index(
    ticker_day: pd.DataFrame,
    coverage_daily: pd.DataFrame,
) -> pd.DataFrame:
    """Equal-weight ticker-day sentiment across available tickers in each sector."""

    required_ticker = {"trading_date", "ticker", "sector", "headline_count", "mean_compound"}
    required_coverage = {"sector", "article_count", "covered_tickers", "coverage_share", "breadth", "has_news"}
    _require_columns(ticker_day, required_ticker, "ticker-day sentiment")
    _require_columns(coverage_daily, required_coverage, "daily coverage")

    coverage = coverage_daily.copy()
    date_col = "date" if "date" in coverage.columns else "trading_date"
    if date_col not in coverage.columns:
        raise ValueError("coverage_daily requires date or trading_date")
    coverage["date"] = _normalise_datetime(coverage[date_col])
    coverage["sector"] = coverage["sector"].astype(str)
    coverage["article_count"] = pd.to_numeric(coverage["article_count"], errors="raise").astype(int)
    coverage["covered_tickers"] = pd.to_numeric(coverage["covered_tickers"], errors="raise").astype(int)
    coverage["coverage_share"] = pd.to_numeric(coverage["coverage_share"], errors="raise")
    coverage["breadth"] = pd.to_numeric(coverage["breadth"], errors="coerce")
    if coverage["has_news"].dtype != bool:
        coverage["has_news"] = coverage["has_news"].astype(str).str.lower().eq("true")
    coverage = coverage[
        ["date", "sector", "article_count", "covered_tickers", "coverage_share", "breadth", "has_news"]
    ].sort_values(["date", "sector"], kind="stable")
    if coverage.duplicated(["date", "sector"]).any():
        raise ValueError("coverage_daily has duplicate date-sector rows")

    td = ticker_day.copy()
    td["trading_date"] = _normalise_datetime(td["trading_date"])
    td["sector"] = td["sector"].astype(str)
    td["ticker_sentiment_category"] = td["mean_compound"].map(compound_category)
    sector = (
        td.groupby(["trading_date", "sector"], observed=True, sort=True)
        .agg(
            vader_compound_raw=("mean_compound", "mean"),
            positive_ticker_share=("ticker_sentiment_category", lambda values: float((values == "positive").mean())),
            neutral_ticker_share=("ticker_sentiment_category", lambda values: float((values == "neutral").mean())),
            negative_ticker_share=("ticker_sentiment_category", lambda values: float((values == "negative").mean())),
            ticker_day_article_count=("headline_count", "sum"),
            ticker_day_covered_tickers=("ticker", "nunique"),
        )
        .reset_index()
        .rename(columns={"trading_date": "date"})
    )
    result = coverage.merge(sector, on=["date", "sector"], how="left", validate="one_to_one")
    _assert_coverage_reconciles(result)
    result = add_lookahead_safe_fields(result)
    result = result[SECTOR_INDEX_COLUMNS].sort_values(["date", "sector"], kind="stable").reset_index(drop=True)
    _validate_sector_index(result)
    return result


def add_lookahead_safe_fields(index: pd.DataFrame, *, window: int = 21) -> pd.DataFrame:
    """Add full-grid lagged and trailing sentiment fields by sector."""

    frame = index.copy().sort_values(["sector", "date"], kind="stable")
    pieces = []
    for _, group in frame.groupby("sector", observed=True, sort=False):
        group = group.sort_values("date", kind="stable").copy()
        group["vader_compound_lag1"] = group["vader_compound_raw"].shift(1)
        group["vader_compound_21d_trailing"] = (
            group["vader_compound_raw"].rolling(window=window, min_periods=1).mean()
        )
        group["vader_compound_21d_trailing_lag1"] = group["vader_compound_21d_trailing"].shift(1)
        previous_date = group["date"].shift(1)
        group["signal_source_date"] = previous_date.where(group["vader_compound_lag1"].notna())
        group["signal_available"] = group["vader_compound_lag1"].notna()
        pieces.append(group)
    return pd.concat(pieces, ignore_index=True).sort_values(["date", "sector"], kind="stable")


def model_diagnostics(
    *,
    total_clean_headlines: int,
    scored_headlines: pd.DataFrame,
    ticker_day: pd.DataFrame,
    sector_index: pd.DataFrame,
) -> pd.DataFrame:
    """Return one-row model diagnostics for the standalone sentiment build."""

    scores = scored_headlines["vader_compound"].astype(float)
    exact_zero = int(scores.eq(0.0).sum())
    neutral = int(scored_headlines["vader_category"].eq("neutral").sum())
    positive = int(scored_headlines["vader_category"].eq("positive").sum())
    negative = int(scored_headlines["vader_category"].eq("negative").sum())
    total_scored = len(scored_headlines)
    diagnostics = SentimentDiagnostics(
        total_clean_headlines=total_clean_headlines,
        total_scored_headlines=total_scored,
        unscored_or_missing_title_count=total_clean_headlines - total_scored,
        exact_zero_compound_count=exact_zero,
        vader_neutral_count=neutral,
        positive_count=positive,
        negative_count=negative,
        compound_mean=float(scores.mean()),
        compound_std=float(scores.std(ddof=1)),
        compound_min=float(scores.min()),
        compound_max=float(scores.max()),
        ticker_days=len(ticker_day),
        sector_days_with_news=int(sector_index["has_news"].sum()),
        sector_days_without_news=int((~sector_index["has_news"]).sum()),
    )
    row = diagnostics.__dict__.copy()
    row["exact_zero_compound_share"] = exact_zero / total_scored if total_scored else np.nan
    row["vader_neutral_share"] = neutral / total_scored if total_scored else np.nan
    row["positive_share"] = positive / total_scored if total_scored else np.nan
    row["negative_share"] = negative / total_scored if total_scored else np.nan
    return pd.DataFrame([row])


def sector_summary(scored_headlines: pd.DataFrame, ticker_day: pd.DataFrame, sector_index: pd.DataFrame) -> pd.DataFrame:
    """Return per-sector sentiment and coverage diagnostics."""

    headline_counts = scored_headlines.groupby("sector", observed=True).size().rename("headline_count")
    ticker_counts = ticker_day.groupby("sector", observed=True).size().rename("ticker_day_count")
    sector = sector_index.copy()
    sector["raw_category"] = sector["vader_compound_raw"].map(lambda value: compound_category(value) if pd.notna(value) else "missing")

    def category_share(values: pd.Series, category: str) -> float:
        valid = values.loc[values.ne("missing")]
        if valid.empty:
            return np.nan
        return float(valid.eq(category).mean())

    def exact_zero_share(values: pd.Series) -> float:
        valid = values.dropna()
        if valid.empty:
            return np.nan
        return float(valid.eq(0.0).mean())

    summary = (
        sector.groupby("sector", observed=True)
        .agg(
            sector_day_count_with_news=("has_news", "sum"),
            mean_raw_compound=("vader_compound_raw", "mean"),
            std_raw_compound=("vader_compound_raw", "std"),
            positive_sector_day_share=("raw_category", lambda values: category_share(values, "positive")),
            neutral_sector_day_share=("raw_category", lambda values: category_share(values, "neutral")),
            negative_sector_day_share=("raw_category", lambda values: category_share(values, "negative")),
            exact_zero_share=("vader_compound_raw", exact_zero_share),
            average_covered_tickers=("covered_tickers", "mean"),
            average_coverage_share=("coverage_share", "mean"),
            average_breadth=("breadth", "mean"),
        )
        .reset_index()
    )
    summary = summary.merge(headline_counts, on="sector", how="left")
    summary = summary.merge(ticker_counts, on="sector", how="left")
    summary["headline_count"] = summary["headline_count"].fillna(0).astype(int)
    summary["ticker_day_count"] = summary["ticker_day_count"].fillna(0).astype(int)
    columns = [
        "sector",
        "headline_count",
        "ticker_day_count",
        "sector_day_count_with_news",
        "mean_raw_compound",
        "std_raw_compound",
        "positive_sector_day_share",
        "neutral_sector_day_share",
        "negative_sector_day_share",
        "exact_zero_share",
        "average_covered_tickers",
        "average_coverage_share",
        "average_breadth",
    ]
    return summary[columns].sort_values("sector", kind="stable").reset_index(drop=True)


def extreme_headline_sample(scored_headlines: pd.DataFrame, n: int = 25) -> pd.DataFrame:
    """Return compact most-positive and most-negative headline samples."""

    cols = ["trading_date", "ticker", "sector", "title", "vader_compound"]
    positive = scored_headlines.sort_values(
        ["vader_compound", "trading_date", "ticker", "title"],
        ascending=[False, True, True, True],
    ).head(n).copy()
    positive["tail"] = "most_positive"
    negative = scored_headlines.sort_values(
        ["vader_compound", "trading_date", "ticker", "title"],
        ascending=[True, True, True, True],
    ).head(n).copy()
    negative["tail"] = "most_negative"
    return pd.concat([positive, negative], ignore_index=True)[["tail", *cols]].rename(
        columns={"trading_date": "date", "vader_compound": "compound"}
    )


def zero_score_headline_sample(scored_headlines: pd.DataFrame, n: int = 100) -> pd.DataFrame:
    """Return deterministic sample of exact-zero compound headlines."""

    zero = scored_headlines.loc[scored_headlines["vader_compound"].eq(0.0)].copy()
    if zero.empty:
        return pd.DataFrame(columns=["date", "ticker", "sector", "title", "compound", "occurrences"])
    counts = zero.groupby("title", observed=True).size().rename("occurrences").reset_index()
    sample = zero.merge(counts, on="title", how="left")
    sample = sample.sort_values(
        ["occurrences", "trading_date", "ticker", "sector", "title"],
        ascending=[False, True, True, True, True],
        kind="stable",
    ).head(n)
    return sample[
        ["trading_date", "ticker", "sector", "title", "vader_compound", "occurrences"]
    ].rename(columns={"trading_date": "date", "vader_compound": "compound"})


def assert_no_lookahead(index: pd.DataFrame) -> None:
    """Validate full-grid lag and trailing timing rules."""

    frame = index.copy()
    frame["date"] = _normalise_datetime(frame["date"])
    for sector, group in frame.sort_values(["sector", "date"]).groupby("sector", observed=True):
        raw = group["vader_compound_raw"].reset_index(drop=True)
        lag = group["vader_compound_lag1"].reset_index(drop=True)
        trailing = group["vader_compound_21d_trailing"].reset_index(drop=True)
        trailing_lag = group["vader_compound_21d_trailing_lag1"].reset_index(drop=True)
        expected_lag = raw.shift(1)
        expected_trailing = raw.rolling(window=21, min_periods=1).mean()
        if not _series_equal_with_nan(lag, expected_lag):
            raise ValueError(f"lag1 mismatch for sector {sector}")
        if not _series_equal_with_nan(trailing, expected_trailing):
            raise ValueError(f"trailing mismatch for sector {sector}")
        if not _series_equal_with_nan(trailing_lag, expected_trailing.shift(1)):
            raise ValueError(f"trailing lag mismatch for sector {sector}")


def compound_category(value: float) -> str:
    """Standard VADER compound diagnostic category."""

    if value >= POSITIVE_THRESHOLD:
        return "positive"
    if value <= NEGATIVE_THRESHOLD:
        return "negative"
    return "neutral"


def _assert_coverage_reconciles(frame: pd.DataFrame) -> None:
    with_news = frame["ticker_day_article_count"].notna()
    if not np.allclose(
        frame.loc[with_news, "article_count"].to_numpy(dtype=float),
        frame.loc[with_news, "ticker_day_article_count"].to_numpy(dtype=float),
        atol=1e-12,
    ):
        raise ValueError("article_count does not reconcile with ticker-day headlines")
    if not np.allclose(
        frame.loc[with_news, "covered_tickers"].to_numpy(dtype=float),
        frame.loc[with_news, "ticker_day_covered_tickers"].to_numpy(dtype=float),
        atol=1e-12,
    ):
        raise ValueError("covered_tickers does not reconcile with ticker-day headlines")
    no_news = ~with_news
    if not frame.loc[no_news, "article_count"].eq(0).all():
        raise ValueError("coverage has article counts where ticker-day sentiment is missing")
    if not frame.loc[no_news, "covered_tickers"].eq(0).all():
        raise ValueError("coverage has covered tickers where ticker-day sentiment is missing")


def _validate_sector_index(frame: pd.DataFrame) -> None:
    missing = set(SECTOR_INDEX_COLUMNS).difference(frame.columns)
    if missing:
        raise ValueError(f"sector index missing columns: {sorted(missing)}")
    if frame.duplicated(["date", "sector"]).any():
        raise ValueError("sector index has duplicate date-sector rows")
    sentiment_cols = [
        "vader_compound_raw",
        "vader_compound_lag1",
        "vader_compound_21d_trailing",
        "vader_compound_21d_trailing_lag1",
        "positive_ticker_share",
        "neutral_ticker_share",
        "negative_ticker_share",
    ]
    for column in sentiment_cols:
        values = frame[column].dropna().astype(float)
        if not values.between(-1.0, 1.0).all():
            raise ValueError(f"{column} contains values outside [-1, 1]")
    assert_no_lookahead(frame)


def _normalise_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.tz_localize(None).dt.normalize().astype("datetime64[ns]")


def _fallback_article_id(row: pd.Series) -> str:
    text = "|".join(
        [
            str(row.get("source_date", "")),
            str(row.get("trading_date", "")),
            str(row.get("ticker", "")),
            str(row.get("title", "")),
        ]
    )
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")


def _series_equal_with_nan(left: pd.Series, right: pd.Series, *, atol: float = 1e-12) -> bool:
    both_missing = left.isna() & right.isna()
    comparable = ~both_missing
    return bool(np.allclose(left.loc[comparable], right.loc[comparable], atol=atol, equal_nan=True))
