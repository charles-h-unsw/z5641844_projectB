"""Run the complete Project B analytical pipeline.

This command rebuilds the precomputed artifacts that the Streamlit app will
later read. It does not run Streamlit, Git, deployment, report generation, or
the hand-in checker.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "results" / "data"
TABLES = ROOT / "results" / "tables"

BASE_FUND_IDS = {
    "equity_equal_weight",
    "equity_minimum_variance",
    "equity_risk_parity",
    "crypto_equal_weight",
    "crypto_minimum_variance",
    "crypto_risk_parity",
    "combined_equal_weight",
    "combined_minimum_variance",
    "combined_risk_parity",
}
FUSION_FUND_IDS = {
    "equity_sentiment_naive",
    "equity_sentiment_coverage_gated",
}
FINAL_FUND_IDS = BASE_FUND_IDS | FUSION_FUND_IDS

STAGES = [
    "scripts/build_foundation.py",
    "scripts/build_funds.py",
    "scripts/build_sentiment.py",
    "scripts/build_fusion.py",
]


@dataclass(frozen=True)
class ArtifactSpec:
    path: str
    purpose: str
    key: tuple[str, ...]
    date_column: str | None = None
    fund_column: str | None = None
    sector_column: str | None = None


APP_ARTIFACTS = [
    ArtifactSpec(
        "results/data/fund_returns.csv",
        "App-ready daily gross and net fund returns, wealth, drawdown, turnover, and costs.",
        ("date", "fund_id"),
        "date",
        "fund_id",
    ),
    ArtifactSpec(
        "results/data/fund_weights.csv",
        "App-ready monthly target and pretrade fund holdings.",
        ("rebalance_date", "fund_id", "asset"),
        "rebalance_date",
        "fund_id",
    ),
    ArtifactSpec(
        "results/data/sector_sentiment_index.csv",
        "App-ready standalone daily equity-sector sentiment index with lagged fields.",
        ("date", "sector"),
        "date",
        sector_column="sector",
    ),
    ArtifactSpec(
        "results/data/fusion_rebalance_signals.csv",
        "App-ready monthly sector sentiment and coverage-gated fusion signals.",
        ("rebalance_date", "sector"),
        "rebalance_date",
        sector_column="sector",
    ),
    ArtifactSpec(
        "results/tables/performance_metrics.csv",
        "App-ready fund performance metrics and assumptions.",
        ("fund_id",),
        fund_column="fund_id",
    ),
    ArtifactSpec(
        "results/tables/fusion_before_after.csv",
        "App-ready before-vs-after comparison for Equity Equal Weight and sentiment tilts.",
        ("fund_id",),
        fund_column="fund_id",
    ),
    ArtifactSpec(
        "results/tables/fusion_predictive_diagnostics.csv",
        "App-ready non-parametric sentiment-return diagnostics.",
        ("sample",),
    ),
    ArtifactSpec(
        "results/tables/fund_latest_holdings.csv",
        "App-ready latest holdings for all final funds.",
        ("fund_id", "asset"),
        "rebalance_date",
        "fund_id",
    ),
    ArtifactSpec(
        "results/tables/fund_fact_sheet_summary.csv",
        "App-ready compact fact-sheet summary for every final fund.",
        ("fund_id",),
        "first_live_date",
        "fund_id",
    ),
]

REQUIRED_COLUMNS = {
    "results/data/fund_returns.csv": {
        "date",
        "fund_id",
        "fund_name",
        "asset_family",
        "method",
        "gross_return",
        "net_return",
        "gross_wealth",
        "net_wealth",
        "net_drawdown",
        "rebalance_flag",
        "turnover",
        "transaction_cost",
    },
    "results/data/fund_weights.csv": {
        "rebalance_date",
        "fund_id",
        "fund_name",
        "asset_family",
        "method",
        "asset",
        "asset_class",
        "sector",
        "pretrade_weight",
        "target_weight",
        "is_latest_rebalance",
    },
    "results/data/sector_sentiment_index.csv": {
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
    },
    "results/data/fusion_rebalance_signals.csv": {
        "rebalance_date",
        "sector",
        "sentiment_signal",
        "sentiment_zscore",
        "coverage_share_21d_lag1",
        "breadth_21d_lag1",
        "coverage_quality",
        "naive_multiplier",
        "gated_multiplier",
        "base_sector_weight",
        "naive_sector_weight",
        "gated_sector_weight",
        "signal_available",
        "coverage_available",
    },
    "results/tables/performance_metrics.csv": {
        "fund_id",
        "fund_name",
        "first_live_date",
        "end_date",
        "number_of_observations",
        "annualisation_factor",
        "annualised_return_net",
        "annualised_volatility_net",
        "Sharpe_net",
        "maximum_drawdown_net",
        "current_number_of_holdings",
        "largest_current_weight",
    },
    "results/tables/fusion_before_after.csv": {
        "fund_id",
        "fund_name",
        "annualised_return_net",
        "annualised_volatility_net",
        "Sharpe_net",
        "maximum_drawdown_net",
        "cumulative_return_net",
        "change_in_return_vs_base",
        "change_in_volatility_vs_base",
        "change_in_Sharpe_vs_base",
        "change_in_max_drawdown_vs_base",
    },
    "results/tables/fusion_predictive_diagnostics.csv": {
        "sample",
        "pooled_spearman",
        "average_cross_sectional_spearman",
        "valid_monthly_observations",
        "valid_pair_observations",
        "median_coverage_quality",
    },
    "results/tables/fund_latest_holdings.csv": {
        "rebalance_date",
        "fund_id",
        "fund_name",
        "asset",
        "asset_class",
        "sector",
        "target_weight",
    },
    "results/tables/fund_fact_sheet_summary.csv": {
        "fund_id",
        "fund_name",
        "asset_family",
        "method",
        "first_live_date",
        "end_date",
        "annualised_return_net",
        "annualised_volatility_net",
        "Sharpe_net",
        "maximum_drawdown_net",
    },
}


def main() -> None:
    print(f"Project B root: {ROOT}", flush=True)
    _run_stages()
    frames = _load_app_artifacts()
    validation = validate_app_artifacts(frames)
    inventory = build_app_artifact_inventory(frames)
    validation = pd.concat(
        [validation, deployment_readiness_checks(frames)],
        ignore_index=True,
    )
    _write_csv(inventory, TABLES / "app_artifact_inventory.csv")
    _write_csv(validation, TABLES / "pipeline_validation.csv")
    failures = validation.loc[~validation["status"].eq("PASS")]
    if not failures.empty:
        raise SystemExit(
            "pipeline validation failed:\n"
            + failures.to_string(index=False)
        )
    _print_final_summary(frames, validation)


def _run_stages() -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for index, stage in enumerate(STAGES, start=1):
        command = [sys.executable, stage]
        print(f"\n=== Stage {index}: {stage} ===", flush=True)
        subprocess.run(command, cwd=ROOT, env=env, check=True)


def _load_app_artifacts() -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for spec in APP_ARTIFACTS:
        path = ROOT / spec.path
        if not path.exists():
            raise SystemExit(f"missing required app artifact: {spec.path}")
        frames[spec.path] = pd.read_csv(path)
    return frames


def validate_app_artifacts(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def add(name: str, expected: object, observed: object, passed: bool, notes: str = "") -> None:
        rows.append(
            {
                "validation_name": name,
                "expected": str(expected),
                "observed": str(observed),
                "status": "PASS" if passed else "FAIL",
                "notes": notes,
            }
        )

    for spec in APP_ARTIFACTS:
        path = ROOT / spec.path
        frame = frames.get(spec.path)
        exists = path.exists()
        add(f"{spec.path}: exists", True, exists, exists)
        if frame is None:
            continue
        missing = REQUIRED_COLUMNS[spec.path].difference(frame.columns)
        add(
            f"{spec.path}: required columns",
            "no missing required columns",
            sorted(missing),
            not missing,
        )
        duplicate_count = _duplicate_count(frame, spec.key)
        add(f"{spec.path}: duplicate key count", 0, duplicate_count, duplicate_count == 0)

    returns = frames["results/data/fund_returns.csv"].copy()
    weights = frames["results/data/fund_weights.csv"].copy()
    sentiment = frames["results/data/sector_sentiment_index.csv"].copy()
    signals = frames["results/data/fusion_rebalance_signals.csv"].copy()
    metrics = frames["results/tables/performance_metrics.csv"].copy()
    latest = frames["results/tables/fund_latest_holdings.csv"].copy()
    fact_sheet = frames["results/tables/fund_fact_sheet_summary.csv"].copy()
    before_after = frames["results/tables/fusion_before_after.csv"].copy()

    fund_ids = set(metrics["fund_id"].astype(str))
    add("final fund count", 11, len(fund_ids), len(fund_ids) == 11)
    add("exact nine base fund IDs", sorted(BASE_FUND_IDS), sorted(fund_ids & BASE_FUND_IDS), BASE_FUND_IDS.issubset(fund_ids))
    add("exact two fusion fund IDs", sorted(FUSION_FUND_IDS), sorted(fund_ids & FUSION_FUND_IDS), FUSION_FUND_IDS.issubset(fund_ids))
    add("metrics only final fund IDs", sorted(FINAL_FUND_IDS), sorted(fund_ids), fund_ids == FINAL_FUND_IDS)
    add("returns for every final fund", sorted(FINAL_FUND_IDS), sorted(returns["fund_id"].astype(str).unique()), set(returns["fund_id"].astype(str).unique()) == FINAL_FUND_IDS)
    add("weights for every final fund", sorted(FINAL_FUND_IDS), sorted(weights["fund_id"].astype(str).unique()), set(weights["fund_id"].astype(str).unique()) == FINAL_FUND_IDS)
    add("latest holdings for every final fund", sorted(FINAL_FUND_IDS), sorted(latest["fund_id"].astype(str).unique()), set(latest["fund_id"].astype(str).unique()) == FINAL_FUND_IDS)
    add("fact sheet for every final fund", sorted(FINAL_FUND_IDS), sorted(fact_sheet["fund_id"].astype(str).unique()), set(fact_sheet["fund_id"].astype(str).unique()) == FINAL_FUND_IDS)
    add("fusion before-after comparison funds", ["equity_equal_weight", *sorted(FUSION_FUND_IDS)], sorted(before_after["fund_id"].astype(str).unique()), set(before_after["fund_id"].astype(str).unique()) == {"equity_equal_weight", *FUSION_FUND_IDS})

    sectors = set(sentiment["sector"].astype(str).unique())
    add("sentiment sector count", 10, len(sectors), len(sectors) == 10)
    add("no crypto sentiment rows", "no sector contains crypto", any("crypto" in s.lower() for s in sectors), not any("crypto" in s.lower() for s in sectors))
    add("fusion signal rows", "rebalance dates x sectors", len(signals), len(signals) == signals["rebalance_date"].nunique() * len(sectors))

    weight_sums = weights.groupby(["fund_id", "rebalance_date"], observed=True)["target_weight"].sum()
    add("target weights sum to one", "all close to 1", float((weight_sums - 1.0).abs().max()), np.allclose(weight_sums.to_numpy(dtype=float), 1.0, atol=1e-8))
    add("target weights finite", True, _finite(weights["target_weight"]), _finite(weights["target_weight"]))
    add("pretrade weights finite", True, _finite(weights["pretrade_weight"]), _finite(weights["pretrade_weight"]))
    add("gross wealth positive", True, returns["gross_wealth"].astype(float).gt(0).all(), returns["gross_wealth"].astype(float).gt(0).all())
    add("net wealth positive", True, returns["net_wealth"].astype(float).gt(0).all(), returns["net_wealth"].astype(float).gt(0).all())
    add("net drawdowns non-positive", True, returns["net_drawdown"].astype(float).le(1e-12).all(), returns["net_drawdown"].astype(float).le(1e-12).all())
    add("transaction costs non-negative", True, returns["transaction_cost"].astype(float).ge(-1e-12).all(), returns["transaction_cost"].astype(float).ge(-1e-12).all())

    for column in ["gross_return", "net_return", "gross_wealth", "net_wealth", "net_drawdown", "turnover", "transaction_cost"]:
        values = pd.to_numeric(returns[column], errors="coerce")
        add(f"fund_returns.{column} finite non-missing", True, bool(values.notna().all() and np.isfinite(values).all()), bool(values.notna().all() and np.isfinite(values).all()))
    for column in ["annualised_return_net", "annualised_volatility_net", "Sharpe_net", "maximum_drawdown_net"]:
        values = pd.to_numeric(metrics[column], errors="coerce")
        add(f"performance_metrics.{column} finite non-missing", True, bool(values.notna().all() and np.isfinite(values).all()), bool(values.notna().all() and np.isfinite(values).all()))

    sentiment_columns = [
        "vader_compound_raw",
        "vader_compound_lag1",
        "vader_compound_21d_trailing",
        "vader_compound_21d_trailing_lag1",
        "positive_ticker_share",
        "neutral_ticker_share",
        "negative_ticker_share",
    ]
    for column in sentiment_columns:
        values = pd.to_numeric(sentiment[column], errors="coerce").dropna()
        add(f"sector_sentiment_index.{column} within [-1, 1]", True, values.between(-1, 1).all(), values.between(-1, 1).all())
    add("missing raw sentiment preserved", "at least one NaN raw sentiment", int(sentiment["vader_compound_raw"].isna().sum()), sentiment["vader_compound_raw"].isna().any())

    expected_rows = {
        "results/data/fund_returns.csv": 9309,
        "results/data/fund_weights.csv": 16560,
        "results/data/sector_sentiment_index.csv": 10060,
        "results/data/fusion_rebalance_signals.csv": 360,
        "results/tables/performance_metrics.csv": 11,
    }
    for path, expected in expected_rows.items():
        observed = len(frames[path])
        add(f"{path}: observed frozen-sample row count", expected, observed, observed == expected)

    return pd.DataFrame(rows)


def build_app_artifact_inventory(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for spec in APP_ARTIFACTS:
        path = ROOT / spec.path
        frame = frames.get(spec.path)
        exists = path.exists()
        duplicate_count = _duplicate_count(frame, spec.key) if frame is not None else ""
        missing = REQUIRED_COLUMNS[spec.path].difference(frame.columns) if frame is not None else REQUIRED_COLUMNS[spec.path]
        min_date = ""
        max_date = ""
        if frame is not None and spec.date_column and spec.date_column in frame.columns:
            dates = pd.to_datetime(frame[spec.date_column], errors="coerce").dropna()
            if not dates.empty:
                min_date = dates.min().date().isoformat()
                max_date = dates.max().date().isoformat()
        unique_funds = ""
        if frame is not None and spec.fund_column and spec.fund_column in frame.columns:
            unique_funds = int(frame[spec.fund_column].nunique())
        unique_sectors = ""
        if frame is not None and spec.sector_column and spec.sector_column in frame.columns:
            unique_sectors = int(frame[spec.sector_column].nunique())
        schema_status = "PASS" if exists and not missing else "FAIL"
        readiness_status = "READY" if exists and not missing and duplicate_count == 0 else "NOT_READY"
        rows.append(
            {
                "path": spec.path,
                "purpose": spec.purpose,
                "exists": exists,
                "row_count": "" if frame is None else len(frame),
                "column_count": "" if frame is None else len(frame.columns),
                "minimum_date": min_date,
                "maximum_date": max_date,
                "unique_funds": unique_funds,
                "unique_sectors": unique_sectors,
                "duplicate_key_count": duplicate_count,
                "schema_status": schema_status,
                "readiness_status": readiness_status,
            }
        )
    return pd.DataFrame(rows)


def deployment_readiness_checks(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def add(name: str, expected: object, observed: object, passed: bool, notes: str = "") -> None:
        rows.append(
            {
                "validation_name": name,
                "expected": str(expected),
                "observed": str(observed),
                "status": "PASS" if passed else "FAIL",
                "notes": notes,
            }
        )

    requirements = _requirement_names(ROOT / "requirements.txt")
    requirements_dev = _requirement_names(ROOT / "requirements-dev.txt")
    app_text = (ROOT / "streamlit_app.py").read_text(encoding="utf-8", errors="ignore")
    add("deployment requirements exclude nltk", "nltk absent", "nltk" in requirements, "nltk" not in requirements)
    add("development requirements include nltk", "nltk present", "nltk" in requirements_dev, "nltk" in requirements_dev)
    add("streamlit root entrypoint exists", True, (ROOT / "streamlit_app.py").exists(), (ROOT / "streamlit_app.py").exists())
    add("future app does not import nltk", "nltk absent from streamlit_app.py", "nltk" in app_text.lower(), "nltk" not in app_text.lower())
    add("future app does not call build scripts", "build scripts absent from streamlit_app.py", bool(re.search(r"build_(foundation|funds|sentiment|fusion)|run_part_b", app_text)), not bool(re.search(r"build_(foundation|funds|sentiment|fusion)|run_part_b", app_text)))
    add("no committed streamlit secrets", ".streamlit/secrets.toml absent", (ROOT / ".streamlit" / "secrets.toml").exists(), not (ROOT / ".streamlit" / "secrets.toml").exists())

    source_paths = list((ROOT / "src").glob("*.py")) + list((ROOT / "scripts").glob("*.py")) + [ROOT / "streamlit_app.py"]
    local_path_pattern = _local_path_pattern()
    hardcoded_paths = [
        str(path.relative_to(ROOT))
        for path in source_paths
        if local_path_pattern.search(path.read_text(encoding="utf-8", errors="ignore"))
    ]
    add("no user-specific paths in source files", "none", hardcoded_paths, not hardcoded_paths)
    project_a_name = "z" + "5641844" + "_projectA"
    project_a_refs = [
        str(path.relative_to(ROOT))
        for path in source_paths
        if project_a_name in path.read_text(encoding="utf-8", errors="ignore")
    ]
    add("no Project A runtime references in source files", "none", project_a_refs, not project_a_refs)

    path_like_cells: list[str] = []
    secret_like_cells: list[str] = []
    for rel, frame in frames.items():
        text = frame.astype(str)
        if text.apply(lambda col: col.str.contains(local_path_pattern, na=False)).any().any():
            path_like_cells.append(rel)
        if text.apply(lambda col: col.str.contains(r"(?:api[_-]?key|secret|token|password)\s*[:=]", case=False, regex=True, na=False)).any().any():
            secret_like_cells.append(rel)
    add("no absolute local paths in app-facing CSVs", "none", path_like_cells, not path_like_cells)
    add("no secrets in app-facing CSVs", "none", secret_like_cells, not secret_like_cells)

    raw_artifacts = [
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".parquet", ".zip"} and "results" not in path.parts
    ]
    add("no raw parquet or zip required by deployed app", "none", raw_artifacts, not raw_artifacts)
    return pd.DataFrame(rows)


def deterministic_hashes(paths: list[str] | None = None) -> dict[str, str]:
    selected = paths or [
        "results/data/fund_returns.csv",
        "results/data/fund_weights.csv",
        "results/data/sector_sentiment_index.csv",
        "results/data/fusion_rebalance_signals.csv",
        "results/tables/performance_metrics.csv",
        "results/tables/fusion_before_after.csv",
        "results/tables/fusion_predictive_diagnostics.csv",
        "results/tables/fund_latest_holdings.csv",
        "results/tables/fund_fact_sheet_summary.csv",
    ]
    return {
        rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        for rel in selected
    }


def _requirement_names(path: pathlib.Path) -> set[str]:
    names: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        name = re.split(r"[<>=!~\[]", line, maxsplit=1)[0].strip().lower()
        if name:
            names.add(name)
    return names


def _local_path_pattern() -> re.Pattern[str]:
    path_tokens = [
        "C:" + chr(92) + "Users" + chr(92),
        "/" + "Users" + "/",
        "/" + "home" + "/",
    ]
    return re.compile("|".join(re.escape(token) for token in path_tokens))


def _duplicate_count(frame: pd.DataFrame | None, key: tuple[str, ...]) -> int:
    if frame is None or not set(key).issubset(frame.columns):
        return -1
    return int(frame.duplicated(list(key)).sum())


def _finite(series: pd.Series) -> bool:
    values = pd.to_numeric(series, errors="coerce")
    return bool(values.notna().all() and np.isfinite(values).all())


def _write_csv(frame: pd.DataFrame, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, float_format="%.12g")


def _print_final_summary(frames: dict[str, pd.DataFrame], validation: pd.DataFrame) -> None:
    print("\n=== Final artifact validation ===")
    for spec in APP_ARTIFACTS:
        frame = frames[spec.path]
        print(f" - {spec.path}: rows={len(frame)}, columns={len(frame.columns)}")
    print(f"validation_rules={len(validation)}")
    print("validation_status=PASS")
    print("wrote:")
    print(f" - {(TABLES / 'app_artifact_inventory.csv').relative_to(ROOT)}")
    print(f" - {(TABLES / 'pipeline_validation.csv').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
