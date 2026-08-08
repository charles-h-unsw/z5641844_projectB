from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import sentiment  # noqa: E402


class RecordingAnalyzer:
    def __init__(self):
        self.seen: list[str] = []

    def polarity_scores(self, text: str) -> dict[str, float]:
        self.seen.append(text)
        lower = text.lower()
        compound = 0.8 if "excellent" in lower else (-0.8 if "terrible" in lower else 0.0)
        return {
            "neg": max(-compound, 0.0),
            "neu": 0.0 if compound else 1.0,
            "pos": max(compound, 0.0),
            "compound": compound,
        }


def _headline_panel() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_date": pd.to_datetime(["2023-01-02", "2023-01-02", "2023-01-03"]),
            "trading_date": pd.to_datetime(["2023-01-02", "2023-01-02", "2023-01-03"]),
            "ticker": ["AAA", "AAA", "BBB"],
            "sector": ["Tech", "Tech", "Tech"],
            "title": ["Excellent growth!", "Terrible loss.", "Flat update"],
            "url": ["a", "b", "c"],
        }
    )


def _coverage() -> pd.DataFrame:
    dates = pd.to_datetime(["2023-01-02", "2023-01-03", "2023-01-04"])
    return pd.DataFrame(
        {
            "trading_date": dates,
            "sector": ["Tech"] * 3,
            "article_count": [2, 1, 0],
            "covered_tickers": [1, 1, 0],
            "coverage_share": [0.2, 0.2, 0.0],
            "breadth": [0.2, 0.2, np.nan],
            "has_news": [True, True, False],
        }
    )


def test_headline_scoring_signs_bounds_and_text_preservation():
    analyzer = RecordingAnalyzer()
    scores = sentiment.score_headlines(_headline_panel(), analyzer=analyzer, allow_download=False)
    assert scores.loc[scores["title"].str.contains("Excellent"), "vader_compound"].iloc[0] > 0
    assert scores.loc[scores["title"].str.contains("Terrible"), "vader_compound"].iloc[0] < 0
    assert scores["vader_compound"].between(-1, 1).all()
    assert "Excellent growth!" in analyzer.seen


def test_missing_titles_are_not_scored_and_crypto_is_not_added():
    panel = _headline_panel()
    panel.loc[len(panel)] = [pd.Timestamp("2023-01-03"), pd.Timestamp("2023-01-03"), "CCC", "Tech", None, "d"]
    scores = sentiment.score_headlines(panel, analyzer=RecordingAnalyzer(), allow_download=False)
    assert scores["title"].notna().all()
    assert len(scores) == 3
    assert not scores["ticker"].str.startswith("CR_").any()


def test_ticker_day_aggregation_is_correct_and_unique():
    scores = sentiment.score_headlines(_headline_panel(), analyzer=RecordingAnalyzer(), allow_download=False)
    td = sentiment.ticker_day_sentiment(scores)
    aaa = td.loc[td["ticker"].eq("AAA")].iloc[0]
    assert aaa["headline_count"] == 2
    assert aaa["mean_compound"] == pytest.approx(0.0)
    assert not td.duplicated(["trading_date", "ticker"]).any()


def test_sector_equal_weights_tickers_not_articles():
    td = pd.DataFrame(
        {
            "trading_date": pd.to_datetime(["2023-01-02", "2023-01-02"]),
            "ticker": ["A", "B"],
            "sector": ["Tech", "Tech"],
            "headline_count": [20, 1],
            "mean_compound": [0.8, -0.2],
        }
    )
    coverage = _coverage().iloc[[0]].copy()
    coverage["article_count"] = 21
    coverage["covered_tickers"] = 2
    coverage["coverage_share"] = 0.4
    coverage["breadth"] = 0.4
    index = sentiment.build_sector_sentiment_index(td, coverage)
    assert index["vader_compound_raw"].iloc[0] == pytest.approx(0.3)


def test_missing_news_is_nan_while_genuine_zero_is_zero():
    scores = sentiment.score_headlines(_headline_panel(), analyzer=RecordingAnalyzer(), allow_download=False)
    td = sentiment.ticker_day_sentiment(scores)
    index = sentiment.build_sector_sentiment_index(td, _coverage())
    day1 = index.loc[index["date"].eq(pd.Timestamp("2023-01-02"))].iloc[0]
    day3 = index.loc[index["date"].eq(pd.Timestamp("2023-01-04"))].iloc[0]
    assert day1["vader_compound_raw"] == pytest.approx(0.0)
    assert pd.isna(day3["vader_compound_raw"])
    assert not bool(day3["has_news"])


def test_coverage_reconciles_exactly():
    scores = sentiment.score_headlines(_headline_panel(), analyzer=RecordingAnalyzer(), allow_download=False)
    td = sentiment.ticker_day_sentiment(scores)
    index = sentiment.build_sector_sentiment_index(td, _coverage())
    for column in ["article_count", "covered_tickers", "coverage_share", "breadth"]:
        left = index[column].reset_index(drop=True)
        right = _coverage()[column].reset_index(drop=True)
        assert np.allclose(left.fillna(-999), right.fillna(-999))


def test_full_grid_lag_includes_no_news_days_and_uses_no_future():
    raw = pd.DataFrame(
        {
            "date": pd.to_datetime(["2023-01-02", "2023-01-03", "2023-01-04"]),
            "sector": ["Tech"] * 3,
            "vader_compound_raw": [0.2, np.nan, 0.9],
        }
    )
    out = sentiment.add_lookahead_safe_fields(raw)
    assert out.loc[1, "vader_compound_lag1"] == pytest.approx(0.2)
    assert pd.isna(out.loc[2, "vader_compound_lag1"])
    changed = raw.copy()
    changed.loc[2, "vader_compound_raw"] = -0.9
    changed_out = sentiment.add_lookahead_safe_fields(changed)
    assert changed_out.loc[1, "vader_compound_lag1"] == out.loc[1, "vader_compound_lag1"]


def test_saturday_and_monday_information_first_usable_tuesday():
    dates = pd.to_datetime(["2023-01-06", "2023-01-09", "2023-01-10"])
    raw = pd.DataFrame(
        {
            "date": dates,
            "sector": ["Tech"] * 3,
            "vader_compound_raw": [np.nan, 0.4, 0.1],
        }
    )
    out = sentiment.add_lookahead_safe_fields(raw)
    assert out.loc[out["date"].eq(pd.Timestamp("2023-01-09")), "vader_compound_lag1"].isna().all()
    assert out.loc[out["date"].eq(pd.Timestamp("2023-01-10")), "vader_compound_lag1"].iloc[0] == pytest.approx(0.4)


def test_sentiment_artifact_schema_when_built():
    path = ROOT / "results" / "data" / "sector_sentiment_index.csv"
    if not path.exists() or path.stat().st_size == 0:
        pytest.skip("run scripts/run_part_b.py to build the final sentiment artifact")
    frame = pd.read_csv(path)
    assert set(sentiment.SECTOR_INDEX_COLUMNS).issubset(frame.columns)
    assert not frame.duplicated(["date", "sector"]).any()
    assert frame["sector"].nunique() == 10
