# AI Workflow Record 11: Report Naturalisation

## Purpose and Scope

Stage: Natural student-voice revision without changing the evidence.

Purpose: create a more natural, professional student-voice version of the Phase 1 Markdown report draft while preserving all verified evidence, numerical results, fund names, formulas, assumptions, exhibit sources, references, conclusions, and student-review markers.

Allowed output:

- `report/report_draft_naturalised.md`
- `ai/11_report_naturalisation.md`

Not performed:

- no overwrite of `report/report_draft.md`
- no DOCX or PDF creation
- no analytical artifact modification
- no model, formula, build-script, Streamlit, Git, deployment, or Project A work
- no web research

## Exact Prompt

[USER TO PASTE THE EXACT NATURALISATION PROMPT HERE]

The prompt was the current task requesting a natural student-voice revision of `report/report_draft.md` into `report/report_draft_naturalised.md`, preserving evidence and creating this workflow record. The exact long prompt has not been reconstructed verbatim here to avoid accidental inaccuracy.

## Files Inspected

- `report/report_draft.md`
- `report/EVIDENCE_MAP.md`
- `ai/10_report_draft.md`
- `PROJECT_BRIEF.md`
- `report/OUTLINE.md`
- `results/tables/sentiment_model_diagnostics.csv`
- `results/tables/foundation_integrity_checks.csv`
- `results/tables/foundation_inventory.csv`
- `src/sentiment.py`
- `scripts/build_sentiment.py`
- `src/features.py`
- local editing rules: `docs/ai/workflows/edit-section.md`, `docs/ai/rules/academic-writing.md`, `docs/ai/rules/banned-words.md`

## Output File Created

- `report/report_draft_naturalised.md`

The original `report/report_draft.md` was not overwritten.

## Six Excluded Headlines

The Phase 1 draft said that six records were unscored because of missing titles. Local evidence shows a more precise explanation:

- `results/tables/sentiment_model_diagnostics.csv` reports 146,836 cleaned headlines, 146,830 scored headlines, and 6 unscored or missing-title records.
- `src/sentiment.py` drops rows with missing `trading_date`, missing title, or empty title before scoring.
- `results/tables/foundation_integrity_checks.csv` reports `headline_outside_calendar_rows = 6` with the detail "end-of-sample outside-calendar rows are explicit".
- `src/features.py` maps headlines to the same or next available equity trading date and marks rows beyond the available calendar as outside the available calendar.

Resolution used in the naturalised draft:

"The six excluded records are explained by the foundation integrity check: six end-of-sample headlines fall outside the available equity trading calendar after same-or-next trading-day alignment. The scoring function also excludes missing or empty titles, but the local counts show that the observed six-record difference is the outside-calendar case."

## Formulaic Phrases Removed

The naturalised draft removes or rewrites formulaic meta-language from the Phase 1 draft, including:

- "The student should review this wording"
- "The student should decide how strongly to frame this"
- "This statement should be kept narrow"
- "This should be presented as"
- "The final report should preserve that distinction"
- "investor-usefulness judgment"
- "strongest headline fund result"
- "investable in the backtest sense"
- raw field wording such as `vader_compound_21d_trailing_lag1` in the client-facing narrative

The caution behind those phrases was preserved as direct report language.

## First-Person Statements Introduced

First person was used sparingly only for genuine methodological or interpretive decisions supported by workflow records:

- "I keep plain VADER as the transparent baseline here rather than changing the model after seeing the backtest."
- "I retain Equal Weight as the comparison base..."
- "I interpret Coverage Lens mainly as a way to disclose signal support..."
- "I do not treat this as proof that sentiment can never work..."

No fake personal experience, surprise, struggle, expectation, or personal reflection was introduced.

## Paragraphs Reorganised

Main changes:

- student-review markers were moved onto their own line before each relevant paragraph
- critical reflection was reorganised into a more natural sequence covering sample/universe, sentiment/VADER, implementation/costs, calendar choices, and Coverage Lens interpretation
- recommendations were rewritten as operational decisions rather than generic checklists
- transaction-cost values were expressed as percentages where the metric is a rate
- figure order was corrected so Figure 5 is the sentiment-with-coverage figure and Figure 6 is fusion growth of one dollar
- a narrative reference to `results/figures/fund_weights_over_time_combined.png` was added before the appendix placeholder

## Terminology Corrected

Display and narrative terminology was revised:

- "strongest headline fund result" became "highest measured net return and Sharpe result"
- "investable in the backtest sense" became "look-ahead-controlled historical simulation based only on prior information"
- "current holdings" became "holdings at the final reported rebalance" or equivalent wording
- the raw sentiment field name was replaced with "one-trading-day-lagged, 21-day trailing sector sentiment measure"
- decimal cost rates were expressed as 0.09% and 0.24% in the narrative

## Word Count

- Before naturalisation: 4,969 words in `report/report_draft.md`
- After naturalisation: 4,685 words in `report/report_draft_naturalised.md`

The naturalised draft is within the requested approximate 4,000-4,700 word range.

## Evidence Preservation Checks

Automated QA checked that:

- key numerical values remained present
- fund names remained present
- dates remained present
- method and strategy names remained present
- review markers remained on their own line
- exactly three recommendations remained
- all exhibit source filenames still exist
- removed formulaic phrases did not remain
- no raw sentiment field name remained in the narrative

QA result: 0 issues.

Student-review marker count in the naturalised draft:

- total: 24
- Economic interpretation: 10
- Critical reflection: 6
- Recommendation: 3
- Product positioning: 5

## Confirmation

- No evidence or analytical value was intentionally changed.
- No analytical conclusion was reversed.
- No unsupported causal claim was introduced.
- No intentional grammar, spelling, factual, punctuation, or style error was added.
- No fake student experience or opinion was invented.
- Final student approval is still required before Word or PDF production.

## Verification Commands

Commands run from the Project B root:

```powershell
& "C:\Users\19476\Documents\GitHub\fins-agent\.venv\Scripts\python.exe" -m pytest -q
& "C:\Users\19476\Documents\GitHub\fins-agent\.venv\Scripts\python.exe" scripts\check_handin.py
```

Verification results:

- `pytest -q`: 57 passed in 23.68 seconds.
- `scripts/check_handin.py`: 21 checks passed; 2 reminders.

Hand-in reminders:

- delete `__pycache__/` and `*.pyc` before zipping
- `report/report.pdf` is still absent because no DOCX or PDF was created in this stage
