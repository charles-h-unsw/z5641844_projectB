"""Foundation data-contract tests for Project B."""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src import etl, features  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def foundation():
    equities, eq_summary = etl.load_clean_equities(return_summary=True)
    crypto, cr_summary = etl.load_clean_crypto(return_summary=True)
    news, news_summary = etl.load_clean_news(return_summary=True)
    equity_returns = features.daily_returns(equities)
    crypto_returns = features.daily_returns(crypto)
    combined = features.combined_returns_on_equity_calendar(
        equity_returns,
        crypto_returns,
    )
    sector_map = etl.ticker_sector_map(equities)
    headline_panel, aligned = features.assemble_headline_panel(
        news,
        equities["date"].drop_duplicates(),
    )
    monthly = features.monthly_coverage_lens(
        aligned,
        sector_map,
        equities["date"].drop_duplicates(),
    )
    daily = features.daily_sector_coverage_panel(
        aligned,
        sector_map,
        equities["date"].drop_duplicates(),
    )
    return {
        "equities": equities,
        "crypto": crypto,
        "news": news,
        "eq_summary": eq_summary,
        "cr_summary": cr_summary,
        "news_summary": news_summary,
        "equity_returns": equity_returns,
        "crypto_returns": crypto_returns,
        "combined": combined,
        "sector_map": sector_map,
        "headline_panel": headline_panel,
        "aligned": aligned,
        "monthly": monthly,
        "daily": daily,
    }


def test_clean_schemas_and_sample_bounds(foundation):
    equities = foundation["equities"]
    crypto = foundation["crypto"]
    news = foundation["news"]
    sector_map = foundation["sector_map"]

    assert equities["ticker"].nunique() == 50
    assert crypto["ticker"].nunique() == 10
    assert sector_map["sector"].nunique() == 10
    assert equities["date"].max() <= pd.Timestamp("2023-12-31")
    assert crypto["date"].max() <= pd.Timestamp("2023-12-31")
    assert news["source_date"].max() <= pd.Timestamp("2023-12-31")
    assert {"ticker", "date", "adjClose", "sector"}.issubset(equities.columns)
    assert {"ticker", "date", "adjClose"}.issubset(crypto.columns)
    assert {"source_date", "ticker", "sector", "title", "url", "publisher"}.issubset(news.columns)
    assert equities["date"].dtype == "datetime64[ns]"
    assert crypto["date"].dtype == "datetime64[ns]"
    assert news["source_date"].dtype == "datetime64[ns]"
    assert equities.sort_values(["ticker", "date"]).index.equals(equities.index)
    assert crypto.sort_values(["ticker", "date"]).index.equals(crypto.index)


def test_duplicate_and_integrity_rules(foundation):
    equities = foundation["equities"]
    crypto = foundation["crypto"]
    news = foundation["news"]
    sector_map = foundation["sector_map"]

    assert not equities.duplicated(["ticker", "date"]).any()
    assert not crypto.duplicated(["ticker", "date"]).any()
    assert not news.duplicated(["ticker", "source_date", "title"]).any()
    assert not sector_map.duplicated(["ticker"]).any()
    assert sector_map.groupby("ticker", observed=True)["sector"].nunique().eq(1).all()
    assert (equities[["open", "high", "low", "close", "adjClose"]] > 0).all().all()
    assert (crypto[["open", "high", "low", "close", "adjClose"]] > 0).all().all()
    assert etl.price_integrity_metrics(equities, calendar="equity")["duplicate_ticker_date_rows"] == 0
    assert etl.price_integrity_metrics(crypto, calendar="daily")["duplicate_ticker_date_rows"] == 0
    assert etl.news_integrity_metrics(news)["duplicate_ticker_source_date_title_rows"] == 0


def test_return_construction_contracts(foundation):
    equities = foundation["equities"]
    crypto = foundation["crypto"]
    equity_returns = foundation["equity_returns"]
    crypto_returns = foundation["crypto_returns"]
    combined = foundation["combined"]

    assert len(equity_returns) == equities["date"].nunique() - 1
    assert len(crypto_returns) == crypto["date"].nunique() - 1
    assert not equity_returns.iloc[0].isna().all()
    assert not crypto_returns.iloc[0].isna().all()
    assert equity_returns.shape[1] == 50
    assert crypto_returns.shape[1] == 10
    assert not equity_returns.columns.duplicated().any()
    assert not crypto_returns.columns.duplicated().any()
    assert combined.index.equals(equity_returns.index)
    assert combined.shape[1] == 60
    assert not combined.columns.duplicated().any()

    date = combined.index[20]
    ticker = "BTC-USD"
    assert combined.loc[date, f"CR_{ticker}"] == pytest.approx(
        crypto_returns.loc[date, ticker]
    )


