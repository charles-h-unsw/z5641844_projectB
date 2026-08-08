# AI Workflow Record 10: Report Phase 1 Evidence-Grounded Draft

## Purpose and Scope

Stage: Part B Report Phase 1 - evidence audit, evidence-grounded Markdown draft, and student-review handoff.

Purpose: organise verified Project B evidence into an evidence map and a Markdown report draft without creating a final Word or PDF submission. This phase supports student review and rewriting; it does not approve final economic interpretation.

Allowed outputs for this phase:

- `report/EVIDENCE_MAP.md`
- `report/report_draft.md`
- `ai/10_report_draft.md`

Not performed:

- no DOCX or PDF creation
- no report rendering or conversion
- no Streamlit run
- no Git command
- no deployment command
- no web research
- no Project A or sibling-folder inspection

## Exact User Prompt

[USER TO PASTE THE EXACT REPORT-PHASE-1 PROMPT HERE]

The exact long prompt was not reproduced verbatim in this log after conversation compaction. It has therefore been left as a labelled placeholder rather than reconstructed inaccurately.

## Files Inspected

Project instructions and context:

- `PROJECT_BRIEF.md`
- `README.md`
- `SUBMISSION_CHECKLIST.md`
- `AGENTS.md`
- `context/DATA_GUIDE.md`
- `context/project_context.md`
- `context/verify_ai_output.md`
- `report/OUTLINE.md`

Prior AI workflow records:

- `ai/03_foundation_implementation.md`
- `ai/04_funds_oos_backtest.md`
- `ai/05_standalone_sentiment_index.md`
- `ai/06_sentiment_fusion.md`
- `ai/07_pipeline_orchestration.md`
- `ai/08_streamlit_app.md`
- `ai/09_app_visual_polish.md`

Report-facing tables and data:

- `results/tables/performance_metrics.csv`
- `results/tables/fund_backtest_design.csv`
- `results/tables/fund_fact_sheet_summary.csv`
- `results/tables/fund_latest_holdings.csv`
- `results/tables/fund_optimizer_diagnostics.csv`
- `results/tables/fusion_before_after.csv`
- `results/tables/fusion_signal_diagnostics.csv`
- `results/tables/fusion_predictive_diagnostics.csv`
- `results/tables/sentiment_model_diagnostics.csv`
- `results/tables/sentiment_sector_summary.csv`
- `results/tables/app_artifact_inventory.csv`
- `results/tables/pipeline_validation.csv`
- `results/data/fund_returns.csv`
- `results/data/fund_weights.csv`
- `results/data/sector_sentiment_index.csv`
- `results/data/fusion_rebalance_signals.csv`

Report-relevant figures inspected by filename:

- `results/figures/fund_drawdowns_combined.png`
- `results/figures/fund_growth_of_one_by_family.png`
- `results/figures/fund_risk_return_comparison.png`
- `results/figures/fund_weights_over_time_combined.png`
- `results/figures/fusion_before_after_metrics.png`
- `results/figures/fusion_coverage_attenuation.png`
- `results/figures/fusion_growth_of_one.png`
- `results/figures/fusion_sector_active_weights.png`
- `results/figures/sector_sentiment_timeseries.png`
- `results/figures/sentiment_coverage_context.png`
- `results/figures/vader_neutrality_by_sector.png`

Final app copy and methodology code inspected:

- `streamlit_app.py`
- `src/app_copy.py`
- `src/app_logic.py`
- `src/app_data.py`

## Evidence-Map Process

The evidence map was created before the draft. It records each central report claim with:

- claim ID
- proposed claim
- claim type
- exact supporting file
- exact row, fund, sector, date, field, or statistic
- related table or figure
- numerical value where applicable
- permitted wording
- wording that would overstate the evidence
- limitation or caveat
- student-review requirement
- final claim status

Evidence-map result:

- total claim rows: 53
- verified rows: 43
- review-required rows: 5
- unsupported rows excluded from the draft: 4
- rows with a student-review requirement: 19

Unsupported claims excluded:

- the app is live or deployed
- sentiment generated alpha
- coverage proves truth or predictive value
- the app provides personal financial advice

## Protected Analytical CSV Hashes Before Drafting

