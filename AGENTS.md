# Project B Agent Instructions

This folder, `fins2026/z5641844_projectB/`, is the working root for FINS3645
Project B. Project B covers Stations 3 and 4: funds, sentiment, fusion, and the
Streamlit app.

## Workspace Boundary

- Treat this Project B folder as the working root for inspection, commands,
  analysis, edits, tests, and generated outputs.
- Do not inspect or modify sibling folders unless the user explicitly authorises
  a named, read-only migration task.
- Never modify `z5641844_projectA`.
- If a task appears to require access outside Project B, stop and ask first.

## Course Infrastructure

- Before major implementation work, read `PROJECT_BRIEF.md`, `README.md`,
  `SUBMISSION_CHECKLIST.md`, and the files under `context/`.
- Keep `context/` unchanged.
- Preserve the provided `src/data_access.py` interface.
- Do not replace official data access with scraping, unofficial APIs, or
  invented data.

## Data Rules

- Never commit raw source parquet files or cached raw data.
- Cap crypto data at `2023-12-31`.
- Compute equity and crypto returns on their native calendars before alignment.
- Use the correct annualisation convention and document it.
- Normalise news timezone and date types before joining.
- Deduplicate news using `ticker`, `date`, and `title`.
- Do not interpret missing news as neutral sentiment without an explicit,
  documented modelling decision.

## Backtest Rules

- All reported fund performance must be walk-forward and out-of-sample.
- Weights at time `t` may use only information available before the holding
  period.
- The initial estimation window, first live date, rebalance rule, window type,
  constraints, risk-free-rate assumption, and transaction-cost assumption must be
  explicit.
- Include automated checks against look-ahead bias.
- Check that weights sum to one and that different optimisation methods
  genuinely produce different weights.
- Do not present in-sample optimisation results as investable performance.

## Sentiment Rules

- Sentiment applies only to equity headlines.
- Build the sector index by first forming ticker-day sentiment and then
  equal-weighting tickers within each sector.
- Lag every investable sentiment signal by at least one trading day.
- A headline aligned to trading day `t` cannot affect a position held on day `t`.
- Plain VADER results, finance-lexicon extensions, missing-headline treatment,
  and sentiment fusion choices must be separately documented and tested.

## App Rules

- `streamlit_app.py` must read precomputed artifacts from `results/`.
- The deployed app must not recompute portfolio backtests or run VADER.
- Keep deployment dependencies light.
- Never include secrets, absolute local paths, or user-specific file paths.

## Required Artifacts

Preserve these exact required filenames:

- `results/data/fund_returns.csv`
- `results/data/fund_weights.csv`
- `results/data/sector_sentiment_index.csv`
- `results/tables/performance_metrics.csv`

## Verification

- Run relevant tests after each implementation stage.
- Run `python scripts/run_part_b.py` before final app testing.
- Run `streamlit run streamlit_app.py` locally.
- Run `python scripts/check_handin.py` before a task is considered complete.
- Report exact commands, outputs, files changed, assumptions, and unresolved
  issues.
- Do not fix unrelated files merely to make a check pass.

## AI Transparency

- Maintain curated records under `ai/`.
- Each major entry must record the prompt, what the AI changed or proposed, how
  the result was checked, any errors found, the user's correction, and the reason
  for the correction.
- Never invent user review, test output, results, citations, or corrections.
- If an exact prompt is unavailable, insert a labelled placeholder instead of
  reconstructing it inaccurately.

## Writing And Interpretation

- Do not invent numerical findings.
- Draft prose only from generated and verified project results.
- Distinguish computed evidence from proposed interpretation.
- Leave final economic interpretation and recommendations for user review.
