"""Build and validate Project B foundation artifacts.

This script stops at the Station 1-2 foundation. It does not score sentiment,
optimise portfolios, backtest funds, write final Part B modelling artifacts, or
touch the Streamlit app.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import etl, features  # noqa: E402

TABLES = ROOT / "results" / "tables"
DATA = ROOT / "results" / "data"


def _write_csv(frame: pd.DataFrame, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, float_format="%.12g")


def _date_span(frame: pd.DataFrame, column: str | None = None) -> tuple[str, str]:
    if column is None:
        dates = pd.DatetimeIndex(pd.to_datetime(frame.index))
    else:
        dates = pd.DatetimeIndex(pd.to_datetime(frame[column].dropna()))
    return dates.min().date().isoformat(), dates.max().date().isoformat()


def _inventory(
    equities: pd.DataFrame,
    crypto: pd.DataFrame,
    news: pd.DataFrame,
    equity_returns: pd.DataFrame,
    crypto_returns: pd.DataFrame,
    combined: pd.DataFrame,
    sector_map: pd.DataFrame,
    aligned: pd.DataFrame,
    headline_panel: pd.DataFrame,
    daily_coverage: pd.DataFrame,
    monthly_coverage: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def add(
        dataset: str,
        row_count: int,
        start: str | None,
        end: str | None,
        entities: int | None,
        key: str,
        columns: list[str],
        note: str,
    ) -> None:
        rows.append(
            {
                "dataset": dataset,
                "rows": row_count,
                "start_date": start or "",
                "end_date": end or "",
                "entities": "" if entities is None else entities,
                "row_key": key,
                "columns": ";".join(columns),
                "note": note,
            }
        )

    add(
        "clean_equity_prices",
        len(equities),
        *_date_span(equities, "date"),
        equities["ticker"].nunique(),
        "ticker,date",
        equities.columns.tolist(),
        "official equity data cleaned; outliers retained",
    )
    add(
        "clean_crypto_prices",
        len(crypto),
        *_date_span(crypto, "date"),
        crypto["ticker"].nunique(),
        "ticker,date",
        crypto.columns.tolist(),
        "official crypto data cleaned and capped at 2023-12-31",
    )
    add(
        "clean_headlines",
        len(news),
        *_date_span(news, "source_date"),
        news["ticker"].nunique(),
        "ticker,source_date,title",
        news.columns.tolist(),
        "exact duplicate headlines removed; raw title text retained",
    )
    add(
        "equity_returns",
        len(equity_returns),
        *_date_span(equity_returns),
        len(equity_returns.columns),
        "date",
        equity_returns.columns.astype(str).tolist(),
        "wide adjusted-close simple returns; first all-NaN row dropped",
    )
    add(
        "crypto_returns_native",
        len(crypto_returns),
        *_date_span(crypto_returns),
        len(crypto_returns.columns),
        "date",
        crypto_returns.columns.astype(str).tolist(),
        "wide native-calendar crypto returns; weekend returns retained",
    )
    add(
        "combined_returns_on_equity_calendar",
        len(combined),
        *_date_span(combined),
        len(combined.columns),
        "date",
        combined.columns.astype(str).tolist(),
        "native crypto returns left-joined onto the equity-return calendar",
    )
    add(
        "ticker_sector_map",
        len(sector_map),
        None,
        None,
        sector_map["sector"].nunique(),
        "ticker",
        sector_map.columns.tolist(),
        "one sector per equity ticker; crypto has no sector assignment",
    )
    add(
        "aligned_headlines",
        len(aligned),
        *_date_span(aligned, "source_date"),
        aligned["ticker"].nunique(),
        "source row",
        aligned.columns.tolist(),
        "same-or-next equity trading-day mapping; outside-calendar rows retained",
    )
    add(
        "ticker_day_news_panel",
        len(headline_panel),
        *_date_span(headline_panel, "trading_date"),
        headline_panel["ticker"].nunique(),
        "trading_date,ticker",
        headline_panel.columns.tolist(),
        "full in-memory panel; not written as a compact validation artifact",
    )
    add(
        "sector_coverage_daily",
        len(daily_coverage),
        *_date_span(daily_coverage, "trading_date"),
        daily_coverage["sector"].nunique(),
        "trading_date,sector",
        daily_coverage.columns.tolist(),
        "all equity trading-date-sector combinations",
    )
    add(
        "sector_coverage_monthly",
        len(monthly_coverage),
        monthly_coverage["month"].min(),
        monthly_coverage["month"].max(),
        monthly_coverage["sector"].nunique(),
        "month,sector",
        monthly_coverage.columns.tolist(),
        "monthly Signal Mosaic Coverage Lens",
    )
    return pd.DataFrame(rows)


def _integrity_checks(
    equities: pd.DataFrame,
    crypto: pd.DataFrame,
    news: pd.DataFrame,
    summaries: list[etl.CleaningSummary],
    equity_returns: pd.DataFrame,
    crypto_returns: pd.DataFrame,
    combined: pd.DataFrame,
    sector_map: pd.DataFrame,
    aligned: pd.DataFrame,
    headline_panel: pd.DataFrame,
    daily_coverage: pd.DataFrame,
    monthly_coverage: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def add(check: str, value: object, passed: bool, detail: str) -> None:
        rows.append(
            {
                "check": check,
                "value": value,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    eq_summary, cr_summary, news_summary = summaries
    eq_metrics = etl.price_integrity_metrics(equities, calendar="equity")
    cr_metrics = etl.price_integrity_metrics(crypto, calendar="daily")
    news_metrics = etl.news_integrity_metrics(news)
    mapping = etl.sector_mapping_issues(equities, news)

    add("equity_tickers", equities["ticker"].nunique(), equities["ticker"].nunique() == 50, "frozen bundle expectation")
    add("crypto_tickers", crypto["ticker"].nunique(), crypto["ticker"].nunique() == 10, "frozen bundle expectation")
    add("equity_sectors", sector_map["sector"].nunique(), sector_map["sector"].nunique() == 10, "frozen bundle expectation")
    add("crypto_rows_after_2023_12_31_removed", cr_summary.rows_outside_sample, cr_summary.rows_outside_sample == 10, "documented stray 2024-01-01 rows")
    add("news_exact_duplicates_removed", news_summary.duplicate_rows_removed, news_summary.duplicate_rows_removed == 2847, "ticker-source_date-title duplicate rule")
    add("equity_duplicate_keys", eq_metrics["duplicate_ticker_date_rows"], eq_metrics["duplicate_ticker_date_rows"] == 0, "ticker-date unique")
    add("crypto_duplicate_keys", cr_metrics["duplicate_ticker_date_rows"], cr_metrics["duplicate_ticker_date_rows"] == 0, "ticker-date unique")
    add("news_duplicate_keys", news_metrics["duplicate_ticker_source_date_title_rows"], news_metrics["duplicate_ticker_source_date_title_rows"] == 0, "ticker-source_date-title unique")
    add("nonpositive_equity_price_rows", eq_metrics["nonpositive_price_rows"], eq_metrics["nonpositive_price_rows"] == 0, "required OHLC adjusted-close fields")
    add("nonpositive_crypto_price_rows", cr_metrics["nonpositive_price_rows"], cr_metrics["nonpositive_price_rows"] == 0, "required OHLC adjusted-close fields")
    add("equity_return_rows", len(equity_returns), len(equity_returns) == equities["date"].nunique() - 1, "first all-NaN return date is dropped")
    add("crypto_return_rows", len(crypto_returns), len(crypto_returns) == crypto["date"].nunique() - 1, "native 7-day calendar")
    add("combined_index_equals_equity_returns", str(combined.index.equals(equity_returns.index)), combined.index.equals(equity_returns.index), "combined panel uses equity-return calendar")
    add("combined_columns", combined.shape[1], combined.shape[1] == 60, "50 equities plus 10 cryptos")
    add("news_unknown_tickers", mapping["news_unknown_ticker_rows"], mapping["news_unknown_ticker_rows"] == 0, "news tickers in equity universe")
    add("news_sector_mismatches", mapping["news_sector_mismatch_rows"], mapping["news_sector_mismatch_rows"] == 0, "news sectors match price universe")
    add("headline_outside_calendar_rows", int(aligned["trading_date"].isna().sum()), int(aligned["trading_date"].isna().sum()) == 6, "end-of-sample outside-calendar rows are explicit")
    add("ticker_day_news_unique_key", int(headline_panel.duplicated(["trading_date", "ticker"]).sum()), not headline_panel.duplicated(["trading_date", "ticker"]).any(), "full panel key")
    add("daily_coverage_rows", len(daily_coverage), len(daily_coverage) == equities["date"].nunique() * 10, "all equity-date-sector combinations")
    add("monthly_coverage_rows", len(monthly_coverage), len(monthly_coverage) == 48 * 10, "48 months x 10 sectors")
    add("monthly_coverage_key", int(monthly_coverage.duplicated(["month", "sector"]).sum()), not monthly_coverage.duplicated(["month", "sector"]).any(), "month-sector unique")
    add("daily_coverage_key", int(daily_coverage.duplicated(["trading_date", "sector"]).sum()), not daily_coverage.duplicated(["trading_date", "sector"]).any(), "date-sector unique")
    return pd.DataFrame(rows)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)

    equities, eq_summary = etl.load_clean_equities(return_summary=True)
    crypto, cr_summary = etl.load_clean_crypto(return_summary=True)
    news, news_summary = etl.load_clean_news(return_summary=True)
    trading_dates = equities["date"].drop_duplicates()
    sector_map = etl.ticker_sector_map(equities)

    equity_returns = features.daily_returns(equities)
    crypto_returns = features.daily_returns(crypto)
    combined = features.combined_returns_on_equity_calendar(
        equity_returns,
        crypto_returns,
    )
    headline_panel, aligned = features.assemble_headline_panel(news, trading_dates)
    monthly_coverage = features.monthly_coverage_lens(aligned, sector_map, trading_dates)
    daily_coverage = features.daily_sector_coverage_panel(aligned, sector_map, trading_dates)

    inventory = _inventory(
        equities,
        crypto,
        news,
        equity_returns,
        crypto_returns,
        combined,
        sector_map,
        aligned,
        headline_panel,
        daily_coverage,
        monthly_coverage,
    )
    integrity = _integrity_checks(
        equities,
        crypto,
        news,
        [eq_summary, cr_summary, news_summary],
        equity_returns,
        crypto_returns,
        combined,
        sector_map,
        aligned,
        headline_panel,
        daily_coverage,
        monthly_coverage,
    )
    _write_csv(inventory, TABLES / "foundation_inventory.csv")
    _write_csv(integrity, TABLES / "foundation_integrity_checks.csv")
    _write_csv(sector_map, DATA / "ticker_sector_map.csv")
    _write_csv(daily_coverage, DATA / "sector_coverage_daily.csv")
    _write_csv(monthly_coverage, DATA / "sector_coverage_monthly.csv")

    print("foundation schemas:")
    for _, row in inventory.iterrows():
        print(
            f" - {row['dataset']}: rows={row['rows']}, "
            f"span={row['start_date'] or 'n/a'} to {row['end_date'] or 'n/a'}, "
            f"key={row['row_key']}"
        )
    print("integrity:", integrity["status"].value_counts().to_dict())
    if not integrity["status"].eq("PASS").all():
        failed = integrity.loc[~integrity["status"].eq("PASS")]
        raise SystemExit(f"foundation integrity checks failed:\n{failed.to_string(index=False)}")
    print("wrote:")
    for path in [
        TABLES / "foundation_inventory.csv",
        TABLES / "foundation_integrity_checks.csv",
        DATA / "ticker_sector_map.csv",
        DATA / "sector_coverage_daily.csv",
        DATA / "sector_coverage_monthly.csv",
    ]:
        print(" -", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
