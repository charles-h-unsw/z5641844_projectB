# AI Workflow Record 12: Final Report Production

## Purpose and Scope

Stage: Part B Report Phase 2 - final content, exhibits, DOCX, PDF, factual QA, and visual QA.

Purpose: produce the submission-ready Part B report from the student-approved naturalised draft and final Project B artifacts, without changing analytical results or running Git, deployment, Streamlit, Project A, or sibling-folder work.

## Exact Prompt

[USER TO PASTE THE EXACT FINAL-REPORT-PRODUCTION PROMPT HERE]

The prompt was the current final report production request with student approval, cover details, approved interpretations, final exhibit structure, references, DOCX/PDF production requirements, factual QA, visual QA, and verification commands. The exact long prompt has not been reconstructed verbatim here to avoid accidental inaccuracy.

## Student Approval Recorded

Author: Chenhang Huang

zID: z5641844

Course: FINS3645 Financial Market Data Design & Analysis

Assessment: Project B

Final title: Signal Mosaic: Systematic Multi-Asset Funds with Coverage-Aware News Sentiment.

The student explicitly approved the substantive interpretations and decisions listed in the final report production prompt, including:

- Crypto Minimum Variance had the highest measured net annualised return and net Sharpe in this sample, but must not be described as universally best or safest because volatility was 76.12% and maximum drawdown was -73.55%.
- Equity Equal Weight had the highest net Sharpe among equity base methods; Minimum Variance reduced measured volatility and drawdown while giving up return.
- Combined Risk Parity had the highest net Sharpe in the combined family, while Combined Equal Weight had higher return and Combined Minimum Variance had lower volatility and drawdown.
- The 2021-2023 out-of-sample period is too short to establish persistent superiority.
- Plain VADER sentiment did not improve Equity Equal Weight in the implemented fusion test.
- Coverage-Gated Sentiment Tilt performed better than Naive Sentiment Tilt but did not create positive predictive value.
- Negative Spearman diagnostics do not prove sentiment can never work.
- Coverage Lens is evidence-breadth disclosure, signal-risk control, and context for sector sentiment, not proof of truth, predictability, sentiment, or alpha.
- "Current holdings" should be replaced with latest backtest target holdings at the final reported rebalance or equivalent wording.
- VADER's 49.57% neutral share and 48.85% exact-zero share indicate a potential false-neutral limitation, not economic neutrality for half the headlines.
- Plain VADER remains the transparent baseline unless a replacement is validated with human labels and a separate holdout.
- The final three recommendations are approved.
- Natural, grammatically correct English is approved, with sparse first person only for genuine methodological judgments.
- The main and appendix exhibit structure is approved.
- The final bibliography listed in the prompt is approved.

No approval is claimed for any interpretation outside those listed areas.

## Files Inspected

Required inputs confirmed:

- `report/report_draft_naturalised.md`
- `report/report_draft.md`
- `report/EVIDENCE_MAP.md`
- `ai/10_report_draft.md`
- `ai/11_report_naturalisation.md`

Additional project files inspected:

- `PROJECT_BRIEF.md`
- `README.md`
- `SUBMISSION_CHECKLIST.md`
- `AGENTS.md`
- `context/DATA_GUIDE.md`
- `context/project_context.md`
- `context/verify_ai_output.md`
- `report/OUTLINE.md`
- `ai/03_foundation_implementation.md`
- `ai/04_funds_oos_backtest.md`
- `ai/05_standalone_sentiment_index.md`
- `ai/06_sentiment_fusion.md`
- `ai/07_pipeline_orchestration.md`
- `ai/08_streamlit_app.md`
- `ai/09_app_visual_polish.md`

Final artifacts inspected:

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
- proposed report figures under `results/figures/`

## Analytical Hashes Before Report Production