| File | SHA-256 before |
|---|---|
| `results/data/fund_returns.csv` | `5e51f0aa2044f11b181f6f26271342dad338f52e34c1d49aaebfdee408797d5c` |
| `results/data/fund_weights.csv` | `63d559844fa5bac5ea2f7c5af966a1bccd1d2479f2e2f1fab7a1596dd2058b26` |
| `results/data/sector_sentiment_index.csv` | `7df0d114663fbaf1e9721d3912fce18df0d2d201d97b27688d3e2e737a6d7f6c` |
| `results/data/fusion_rebalance_signals.csv` | `a5a57c00198d3cd3d7fce412a884302451633636f78581920b3af1231b6cc751` |
| `results/tables/performance_metrics.csv` | `bc82cf0b987675618ccd165775d112a24be071b4fb3403d848117d312c0499d8` |
| `results/tables/fusion_before_after.csv` | `d73c724a6dd073b8dccc43d3724c08101528b115b3b32baa8e25f98938142f5d` |
| `results/tables/fusion_predictive_diagnostics.csv` | `f37a81d5d0f7e2d5ae36fb2a564ccf31696a3fd84b76ccb8f1c46617045423de` |
| `results/tables/fund_latest_holdings.csv` | `8eab12b49b667f5de103963d6cfb5ae6fd78352bc3bde3c0cabb391881dddfb5` |
| `results/tables/fund_fact_sheet_summary.csv` | `f140f5e54b2fbfd29273740728bc55cb1d0db5968bec05ffcd9c256ff4c6a87b` |

## Files Created

- `report/EVIDENCE_MAP.md`
- `report/report_draft.md`
- `ai/10_report_draft.md`

No analytical result CSV, figure, source module, app file, DOCX, or PDF was created or modified.

## Draft Word Count

The Markdown draft contains 4,969 total words including the draft notice, references, exhibit placeholders, and student review checklist.

Section counts:

- Draft notice: 64
- Executive Summary: 405
- Section 1: 515
- Section 2: 949
- Section 3: 492
- Section 4: 803
- Section 5: 435
- Section 6: 558
- Conclusion: 164
- References: 81
- Appendix Plan: 282
- Student Review Checklist: 204

## Student-Review Markers

Total student-review markers in the draft: 27.

By category:

- Economic interpretation: 10
- Critical reflection: 8
- Recommendation: 3
- Product positioning: 5
- General draft-status notice: 1

The draft keeps these markers in place for Phase 1 review and does not claim student approval.

## Exhibits Proposed

Core narrative exhibits:

- Table 1. Backtest design and assumptions: `results/tables/fund_backtest_design.csv`
- Table 2. Net performance metrics across the eleven funds: `results/tables/performance_metrics.csv`
- Figure 1. Net risk-return comparison across funds: `results/figures/fund_risk_return_comparison.png`
- Figure 2. Net growth of $1 for representative funds: `results/figures/fund_growth_of_one_by_family.png`
- Figure 3. Combined-fund drawdowns: `results/figures/fund_drawdowns_combined.png`
- Figure 4. Sector sentiment over time: `results/figures/sector_sentiment_timeseries.png`
- Table 3. Equal Weight versus Naive and Coverage-Gated sentiment tilts: `results/tables/fusion_before_after.csv`
- Figure 5. Fusion growth of $1: `results/figures/fusion_growth_of_one.png`
- Figure 6. Sentiment with coverage context: `results/figures/sentiment_coverage_context.png`

Appendix exhibits:

- complete fund metrics: `results/tables/performance_metrics.csv`
- portfolio weights over time: `results/figures/fund_weights_over_time_combined.png`
- latest holdings: `results/tables/fund_latest_holdings.csv`
- fund fact-sheet summary: `results/tables/fund_fact_sheet_summary.csv`
- sentiment diagnostics: `results/tables/sentiment_model_diagnostics.csv`
- predictive diagnostics: `results/tables/fusion_predictive_diagnostics.csv`
- pipeline validation summary: `results/tables/pipeline_validation.csv`

All proposed exhibit source files exist locally.

## References Used

Draft references are limited to locally supported sources:

- UNSW FINS3645 Project Brief (2026)
- UNSW FINS3645 course project_data.zip, accessed through `src/data_access.py`
- Hric and Lin (2026), as identified in local course materials
- Markowitz (1952), as identified in local Project B context
- Sharpe (1966), as identified in local Project B context
- NLTK package metadata for the VADER implementation used locally

