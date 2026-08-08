"""Signal Mosaic Streamlit investment prototype."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.app_charts import (
    active_weight_chart,
    attenuation_chart,
    correlation_heatmap,
    coverage_chart,
    drawdown_chart,
    growth_chart,
    holdings_chart,
    metric_bar_chart,
    risk_return_chart,
    sentiment_chart,
)
from src.app_copy import LIMITATIONS, METHOD_DESCRIPTIONS, SECTION_NAMES
from src.app_data import AppDataError, load_app_data
from src.app_logic import (
    AllocationError,
    allocation_metrics,
    allocation_return_history,
    calendar_label,
    compact_month_range,
    format_number,
    format_percent,
    fusion_summary,
    latest_holdings_for_fund,
    monthly_fund_returns,
    normalise_weights,
    overview_highlights,
    return_history_for_fund,
    selected_metric_table,
    table_to_csv_bytes,
)


PROJECT_ROOT = Path(__file__).resolve().parent

FUND_SHELF_LABELS = {
    "fund_name": "Fund",
    "asset_family": "Asset family",
    "method": "Strategy",
    "annualised_return_net": "Net annualised return",
    "annualised_volatility_net": "Net volatility",
    "Sharpe_net": "Net Sharpe",
    "maximum_drawdown_net": "Maximum drawdown",
}

COMPARISON_LABELS = {
    **FUND_SHELF_LABELS,
    "fund_id": "Fund ID",
    "cumulative_return_net": "Cumulative net return",
    "average_rebalance_turnover": "Average turnover",
}

HOLDINGS_LABELS = {
    "rebalance_date": "Latest rebalance",
    "fund_id": "Fund ID",
    "fund_name": "Fund",
    "asset_family": "Asset family",
    "method": "Strategy",
    "asset": "Holding",
    "asset_class": "Asset class",
    "sector": "Sector",
    "pretrade_weight": "Pre-trade weight",
    "target_weight": "Target weight",
    "is_latest_rebalance": "Latest rebalance flag",
}

SENTIMENT_LABELS = {
    "sector": "Sector",
    "vader_compound_lag1": "Lagged sentiment",
    "coverage_share": "Coverage share",
    "breadth": "Breadth",
    "article_count": "Article count",
    "signal_available": "Signal available",
}

FUSION_LABELS = {
    "fund_name": "Fund",
    "annualised_return_net": "Net annualised return",
    "annualised_volatility_net": "Net volatility",
    "Sharpe_net": "Net Sharpe",
    "maximum_drawdown_net": "Maximum drawdown",
    "cumulative_return_net": "Cumulative net return",
}


def rename_for_display(frame: pd.DataFrame, labels: dict[str, str]) -> pd.DataFrame:
    return frame.rename(columns={key: value for key, value in labels.items() if key in frame.columns})


def setup_page() -> None:
    st.set_page_config(page_title="Signal Mosaic", page_icon=None, layout="wide")
    st.markdown(
        """
        <style>
        :root {
            --sm-navy: #17233c;
            --sm-ink: #22304f;
            --sm-offwhite: #f7f3eb;
            --sm-panel: #fffaf2;
            --sm-teal: #2f7f7a;
            --sm-burgundy: #9a3f5f;
            --sm-gold: #b58b2b;
            --sm-muted: #6b7280;
        }
        html, body, [data-testid="stAppViewContainer"] {
            background: var(--sm-offwhite);
            color: var(--sm-ink);
        }
        .signal-brand {
            font-size: 0.82rem;
            letter-spacing: 0;
            text-transform: uppercase;
            color: var(--sm-burgundy);
            font-weight: 700;
        }
        .signal-hero {
            padding: 1.25rem 0 0.75rem 0;
            border-bottom: 1px solid #e1dbd0;
            margin-bottom: 1.25rem;
        }
        .signal-hero h1 {
            color: var(--sm-navy);
            font-size: 3rem;
            line-height: 1.05;
            margin: 0.15rem 0 0.4rem 0;
        }
        .signal-hero p, .signal-copy {
            color: var(--sm-ink);
            font-size: 1.02rem;
            line-height: 1.55;
            max-width: 76rem;
        }
        .signal-note {
            border-left: 4px solid var(--sm-teal);
            padding: 0.55rem 0.9rem;
            background: #fffaf2;
            color: var(--sm-ink);
            margin: 0.75rem 0 1rem 0;
        }
        .signal-warning {
            border-left: 4px solid var(--sm-burgundy);
            padding: 0.55rem 0.9rem;
            background: #fff7f7;
            color: var(--sm-ink);
            margin: 0.75rem 0 1rem 0;
        }
        div[data-testid="stMetric"] {
            background: #fffaf2;
            border: 1px solid #e5ded2;
            padding: 0.8rem 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_or_stop() -> dict[str, pd.DataFrame]:
    try:
        return load_app_data(str(PROJECT_ROOT))
    except AppDataError as exc:
        command = "python scripts/" + "run_" + "part_b.py"
        st.error(
            "Signal Mosaic could not load the required precomputed artifacts. "
            f"Build the analytical pipeline first with `{command}` from the Project B root, then reopen the app.\n\n"
            f"Details: {exc}"
        )
        st.stop()


def section_header(title: str, body: str | None = None) -> None:
    st.markdown(f"### {title}")
    if body:
        st.markdown(f"<div class='signal-copy'>{body}</div>", unsafe_allow_html=True)


def overview_page(data: dict[str, pd.DataFrame]) -> None:
    metrics = data["metrics"]
    fund_returns = data["fund_returns"]
    sentiment = data["sector_sentiment"]
    pipeline = data["pipeline_validation"]
    fusion = data["fusion_before_after"]
    predictive = data["fusion_predictive"]

    st.markdown(
        """
        <div class="signal-hero">
            <div class="signal-brand">Signal Mosaic</div>
            <p>Systematic multi-asset funds, with the evidence behind the signal in view.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title("Signal Mosaic")

    cols = st.columns(4)
    cols[0].metric("Funds", f"{metrics['fund_id'].nunique():.0f}")
    cols[1].metric("Equity sectors", f"{sentiment['sector'].nunique():.0f}")
    cols[2].metric("Out-of-sample window", compact_month_range(fund_returns["date"].min(), fund_returns["date"].max()))
    cols[3].metric("Pipeline checks passed", f"{(pipeline['status'] == 'PASS').sum():.0f}")

    st.markdown(
        f"<div class='signal-note'>{metrics['fund_id'].nunique():.0f} funds cover equity, crypto, combined, and sentiment-overlay strategies. The Coverage Lens shows whether sector sentiment rests on broad or narrow headline evidence.</div>",
        unsafe_allow_html=True,
    )

    section_header("Fund Shelf")
    family = st.selectbox("Filter by asset family", ["All", *sorted(metrics["asset_family"].unique())], key="overview_family")
    shelf = metrics.copy()
    if family != "All":
        shelf = shelf.loc[shelf["asset_family"] == family]
    display = shelf[
        [
            "fund_name",
            "asset_family",
            "method",
            "annualised_return_net",
            "annualised_volatility_net",
            "Sharpe_net",
            "maximum_drawdown_net",
        ]
    ].copy()
    display = rename_for_display(display, FUND_SHELF_LABELS)
    st.dataframe(
        display.style.format(
            {
                "Net annualised return": "{:.1%}",
                "Net volatility": "{:.1%}",
                "Net Sharpe": "{:.2f}",
                "Maximum drawdown": "{:.1%}",
            }
        ),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fund": st.column_config.TextColumn("Fund", width="medium"),
            "Asset family": st.column_config.TextColumn("Asset family", width="small"),
            "Strategy": st.column_config.TextColumn("Strategy", width="medium"),
        },
    )

    section_header("Evidence Highlights")
    for line in overview_highlights(metrics, fusion):
        st.markdown(f"- {line}")
    for line in fusion_summary(fusion, predictive):
        st.markdown(f"- {line}")

    section_header("Investor Path")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown("**Compare funds**\n\nSelect a focused set of funds and compare net returns, risk, Sharpe, and drawdowns.")
    c2.markdown("**Inspect a fact sheet**\n\nOpen one fund to see assumptions, return history, drawdown, and latest holdings.")
    c3.markdown("**Build an allocation**\n\nCombine precomputed funds on a common monthly calendar for an illustrative fund-of-funds view.")
    c4.markdown("**Examine coverage**\n\nView sector sentiment with coverage share, breadth, and the fusion outcome.")

    st.markdown(
        "<div class='signal-warning'>Prototype for educational analysis only. Results are historical 2021-2023 out-of-sample backtests and are not personal financial advice. Past performance does not guarantee future performance.</div>",
        unsafe_allow_html=True,
    )


def compare_funds_page(data: dict[str, pd.DataFrame]) -> None:
    section_header(
        "Compare Funds",
        "Compare two to six precomputed funds. Crypto funds use a native seven-day calendar; equity and combined funds use the equity trading calendar.",
    )
    metrics = data["metrics"].sort_values("fund_name")
    returns = data["fund_returns"]
    families = st.multiselect("Asset-family filter", sorted(metrics["asset_family"].unique()), default=sorted(metrics["asset_family"].unique()))
    methods = st.multiselect("Method filter", sorted(metrics["method"].unique()), default=sorted(metrics["method"].unique()))
    eligible = metrics.loc[metrics["asset_family"].isin(families) & metrics["method"].isin(methods)]
    default_ids = [fund_id for fund_id in ["equity_equal_weight", "crypto_equal_weight", "combined_equal_weight", "equity_sentiment_coverage_gated"] if fund_id in set(eligible["fund_id"])]
    selected = st.multiselect(
        "Funds to show",
        eligible["fund_id"].tolist(),
        default=default_ids[:6],
        format_func=lambda fund_id: metrics.set_index("fund_id").loc[fund_id, "fund_name"],
    )
    if not 2 <= len(selected) <= 6:
        st.warning("Select between two and six funds for a readable comparison.")
        return

    table = selected_metric_table(metrics, selected)
    table_display = rename_for_display(table, COMPARISON_LABELS)
    st.dataframe(
        table_display.style.format(
            {
                "Net annualised return": "{:.1%}",
                "Net volatility": "{:.1%}",
                "Net Sharpe": "{:.2f}",
                "Maximum drawdown": "{:.1%}",
                "Cumulative net return": "{:.1%}",
                "Average turnover": "{:.1%}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button("Download comparison table", table_to_csv_bytes(table), "signal_mosaic_fund_comparison.csv", "text/csv")

    st.pyplot(growth_chart(returns, selected, "Net growth of $1 for selected funds", "Signal Mosaic fund_returns.csv"))
    cols = st.columns(2)
    with cols[0]:
        st.pyplot(risk_return_chart(table, "Net return and volatility"))
    with cols[1]:
        st.pyplot(metric_bar_chart(table, "Sharpe_net", "Net Sharpe comparison", "Sharpe ratio"))
    st.pyplot(metric_bar_chart(table, "maximum_drawdown_net", "Maximum drawdown comparison", "Net maximum drawdown", percent=True))

    calendars = sorted({calendar_label(row["asset_family"]) for _, row in table.iterrows()})
    st.markdown("**Calendar note:** " + " | ".join(calendars))
    for line in overview_highlights(table, data["fusion_before_after"]):
        st.markdown(f"- {line}")


def fact_sheet_page(data: dict[str, pd.DataFrame]) -> None:
    metrics = data["metrics"].sort_values("fund_name")
    returns = data["fund_returns"]
    holdings = data["latest_holdings"]
    design = data["backtest_design"]

    fund_id = st.selectbox("Select fund", metrics["fund_id"].tolist(), format_func=lambda item: metrics.set_index("fund_id").loc[item, "fund_name"])
    record = metrics.loc[metrics["fund_id"] == fund_id].iloc[0]
    fund_returns = return_history_for_fund(returns, fund_id)
    fund_holdings = latest_holdings_for_fund(holdings, fund_id)
    design_record = design.loc[design["fund_id"] == fund_id]
    if design_record.empty and record["asset_family"] == "Equity":
        design_record = design.loc[design["fund_id"] == "equity_equal_weight"]

    section_header(record["fund_name"], f"{record['asset_family']} | {record['method']} | {calendar_label(record['asset_family'])}")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Net annual return", format_percent(record["annualised_return_net"]))
    c2.metric("Net volatility", format_percent(record["annualised_volatility_net"]))
    c3.metric("Net Sharpe", format_number(record["Sharpe_net"]))
    c4.metric("Max drawdown", format_percent(record["maximum_drawdown_net"]))
    c5.metric("Cumulative net", format_percent(record["cumulative_return_net"]))
    c6.metric("Avg turnover", format_percent(record["average_rebalance_turnover"]))

    st.markdown(f"**First live date:** {pd.to_datetime(record['first_live_date']).date()}  |  **Last date:** {pd.to_datetime(record['end_date']).date()}  |  **Annualisation:** {int(record['annualisation_factor'])}")
    st.pyplot(growth_chart(returns, [fund_id], f"{record['fund_name']} net growth of $1", "Signal Mosaic fund_returns.csv"))
    st.pyplot(drawdown_chart(returns, [fund_id], f"{record['fund_name']} net drawdown", "Signal Mosaic fund_returns.csv"))

    section_header("Current Holdings")
    st.pyplot(holdings_chart(fund_holdings, "Largest latest target holdings"))
    aggregate_cols = ["asset_class"] if record["asset_family"] == "Crypto" else ["sector"]
    agg = fund_holdings.groupby(aggregate_cols, dropna=False, observed=True)["target_weight"].sum().reset_index()
    agg_display = rename_for_display(agg, HOLDINGS_LABELS)
    st.dataframe(agg_display.style.format({"Target weight": "{:.1%}"}), use_container_width=True, hide_index=True)
    holdings_display = rename_for_display(
        fund_holdings[
            [
                "rebalance_date",
                "asset",
                "asset_class",
                "sector",
                "pretrade_weight",
                "target_weight",
            ]
        ],
        HOLDINGS_LABELS,
    )
    st.dataframe(
        holdings_display.style.format({"Target weight": "{:.2%}", "Pre-trade weight": "{:.2%}"}),
        use_container_width=True,
        hide_index=True,
    )

    section_header("Method Summary")
    st.markdown(METHOD_DESCRIPTIONS.get(record["method"], "Precomputed rules-based fund."))
    if not design_record.empty:
        d = design_record.iloc[0]
        st.markdown(
            f"Expanding-window backtest; {d.get('rebalance_rule', 'monthly rebalance')}; past information only; "
            "10 basis-point one-way turnover cost after inception; rf = 0 for Sharpe. "
            f"Calendar: {d.get('calendar', calendar_label(record['asset_family']))}."
        )
    else:
        st.markdown("Expanding-window equity overlay using the same monthly schedule and cost assumption as Equity Equal Weight.")

    st.download_button("Download selected fund returns", table_to_csv_bytes(fund_returns), f"{fund_id}_returns.csv", "text/csv")
    st.download_button("Download selected latest holdings", table_to_csv_bytes(fund_holdings), f"{fund_id}_latest_holdings.csv", "text/csv")


def allocation_page(data: dict[str, pd.DataFrame]) -> None:
    section_header(
        "Allocation Studio",
        "Build an illustrative monthly fund-of-funds allocation from precomputed net fund returns. This is not an additional managed fund.",
    )
    metrics = data["metrics"].sort_values("fund_name")
    returns = data["fund_returns"]
    default = ["equity_equal_weight", "combined_equal_weight", "crypto_equal_weight"]
    selected = st.multiselect(
        "Select two to five funds",
        metrics["fund_id"].tolist(),
        default=[fund_id for fund_id in default if fund_id in set(metrics["fund_id"])],
        format_func=lambda fund_id: metrics.set_index("fund_id").loc[fund_id, "fund_name"],
    )
    if not 2 <= len(selected) <= 5:
        st.warning("Select between two and five funds.")
        return

    input_weights: dict[str, float] = {}
    cols = st.columns(len(selected))
    default_weight = 100.0 / len(selected)
    name_map = metrics.set_index("fund_id")["fund_name"].to_dict()
    for idx, fund_id in enumerate(selected):
        input_weights[fund_id] = cols[idx].number_input(name_map[fund_id], min_value=0.0, value=default_weight, step=5.0)

    try:
        weights = normalise_weights(input_weights)
        monthly = monthly_fund_returns(returns, selected)
        history = allocation_return_history(monthly, weights.to_dict())
        stats = allocation_metrics(history)
    except AllocationError as exc:
        st.error(str(exc))
        return

    weight_table = pd.DataFrame({"fund_id": weights.index, "fund_name": [name_map[item] for item in weights.index], "normalised_weight": weights.values})
    weight_display = weight_table.rename(
        columns={
            "fund_id": "Fund ID",
            "fund_name": "Fund",
            "normalised_weight": "Normalised weight",
        }
    )
    st.dataframe(weight_display.style.format({"Normalised weight": "{:.1%}"}), use_container_width=True, hide_index=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Monthly sample", f"{int(stats['number_of_months'])} months")
    c2.metric("Annualised return", format_percent(stats["annualised_return"]))
    c3.metric("Annualised volatility", format_percent(stats["annualised_volatility"]))
    c4.metric("Sharpe", format_number(stats["Sharpe"]))
    st.metric("Maximum drawdown", format_percent(stats["maximum_drawdown"]))

    chart_data = history.set_index("month")[["wealth"]]
    st.line_chart(chart_data, y_label="Growth of $1")
    st.line_chart(history.set_index("month")[["drawdown"]], y_label="Monthly drawdown")
    st.pyplot(correlation_heatmap(monthly.loc[:, selected].corr().rename(index=name_map, columns=name_map), "Monthly fund-return correlations"))
    st.markdown(
        "The allocation compounds each selected fund's daily net returns within calendar months, aligns on the shared monthly sample, and rebalances the illustrative fund mix monthly. No additional allocation-level transaction cost is applied."
    )
    st.download_button("Download normalised allocation", table_to_csv_bytes(weight_table), "signal_mosaic_allocation_weights.csv", "text/csv")
    st.download_button("Download monthly allocation returns", table_to_csv_bytes(history), "signal_mosaic_allocation_returns.csv", "text/csv")


def sentiment_page(data: dict[str, pd.DataFrame]) -> None:
    section_header(
        "Sentiment & Coverage",
        "Sector sentiment is shown with its evidence base. Missing news is not neutral sentiment, and high coverage is not a prediction guarantee.",
    )
    sentiment = data["sector_sentiment"]
    sectors = sorted(sentiment["sector"].unique())
    selected = st.multiselect("Sectors", sectors, default=sectors[:3])
    if not selected:
        st.warning("Select at least one sector.")
        return
    min_date, max_date = sentiment["date"].min().date(), sentiment["date"].max().date()
    start, end = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    view = st.selectbox(
        "Sentiment view",
        ["21-day trailing headline-aligned", "Raw headline-aligned", "One-day-lagged investable raw"],
    )
    field = {
        "21-day trailing headline-aligned": "vader_compound_21d_trailing",
        "Raw headline-aligned": "vader_compound_raw",
        "One-day-lagged investable raw": "vader_compound_lag1",
    }[view]
    filtered = sentiment.loc[(sentiment["date"].dt.date >= start) & (sentiment["date"].dt.date <= end)]

    st.pyplot(sentiment_chart(filtered, selected, field, f"{view} sector sentiment"))
    st.pyplot(coverage_chart(filtered, selected, "Coverage Lens context"))
    st.markdown(
        "Breadth close to 1 means headlines are spread more evenly across the five stocks in a sector. Breadth close to 0.2 means one ticker dominates that sector-month or day. Coverage stays separate from sentiment."
    )

    latest_date = sentiment["date"].max()
    latest = sentiment.loc[sentiment["date"] == latest_date, [
        "sector",
        "vader_compound_lag1",
        "coverage_share",
        "breadth",
        "article_count",
        "signal_available",
    ]].sort_values("sector")
    latest_display = rename_for_display(latest, SENTIMENT_LABELS)
    st.dataframe(
        latest_display.style.format({"Lagged sentiment": "{:.3f}", "Coverage share": "{:.1%}", "Breadth": "{:.3f}"}),
        use_container_width=True,
        hide_index=True,
    )

    diag = data["sentiment_diagnostics"].iloc[0]
    neutral_share = float(diag.get("vader_neutral_share", float("nan")))
    exact_zero_share = float(diag.get("exact_zero_compound_share", float("nan")))
    c1, c2 = st.columns(2)
    c1.metric("Plain VADER neutral headline share", format_percent(neutral_share, 2))
    c2.metric("Exact-zero compound share", format_percent(exact_zero_share, 2))
    st.markdown("Plain VADER was retained as a transparent baseline. No AI-generated finance lexicon was activated without human validation.")

    section_header("Fusion Result")
    fusion = data["fusion_before_after"]
    predictive = data["fusion_predictive"]
    fusion_display = rename_for_display(
        fusion[[
            "fund_name",
            "annualised_return_net",
            "annualised_volatility_net",
            "Sharpe_net",
            "maximum_drawdown_net",
            "cumulative_return_net",
        ]],
        FUSION_LABELS,
    )
    st.dataframe(
        fusion_display.style.format(
            {
                "Net annualised return": "{:.1%}",
                "Net volatility": "{:.1%}",
                "Net Sharpe": "{:.2f}",
                "Maximum drawdown": "{:.1%}",
                "Cumulative net return": "{:.1%}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.pyplot(growth_chart(data["fund_returns"], ["equity_equal_weight", "equity_sentiment_naive", "equity_sentiment_coverage_gated"], "Equity sentiment overlays versus Equal Weight", "Signal Mosaic fund_returns.csv"))
    for line in fusion_summary(fusion, predictive):
        st.markdown(f"- {line}")


def methodology_page(data: dict[str, pd.DataFrame]) -> None:
    section_header("Methodology & Limitations")
    st.markdown(
        """
        **Data Factory Floor**

        1. Clean market and headline data.
        2. Build returns, headline panels, and the Coverage Lens.
        3. Run walk-forward funds, standalone sentiment, and sentiment fusion.
        4. Deliver precomputed results through this app.
        """
    )
    st.markdown(
        """
        **Data.** The project uses 50 US equities across ten sectors, 10 cryptocurrencies, and equity headlines over the 2020-2023 source period. Fund results begin out of sample in 2021.

        **Fund design.** The funds use expanding training windows, monthly rebalancing, past information only, long-only optimised weights where applicable, a 10 basis-point one-way turnover cost, and rf = 0 for Sharpe. Equity and combined funds use 252 annualisation; crypto-only funds use 365.

        **Sentiment design.** Headlines are scored individually with plain VADER, aggregated to ticker-day first, then equal-weighted by available tickers within each sector. Missing news remains missing. Investable sentiment is lagged one complete trading day, so Saturday and Monday headlines aligned to Monday first become usable on Tuesday.

        **Coverage-Gated innovation.** coverage_quality = lagged 21-day coverage share x lagged 21-day breadth. The value controls the size of an active sentiment view. It is not sentiment and it is not proof of predictive power.
        """
    )
    section_header("Limitations")
    for item in LIMITATIONS:
        st.markdown(f"- {item}")

    section_header("Pipeline Status")
    inventory = data["app_inventory"].copy()
    pipeline = data["pipeline_validation"].copy()
    last_date = max(data["fund_returns"]["date"].max(), data["sector_sentiment"]["date"].max()).date()
    c1, c2, c3 = st.columns(3)
    c1.metric("App artifacts ready", f"{(inventory['readiness_status'] == 'READY').sum()} / {len(inventory)}")
    c2.metric("Validation PASS", f"{(pipeline['status'] == 'PASS').sum()} / {len(pipeline)}")
    c3.metric("Last available date", str(last_date))
    inventory_display = inventory.rename(
        columns={
            "path": "Artifact",
            "purpose": "Purpose",
            "exists": "Exists",
            "row_count": "Rows",
            "column_count": "Columns",
            "minimum_date": "Minimum date",
            "maximum_date": "Maximum date",
            "unique_funds": "Unique funds",
            "unique_sectors": "Unique sectors",
            "duplicate_key_count": "Duplicate keys",
            "schema_status": "Schema status",
            "readiness_status": "Readiness",
        }
    )
    pipeline_display = pipeline.rename(
        columns={
            "validation_name": "Validation",
            "expected": "Expected",
            "observed": "Observed",
            "status": "Status",
            "notes": "Notes",
        }
    )
    st.dataframe(inventory_display, use_container_width=True, hide_index=True)
    st.dataframe(pipeline_display, use_container_width=True, hide_index=True)


def main() -> None:
    setup_page()
    data = load_or_stop()
    st.sidebar.markdown("## Signal Mosaic")
    section = st.sidebar.radio("Navigation", SECTION_NAMES, index=0)

    if section == "Overview":
        overview_page(data)
    elif section == "Compare Funds":
        compare_funds_page(data)
    elif section == "Fund Fact Sheet":
        fact_sheet_page(data)
    elif section == "Allocation Studio":
        allocation_page(data)
    elif section == "Sentiment & Coverage":
        sentiment_page(data)
    elif section == "Methodology & Limitations":
        methodology_page(data)


if __name__ == "__main__":
    main()