| File | SHA-256 before |
|---|---|
| `results/data/fund_returns.csv` | `5e51f0aa2044f11b181f6f26271342dad338f52e34c1d49aaebfdee408797d5c` |
| `results/data/fund_weights.csv` | `63d559844fa5bac5ea2f7c5af966a1bccd1d2479f2e2f1fab7a1596dd2058b26` |
| `results/data/sector_sentiment_index.csv` | `7df0d114663fbaf1e9721d3912fce18df0d2d201d97b27688d3e2e737a6d7f6c` |
| `results/data/fusion_rebalance_signals.csv` | `a5a57c00198d3cd3d7fce412a884302451633636f78581920b3af1231b6cc751` |
| `results/tables/performance_metrics.csv` | `bc82cf0b987675618ccd165775d112a24be071b4fb3403d848117d312c0499d8` |
| `results/tables/fund_backtest_design.csv` | `c2aac703e52e17e3050829ed145bfb0dba21ae7d201ace4594eca79d31725897` |
| `results/tables/fund_fact_sheet_summary.csv` | `f140f5e54b2fbfd29273740728bc55cb1d0db5968bec05ffcd9c256ff4c6a87b` |
| `results/tables/fund_latest_holdings.csv` | `8eab12b49b667f5de103963d6cfb5ae6fd78352bc3bde3c0cabb391881dddfb5` |
| `results/tables/fund_optimizer_diagnostics.csv` | `6347985e11b239dd73ec4d01710b4e6fda7dc1072014a063510c68ebb42544a6` |
| `results/tables/fusion_before_after.csv` | `d73c724a6dd073b8dccc43d3724c08101528b115b3b32baa8e25f98938142f5d` |
| `results/tables/fusion_signal_diagnostics.csv` | `6c96639cce5c9a40b27f1e8c86f72ada0ab933cd99ae4f739a7b64aa58ff487a` |
| `results/tables/fusion_predictive_diagnostics.csv` | `f37a81d5d0f7e2d5ae36fb2a564ccf31696a3fd84b76ccb8f1c46617045423de` |
| `results/tables/sentiment_model_diagnostics.csv` | `e4f1af4f18a3708973e0c7a5fe6bad07f8631d901d2a294d5c257d5a17c312a8` |
| `results/tables/sentiment_sector_summary.csv` | `eb50be195d3e583598cd9fb2e2bd7a7266997e7c6af00afe1a8e524d47d52e7f` |
| `results/tables/app_artifact_inventory.csv` | `97d5ff746bb1394892c03edbc636d816a40788ccdf73289dd29c426dce567fb1` |
| `results/tables/pipeline_validation.csv` | `f77e240eece810b0bf8acaef88ab68900a9e25f9f142645375ac289210864d4a` |

## Production Notes

## Files Created

- `report/report_final.md`
- `report/report.docx`
- `report/report.pdf`
- `scripts/build_report.py`
- `scripts/validate_report.py`
- `ai/12_final_report_production.md`

Temporary render files were created under `report/_qa/` for visual inspection and removed after the final QA pass.

## Six-Excluded-Headline Resolution

Inspected:

- `results/tables/sentiment_model_diagnostics.csv`
- `src/sentiment.py`
- `scripts/build_sentiment.py`
- `tests/test_sentiment.py`

The locally supported wording used in the final report is:

> Of the 146,836 deduplicated headline records, 146,830 could be aligned to an available equity trading date and scored. Six end-of-sample records had no later eligible trading date within the sample and were excluded from the aligned sentiment panel.

This wording is supported by the implemented headline alignment and sentiment build path, which excludes headlines that cannot be mapped to an available equity trading date before scoring the aligned panel.

## Naturalised Draft Used

`report/report_draft_naturalised.md` was used as the primary prose source. `report/report_draft.md` and `report/EVIDENCE_MAP.md` were used as evidence controls to check that material evidence had not been omitted.

## Final Length and Page Count

- Final narrative word count, Executive Summary through Conclusion: 3,564 words.
- Total Markdown word count: 3,788 words.
- Section word counts:
  - Executive Summary: 409
  - Funds and Walk-Forward Backtest Design: 365
  - Out-of-Sample Results and Fund Fact Sheets: 816
  - Standalone Sector Sentiment Index: 401
  - Coverage-Gated Sentiment Fusion: 600
  - Signal Mosaic App and Investor Journey: 344
  - Critical Reflection and Three Recommendations: 447
  - Conclusion: 144
- DOCX page count from Microsoft Word: 18 pages.
- PDF page count from PDF page objects: 18 pages.
- Narrative page count: 10 pages, from Executive Summary on page 2 to before References on page 12.

## Tables and Figures

Main tables inserted:

- Table 1. Walk-forward backtest design by asset family.
- Table 2. Net out-of-sample performance across the eleven Signal Mosaic funds, 2021-2023.
- Table 3. Equity Equal Weight versus the two sentiment-overlay funds.

Main figures inserted:

- Figure 1. `results/figures/fund_risk_return_comparison.png`
- Figure 2. `results/figures/fund_growth_of_one_by_family.png`
- Figure 3. `results/figures/fund_drawdowns_combined.png`
- Figure 4. `results/figures/sector_sentiment_timeseries.png`
- Figure 5. `results/figures/sentiment_coverage_context.png`
- Figure 6. `results/figures/fusion_growth_of_one.png`

Appendix exhibits inserted:

- Appendix Table A1a. Expanded fund performance metrics.
- Appendix Table A1b. Expanded fund implementation metrics.
- Appendix Figure A1. `results/figures/fund_weights_over_time_combined.png`
- Appendix Table A2. Representative latest backtest target holdings at the final reported rebalance.
- Appendix Table A3. Fund fact-sheet summary.
- Appendix Table A4. Plain-VADER headline scoring diagnostics.
- Appendix Table A5. Monthly sentiment-return rank-correlation diagnostics.
- Appendix Table A6. Pipeline validation summary.

## References

The final report uses the six approved Harvard-style references:

- Hric and Lin (2026)
- Hutto and Gilbert (2014)
- Markowitz (1952)
- Sharpe (1966)
- UNSW FINS3645 (2026a)
- UNSW FINS3645 (2026b)

No reference placeholders remain.

## Document Generation and PDF Export

- DOCX method: `python-docx` through `scripts/build_report.py`.
- PDF method: installed Microsoft Word automation through PowerShell COM export from the generated DOCX.
- Report metadata set:
  - Title: Signal Mosaic: Systematic Multi-Asset Funds with Coverage-Aware News Sentiment
  - Author: Chenhang Huang
  - Subject: FINS3645 Project B
  - Keywords: multi-asset funds, sentiment, Coverage Lens, Streamlit

## Visual QA

DOCX QA method:

- Rendered all 18 DOCX pages using Microsoft Word page ranges exported to EMF and converted to PNG contact sheets.
- Inspected the rendered cover, narrative pages, references, figures, tables, landscape appendix figure, and appendix tables.

PDF QA method:

- Exported PDF directly from the validated DOCX using Microsoft Word fixed-format export.
- Confirmed the PDF is non-empty and contains 18 page objects.
- The local environment did not provide a dedicated PDF raster renderer such as Poppler, PyMuPDF, Ghostscript, or LibreOffice. The visual QA therefore relies on the DOCX page render plus Microsoft Word's fixed-format export result and PDF structural validation.

Defects found and corrected:

- Appendix Table A5 initially exposed snake_case sample labels. They were converted to readable labels.
- Appendix Table A2 initially rendered too sparsely across landscape pages. It was revised into a compact three-column Word table while preserving the same representative holdings values.
- Table-grid widths were written explicitly in DOCX XML to improve table stability.

Final visual result:

- No clipped figures, distorted figures, missing figures, overlapping text, accidental blank pages, or narrative page-limit breach was found in the final DOCX render.
- Main figures remain in the required order and are referenced in the surrounding prose.

## Factual QA

Automated factual checks performed: 83.

Result: 83 passed, 0 failed.

The checks covered:

- fund count and sector count
- first live dates and annualisation factors
- all Table 2 and Table 3 metric values
- Crypto Minimum Variance return, volatility, Sharpe, and drawdown
- Combined Risk Parity and Equity Equal Weight metrics
- sentiment scoring count and VADER neutral/exact-zero shares
- ticker-day count, sentiment row count, and no-news sector-day count
- coverage-quality range and attenuation share
- Spearman diagnostics
- pipeline PASS count and app artifact count
- absence of claims that sentiment beat Equal Weight, coverage created predictive value, Coverage Lens proves truth, the App is live/deployed, or the holdings are current-market positions
- exactly three recommendations

## Unfinished-Content Search

Searched `report/report_final.md`, extracted DOCX text, and PDF bytes for:

- DRAFT
- STUDENT REVIEW
- INSERT TABLE
- INSERT FIGURE
- REFERENCE DETAILS
- TODO
- FIXME
- placeholder
- current holdings
- strongest headline
- investable in the backtest sense
- `vader_compound_21d_trailing_lag1`
- `C:\Users\`
- `z5641844_projectA`

Result: no inappropriate matches.

## Analytical Hashes After Report Production

All protected analytical CSV hashes after report production matched the before hashes exactly:

| File | SHA-256 after |
|---|---|
| `results/data/fund_returns.csv` | `5e51f0aa2044f11b181f6f26271342dad338f52e34c1d49aaebfdee408797d5c` |
| `results/data/fund_weights.csv` | `63d559844fa5bac5ea2f7c5af966a1bccd1d2479f2e2f1fab7a1596dd2058b26` |
| `results/data/sector_sentiment_index.csv` | `7df0d114663fbaf1e9721d3912fce18df0d2d201d97b27688d3e2e737a6d7f6c` |
| `results/data/fusion_rebalance_signals.csv` | `a5a57c00198d3cd3d7fce412a884302451633636f78581920b3af1231b6cc751` |
| `results/tables/performance_metrics.csv` | `bc82cf0b987675618ccd165775d112a24be071b4fb3403d848117d312c0499d8` |
| `results/tables/fund_backtest_design.csv` | `c2aac703e52e17e3050829ed145bfb0dba21ae7d201ace4594eca79d31725897` |
| `results/tables/fund_fact_sheet_summary.csv` | `f140f5e54b2fbfd29273740728bc55cb1d0db5968bec05ffcd9c256ff4c6a87b` |
| `results/tables/fund_latest_holdings.csv` | `8eab12b49b667f5de103963d6cfb5ae6fd78352bc3bde3c0cabb391881dddfb5` |
| `results/tables/fund_optimizer_diagnostics.csv` | `6347985e11b239dd73ec4d01710b4e6fda7dc1072014a063510c68ebb42544a6` |
| `results/tables/fusion_before_after.csv` | `d73c724a6dd073b8dccc43d3724c08101528b115b3b32baa8e25f98938142f5d` |
| `results/tables/fusion_signal_diagnostics.csv` | `6c96639cce5c9a40b27f1e8c86f72ada0ab933cd99ae4f739a7b64aa58ff487a` |
| `results/tables/fusion_predictive_diagnostics.csv` | `f37a81d5d0f7e2d5ae36fb2a564ccf31696a3fd84b76ccb8f1c46617045423de` |
| `results/tables/sentiment_model_diagnostics.csv` | `e4f1af4f18a3708973e0c7a5fe6bad07f8631d901d2a294d5c257d5a17c312a8` |
| `results/tables/sentiment_sector_summary.csv` | `eb50be195d3e583598cd9fb2e2bd7a7266997e7c6af00afe1a8e524d47d52e7f` |
| `results/tables/app_artifact_inventory.csv` | `97d5ff746bb1394892c03edbc636d816a40788ccdf73289dd29c426dce567fb1` |
| `results/tables/pipeline_validation.csv` | `f77e240eece810b0bf8acaef88ab68900a9e25f9f142645375ac289210864d4a` |

Confirmation: no analytical result changed.

## Commands Run

- `C:\Users\19476\Documents\GitHub\fins-agent\.venv\Scripts\python.exe scripts\build_report.py`
- `C:\Users\19476\Documents\GitHub\fins-agent\.venv\Scripts\python.exe scripts\validate_report.py`
- Microsoft Word COM commands for DOCX page count, DOCX page rendering, and PDF export.
- Python factual-audit and hash-check commands using the verified virtual-environment interpreter.

Final full-test and hand-in commands are recorded below after execution.

## Final Verification Results

Report-specific validation:

- Command: `C:\Users\19476\Documents\GitHub\fins-agent\.venv\Scripts\python.exe scripts\validate_report.py`
- Result: passed.
- Output summary: `report validation passed`; DOCX size 1,530,436 bytes; PDF size 1,517,938 bytes; embedded images 7; Word tables 10.

Full pytest:

- Command: `C:\Users\19476\Documents\GitHub\fins-agent\.venv\Scripts\python.exe -m pytest -q`
- Result: 57 passed in 21.84 seconds.

Hand-in check:

- Command: `C:\Users\19476\Documents\GitHub\fins-agent\.venv\Scripts\python.exe scripts\check_handin.py`
- Result: 22 checks passed.
- Reminder: delete `__pycache__/` and `*.pyc` before zipping because they are auto-generated and not needed.
- The previous missing-report-PDF reminder is resolved.

## Confirmation

- No analytical CSV was modified.
- No analytical source module was modified.
- No Streamlit work was performed.
- No Git command was run.
- No deployment command was run.
- No Project A or sibling folder was inspected.