References requiring student verification:

- Hric and Lin (2026)
- Markowitz (1952)
- Sharpe (1966)
- the VADER publication details

No URL, DOI, issue number, page number, publisher detail, or access date was invented.

## Factual Checks Performed

Automated and manual checks covered:

1. every quoted metric was checked against final CSVs
2. every named fund exists in `performance_metrics.csv`
3. all eleven funds are represented
4. first-live and final dates match `fund_backtest_design.csv` and result files
5. gross and net values are not confused in reported performance claims
6. crypto funds use 365 annualisation
7. equity and combined funds use 252 annualisation
8. sentiment applies only to equity headlines
9. no claim says sentiment beat Equity Equal Weight
10. no claim says coverage created positive predictive value
11. no claim says coverage proves truth
12. no claim describes the app as live or deployed
13. no claim uses current-market language
14. no claim describes 2021-2023 results as persistent superiority
15. interpretive language is marked for student review
16. exactly three recommendations are included
17. every recommendation has a student-review marker
18. proposed figure sources exist
19. proposed table sources exist
20. no DOCX or PDF was created

QA note: a source scan flagged the phrase "persistent superiority", but inspection confirmed it appears only in the caution that persistent superiority remains unproven. This is a false positive, not an unsupported claim.

## Discrepancies and Corrections

- The first metrics-extraction command used a Bash-style heredoc in PowerShell and failed before analysis ran. It was rerun using PowerShell-compatible stdin.
- A later factual-QA command was malformed before execution. It was replaced with a smaller deterministic QA script.
- No numerical result was changed during these corrections.

## Protected Analytical CSV Hashes After Drafting

| File | SHA-256 after |
|---|---|
| `results/data/fund_returns.csv` | `5e51f0aa2044f11b181f6f26271342dad338f52e34c1d49aaebfdee408797d5c` |
| `results/data/fund_weights.csv` | `63d559844fa5bac5ea2f7c5af966a1bccd1d2479f2e2f1fab7a1596dd2058b26` |
| `results/data/sector_sentiment_index.csv` | `7df0d114663fbaf1e9721d3912fce18df0d2d201d97b27688d3e2e737a6d7f6c` |
| `results/data/fusion_rebalance_signals.csv` | `a5a57c00198d3cd3d7fce412a884302451633636f78581920b3af1231b6cc751` |
| `results/tables/performance_metrics.csv` | `bc82cf0b987675618ccd165775d112a24be071b4fb3403d848117d312c0499d8` |
| `results/tables/fusion_before_after.csv` | `d73c724a6dd073b8dccc43d3724c08101528b115b3b32baa8e25f98938142f5d` |
| `results/tables/fusion_predictive_diagnostics.csv` | `f37a81d5d0f7e2d5ae36fb2a564ccf31696a3fd84b76ccb8f1c46617045423de` |
| `results/tables/fund_latest_holdings.csv` | `8eab12b49b667f5de103963d6cfb5ae6fd78352bc3bde3c0cabb391881dddfb5` |
| `results/tables/fund_fact_sheet_summary.csv` | `f140f5e54b2fbfd29273740728bc55cb1d0db5968bec05ffcd9c256ff4c6a87b` |

Hash comparison result: unchanged for every protected analytical CSV.

## Verification Commands

Commands run or to be run from the Project B root:

```powershell
& "C:\Users\19476\Documents\GitHub\fins-agent\.venv\Scripts\python.exe" -m pytest -q
& "C:\Users\19476\Documents\GitHub\fins-agent\.venv\Scripts\python.exe" scripts\check_handin.py
```

Verification results:

- `pytest -q`: 57 passed in 21.71 seconds on the final rerun.
- `scripts/check_handin.py`: 21 checks passed; 2 reminders.

Hand-in reminders:

- delete `__pycache__/` and `*.pyc` before zipping because they are auto-generated
- `report/report.pdf` is absent because Phase 1 intentionally did not create the final report PDF

## Phase 1 Handoff

The draft remains a student-review artifact. The student must review, rewrite where necessary, and approve all marked interpretation, recommendation, reflection, and product-positioning paragraphs before any final Word or PDF report production.