def test_returns_are_grouped_within_ticker_and_before_alignment():
    equity_prices = pd.DataFrame(
        {
            "ticker": ["A", "A"],
            "date": pd.to_datetime(["2023-01-06", "2023-01-09"]),
            "adjClose": [50.0, 51.0],
        }
    )
    crypto_prices = pd.DataFrame(
        {
            "ticker": ["BTC-USD"] * 4,
            "date": pd.to_datetime(["2023-01-06", "2023-01-07", "2023-01-08", "2023-01-09"]),
            "adjClose": [100.0, 200.0, 300.0, 330.0],
        }
    )
    eq_returns = features.daily_returns(equity_prices)
    cr_returns = features.daily_returns(crypto_prices)
    combined = features.combined_returns_on_equity_calendar(eq_returns, cr_returns)

    assert eq_returns.loc[pd.Timestamp("2023-01-09"), "A"] == pytest.approx(0.02)
    assert cr_returns.loc[pd.Timestamp("2023-01-09"), "BTC-USD"] == pytest.approx(0.10)
    assert combined.loc[pd.Timestamp("2023-01-09"), "CR_BTC-USD"] == pytest.approx(0.10)
    assert combined.loc[pd.Timestamp("2023-01-09"), "CR_BTC-USD"] != pytest.approx(2.30)


def test_headline_alignment_contracts(foundation):
    equities = foundation["equities"]
    aligned = foundation["aligned"]
    panel = foundation["headline_panel"]
    trading_dates = set(equities["date"])
    usable = aligned.dropna(subset=["trading_date"])

    assert (usable["trading_date"] >= usable["source_date"]).all()
    assert set(usable["trading_date"]).issubset(trading_dates)
    assert usable["alignment_lag_days"].dropna().ge(0).all()
    assert int(aligned["trading_date"].isna().sum()) == 6
    assert not panel.duplicated(["trading_date", "ticker"]).any()
    assert panel["headline_count"].ge(1).all()
    first_titles = json.loads(panel["headline_titles_json"].iloc[0])
    assert isinstance(first_titles, list)
    assert first_titles
    assert first_titles[0] in panel["combined_headlines"].iloc[0]


def test_headlines_map_weekends_forward_and_trading_days_same_day():
    headlines = pd.DataFrame(
        {
            "source_date": pd.to_datetime(["2023-01-06", "2023-01-07", "2023-01-08", "2023-01-10"]),
            "ticker": ["A"] * 4,
            "sector": ["Tech"] * 4,
            "title": ["Friday", "Saturday", "Sunday", "After sample"],
            "url": ["u"] * 4,
            "publisher": ["p"] * 4,
        }
    )
    aligned = features.align_headlines_to_trading_days(
        headlines,
        pd.to_datetime(["2023-01-06", "2023-01-09"]),
    )

    assert aligned.loc[0, "trading_date"] == pd.Timestamp("2023-01-06")
    assert aligned.loc[1, "trading_date"] == pd.Timestamp("2023-01-09")
    assert aligned.loc[2, "trading_date"] == pd.Timestamp("2023-01-09")
    assert pd.isna(aligned.loc[3, "trading_date"])
    assert aligned.loc[1, "alignment_lag_days"] == 2
    assert aligned.loc[2, "alignment_lag_days"] == 1


def test_news_deduplication_keeps_distinct_same_day_titles():
    raw = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2023-01-02 00:00:00+00:00",
                    "2023-01-02 00:00:00+00:00",
                    "2023-01-02 00:00:00+00:00",
                ],
                utc=True,
            ),
            "ticker": ["A", "A", "A"],
            "sector": ["Tech", "Tech", "Tech"],
            "title": ["Title one", "Title one", "Title two"],
            "url": ["u1", "u1", "u2"],
            "publisher": ["p", None, ""],
        }
    )
    clean, summary = etl.clean_news_panel(raw)

    assert len(clean) == 2
    assert summary.duplicate_rows_removed == 1
    assert clean["title"].tolist() == ["Title one", "Title two"]
    assert "publisher" in clean.columns


