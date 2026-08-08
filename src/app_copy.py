"""Small text constants for the Signal Mosaic app."""

SECTION_NAMES = [
    "Overview",
    "Compare Funds",
    "Fund Fact Sheet",
    "Allocation Studio",
    "Sentiment & Coverage",
    "Methodology & Limitations",
]

BASE_FUND_IDS = [
    "equity_equal_weight",
    "equity_minimum_variance",
    "equity_risk_parity",
    "crypto_equal_weight",
    "crypto_minimum_variance",
    "crypto_risk_parity",
    "combined_equal_weight",
    "combined_minimum_variance",
    "combined_risk_parity",
]

FUSION_FUND_IDS = [
    "equity_sentiment_naive",
    "equity_sentiment_coverage_gated",
]

COMPARISON_FUND_NAMES = [
    "Equity Equal Weight",
    "Equity Naive Sentiment Tilt",
    "Equity Coverage-Gated Sentiment Tilt",
]

METHOD_DESCRIPTIONS = {
    "Equal Weight": (
        "Allocates equally across the available assets and rebalances monthly. "
        "It is the transparent benchmark for each asset family."
    ),
    "Minimum Variance": (
        "Uses only past returns to estimate risk, then chooses long-only weights "
        "that minimise portfolio variance subject to the stated cap."
    ),
    "Risk Parity": (
        "Uses only past returns to spread estimated risk contributions more evenly "
        "across holdings, subject to long-only and cap constraints."
    ),
    "Naive Sentiment Tilt": (
        "Starts from equal sector weights, then tilts equity sectors with a fixed "
        "plain-VADER sector sentiment signal. It is not an optimiser."
    ),
    "Coverage-Gated Sentiment Tilt": (
        "Uses the same fixed sentiment tilt, but scales the active view by lagged "
        "coverage breadth and coverage share. Coverage controls signal size; it is "
        "not sentiment and it is not proof of predictability."
    ),
}

LIMITATIONS = [
    "The out-of-sample window is short and covers 2021-2023 only.",
    "The equity universe is limited to 50 large US equities across ten sectors.",
    "Crypto funds use market returns only; the project has no crypto headline data.",
    "Plain VADER leaves many finance headlines neutral and was not extended here.",
    "Historical Sharpe ratios are sample evidence, not forecasts.",
    "The 10 basis-point one-way turnover cost is a modelling assumption.",
    "Taxes, market impact, custody, and management fees are not modelled.",
    "Combined funds exclude weekend-only crypto returns by design.",
    "The Allocation Studio compares funds on common monthly returns.",
    "Coverage Lens measures evidence breadth, not truth or predictive power.",
]
