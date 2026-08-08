from __future__ import annotations

import ast
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src import app_logic
from src.app_copy import BASE_FUND_IDS, FUSION_FUND_IDS, SECTION_NAMES
from src.app_data import AppDataError, _load_app_data_uncached, validate_app_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_SOURCES = [
    PROJECT_ROOT / "streamlit_app.py",
    PROJECT_ROOT / "src" / "app_data.py",
    PROJECT_ROOT / "src" / "app_logic.py",
    PROJECT_ROOT / "src" / "app_charts.py",
    PROJECT_ROOT / "src" / "app_copy.py",
]


@pytest.fixture(scope="module")
def app_data():
    return _load_app_data_uncached(PROJECT_ROOT)


def test_app_artifacts_load_and_validate(app_data):
    assert app_data["metrics"]["fund_id"].nunique() == 11
    assert set(app_data["metrics"]["fund_id"]) == set(BASE_FUND_IDS + FUSION_FUND_IDS)
    assert app_data["sector_sentiment"]["sector"].nunique() == 10
    assert pd.api.types.is_datetime64_any_dtype(app_data["fund_returns"]["date"])
    assert pd.api.types.is_datetime64_any_dtype(app_data["sector_sentiment"]["date"])
    assert not app_data["fund_returns"].duplicated(["date", "fund_id"]).any()
    assert not app_data["fund_weights"].duplicated(["rebalance_date", "fund_id", "asset"]).any()
    assert not app_data["sector_sentiment"].duplicated(["date", "sector"]).any()
    assert (app_data["pipeline_validation"]["status"] == "PASS").all()


def test_missing_artifact_has_controlled_error(tmp_path):
    with pytest.raises(AppDataError, match="Missing precomputed artifact"):
        _load_app_data_uncached(tmp_path)


def test_duplicate_keys_are_rejected(app_data):
    duplicate = {key: value.copy() for key, value in app_data.items()}
    duplicate["fund_returns"] = pd.concat(
        [duplicate["fund_returns"], duplicate["fund_returns"].iloc[[0]]],
        ignore_index=True,
    )
    with pytest.raises(AppDataError, match="Duplicate date-fund"):
        validate_app_data(duplicate)


def test_static_deployment_rules():
    forbidden_imports = {
        "nltk",
        "src.data_access",
        "src.etl",
        "src.features",
        "src.portfolios",
        "src.sentiment",
        "src.fusion",
        "scripts.build_foundation",
        "scripts.build_funds",
        "scripts.build_sentiment",
        "scripts.build_fusion",
        "scripts.run_part_b",
    }
    combined = ""
    for source in APP_SOURCES:
        text = source.read_text(encoding="utf-8")
        combined += "\n" + text
        tree = ast.parse(text)
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        assert not (imports & forbidden_imports), f"{source} imports prohibited modules: {imports & forbidden_imports}"

    assert "C:\\Users\\" not in combined
    assert not re.search(r"\bsubprocess\b|\bos\.system\b|\brunpy\b", combined)
    assert not re.search(r"\.to_parquet\s*\(|open\s*\([^)]*,\s*['\"]w", combined)
    req_lines = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    active_reqs = [line.strip().lower() for line in req_lines if line.strip() and not line.strip().startswith("#")]
    assert "nltk" not in active_reqs
    assert (PROJECT_ROOT / "streamlit_app.py").exists()


def test_allocation_weight_normalisation_and_rejection():
    weights = app_logic.normalise_weights({"a": 20, "b": 30})
    assert weights.to_dict() == pytest.approx({"a": 0.4, "b": 0.6})
    with pytest.raises(app_logic.AllocationError):
        app_logic.normalise_weights({"a": 0, "b": 0})
    with pytest.raises(app_logic.AllocationError):
        app_logic.normalise_weights({"a": -1, "b": 2})


def test_monthly_allocation_logic_is_compounded_and_aligned():
    daily = pd.DataFrame(
        {
            "date": pd.to_datetime(["2021-01-04", "2021-01-05", "2021-01-31", "2021-02-01", "2021-02-28"] * 2),
            "fund_id": ["a"] * 5 + ["b"] * 5,
            "net_return": [0.01, 0.02, -0.01, 0.03, 0.00, 0.00, 0.01, 0.02, -0.02, 0.01],
        }
    )
    monthly = app_logic.monthly_fund_returns(daily, ["a", "b"])
    expected_a_jan = (1.01 * 1.02 * 0.99) - 1.0
    expected_b_jan = (1.00 * 1.01 * 1.02) - 1.0
    assert monthly.loc[pd.Timestamp("2021-01-31"), "a"] == pytest.approx(expected_a_jan)
    assert monthly.loc[pd.Timestamp("2021-01-31"), "b"] == pytest.approx(expected_b_jan)
    history = app_logic.allocation_return_history(monthly, {"a": 0.25, "b": 0.75})
    assert history.loc[0, "allocation_return"] == pytest.approx(0.25 * expected_a_jan + 0.75 * expected_b_jan)
    metrics = app_logic.allocation_metrics(history)
    cumulative = float((1.0 + history["allocation_return"]).prod() - 1.0)
    assert metrics["annualised_return"] == pytest.approx((1.0 + cumulative) ** (12 / len(history)) - 1.0)
    assert metrics["annualised_volatility"] == pytest.approx(history["allocation_return"].std(ddof=1) * np.sqrt(12))
    assert history["drawdown"].le(0).all()


def test_fact_sheet_records_exist_for_every_fund(app_data):
    metrics = app_data["metrics"]
    latest = app_data["latest_holdings"]
    returns = app_data["fund_returns"]
    assert set(metrics["fund_id"]) == set(latest["fund_id"].unique())
    assert set(metrics["fund_id"]) == set(returns["fund_id"].unique())
    for _, row in metrics.iterrows():
        label = app_logic.calendar_label(row["asset_family"])
        if row["asset_family"] == "Crypto":
            assert "seven-day" in label
        if row["fund_id"] in FUSION_FUND_IDS:
            assert "Sentiment Tilt" in row["method"]


def test_sentiment_display_data_preserves_missing_zero_and_coverage(app_data):
    sentiment = app_data["sector_sentiment"]
    assert sentiment["sector"].nunique() == 10
    assert sentiment["vader_compound_raw"].isna().any()
    zero_rows = sentiment.loc[sentiment["vader_compound_raw"] == 0]
    assert not zero_rows.empty
    assert zero_rows["vader_compound_raw"].notna().all()
    assert {"coverage_share", "breadth", "article_count"}.issubset(sentiment.columns)
    comparison_names = set(app_data["fusion_before_after"]["fund_name"])
    assert comparison_names == {
        "Equity Equal Weight",
        "Equity Naive Sentiment Tilt",
        "Equity Coverage-Gated Sentiment Tilt",
    }


def test_streamlit_app_smoke_with_apptest():
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(PROJECT_ROOT / "streamlit_app.py"), default_timeout=20)
    app.run()
    assert not app.exception
    text = "\n".join(str(item.value) for item in app.markdown)
    titles = "\n".join(str(item.value) for item in app.title)
    assert "Signal Mosaic" in titles
    assert "Eleven walk-forward" in text or "11" in text
    radio_labels = [str(option) for option in app.sidebar.radio[0].options]
    assert radio_labels == SECTION_NAMES
