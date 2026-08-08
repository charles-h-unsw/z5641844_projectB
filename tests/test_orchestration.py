from __future__ import annotations

import ast
import importlib.util
import pathlib
import sys

import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "run_part_b.py"


def _module():
    spec = importlib.util.spec_from_file_location("run_part_b_recovered", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_stage_order_is_foundation_funds_sentiment_fusion():
    module = _module()
    assert module.STAGES == [
        "scripts/build_foundation.py",
        "scripts/build_funds.py",
        "scripts/build_sentiment.py",
        "scripts/build_fusion.py",
    ]


def test_orchestrator_uses_sys_executable_and_own_root():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "sys.executable" in text
    assert "Path(__file__)" in text or "pathlib.Path(__file__)" in text
    assert "parent.parent" in text


def test_orchestrator_has_no_streamlit_git_or_report_side_effects():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    constants = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    joined = "\n".join(constants).lower()
    assert "streamlit run" not in joined
    assert "git push" not in joined
    assert "build_report.py" not in joined


def test_run_stages_fails_fast(monkeypatch):
    module = _module()
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        raise __import__("subprocess").CalledProcessError(1, command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    with pytest.raises(__import__("subprocess").CalledProcessError):
        module._run_stages()
    assert len(calls) == 1


def test_required_app_artifact_specs_are_present():
    module = _module()
    paths = {spec.path for spec in module.APP_ARTIFACTS}
    assert {
        "results/data/fund_returns.csv",
        "results/data/fund_weights.csv",
        "results/data/sector_sentiment_index.csv",
        "results/data/fusion_rebalance_signals.csv",
        "results/tables/performance_metrics.csv",
    }.issubset(paths)


def test_exact_base_and_fusion_ids():
    module = _module()
    assert len(module.BASE_FUND_IDS) == 9
    assert len(module.FUSION_FUND_IDS) == 2
    assert len(module.FINAL_FUND_IDS) == 11
    assert module.BASE_FUND_IDS.isdisjoint(module.FUSION_FUND_IDS)


def test_final_artifact_keys_when_built():
    returns_path = ROOT / "results" / "data" / "fund_returns.csv"
    weights_path = ROOT / "results" / "data" / "fund_weights.csv"
    metrics_path = ROOT / "results" / "tables" / "performance_metrics.csv"
    sentiment_path = ROOT / "results" / "data" / "sector_sentiment_index.csv"
    if any(not p.exists() or p.stat().st_size == 0 for p in [returns_path, weights_path, metrics_path, sentiment_path]):
        pytest.skip("run scripts/run_part_b.py to build final artifacts")
    returns = pd.read_csv(returns_path)
    weights = pd.read_csv(weights_path)
    metrics = pd.read_csv(metrics_path)
    sent = pd.read_csv(sentiment_path)
    assert metrics["fund_id"].nunique() == 11 and len(metrics) == 11
    assert not returns.duplicated(["date", "fund_id"]).any()
    assert not weights.duplicated(["rebalance_date", "fund_id", "asset"]).any()
    assert not sent.duplicated(["date", "sector"]).any()
    assert sent["sector"].nunique() == 10


def test_inventory_and_validation_ready_when_built():
    inventory_path = ROOT / "results" / "tables" / "app_artifact_inventory.csv"
    validation_path = ROOT / "results" / "tables" / "pipeline_validation.csv"
    if any(not p.exists() or p.stat().st_size == 0 for p in [inventory_path, validation_path]):
        pytest.skip("run scripts/run_part_b.py to create readiness tables")
    inventory = pd.read_csv(inventory_path)
    validation = pd.read_csv(validation_path)
    assert (inventory["readiness_status"] == "READY").all()
    assert (validation["status"] == "PASS").all()