def test_monthly_coverage_formula_synthetic_cases():
    sector_map = pd.DataFrame(
        {"ticker": list("ABCDE"), "sector": ["Tech"] * 5}
    )
    dates = pd.to_datetime(["2023-01-03"])
    equal = pd.DataFrame(
        {
            "trading_date": dates.repeat(5),
            "sector": ["Tech"] * 5,
            "ticker": list("ABCDE"),
        }
    )
    concentrated = pd.DataFrame(
        {
            "trading_date": dates.repeat(5),
            "sector": ["Tech"] * 5,
            "ticker": ["A"] * 5,
        }
    )
    empty = pd.DataFrame(columns=["trading_date", "sector", "ticker"])

    equal_result = features.monthly_coverage_lens(equal, sector_map, dates)
    concentrated_result = features.monthly_coverage_lens(concentrated, sector_map, dates)
    empty_result = features.monthly_coverage_lens(empty, sector_map, dates)

    assert equal_result["breadth"].iloc[0] == pytest.approx(1.0)
    assert concentrated_result["breadth"].iloc[0] == pytest.approx(0.2)
    assert np.isnan(empty_result["breadth"].iloc[0])


def test_coverage_lens_bundle_contracts(foundation):
    equities = foundation["equities"]
    monthly = foundation["monthly"]
    daily = foundation["daily"]

    assert len(monthly) == 48 * 10
    assert not monthly.duplicated(["month", "sector"]).any()
    valid = monthly.loc[monthly["article_count"].gt(0), "breadth"]
    assert valid.between(0.2, 1.0).all()

    assert len(daily) == equities["date"].nunique() * 10
    assert not daily.duplicated(["trading_date", "sector"]).any()
    assert {"article_count", "covered_tickers", "coverage_share", "breadth", "has_news"}.issubset(daily.columns)
    no_news = daily.loc[~daily["has_news"]]
    assert no_news["article_count"].eq(0).all()
    assert no_news["breadth"].isna().all()


def test_rolling_daily_coverage_uses_no_future_information():
    sector_map = pd.DataFrame(
        {"ticker": list("ABCDE"), "sector": ["Tech"] * 5}
    )
    dates = pd.to_datetime(
        ["2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]
    )
    aligned = pd.DataFrame(
        {
            "trading_date": [pd.Timestamp("2023-01-05")],
            "sector": ["Tech"],
            "ticker": ["E"],
        }
    )
    daily = features.daily_sector_coverage_panel(
        aligned,
        sector_map,
        dates,
        window=3,
    )
    before_news = daily.loc[daily["trading_date"].eq(pd.Timestamp("2023-01-04"))].iloc[0]
    on_news = daily.loc[daily["trading_date"].eq(pd.Timestamp("2023-01-05"))].iloc[0]

    assert before_news["rolling_21d_article_count"] == 0
    assert before_news["rolling_21d_covered_tickers"] == 0
    assert np.isnan(before_news["rolling_21d_breadth"])
    assert on_news["rolling_21d_article_count"] == 1
    assert on_news["rolling_21d_covered_tickers"] == 1
    assert on_news["rolling_21d_breadth"] == pytest.approx(0.2)


def test_foundation_build_is_project_b_only():
    build_source = (ROOT / "scripts" / "build_foundation.py").read_text(encoding="utf-8")
    etl_source = (ROOT / "src" / "etl.py").read_text(encoding="utf-8")

    forbidden = [
        "z5641844_projectA",
        "../z5641844_projectA",
        "ROOT.parent",
        "combined_returns_panel.csv",
        "news_coverage_breadth.csv",
    ]
    for token in forbidden:
        assert token not in build_source

    assert "from src import etl, features" in build_source
    assert "from src import data_access" in etl_source
    assert "data_access.load_equity_prices()" in etl_source
    assert "data_access.load_crypto_prices()" in etl_source
    assert "data_access.load_news_headlines()" in etl_source
    assert "foundation_reconciliation.csv" not in build_source
