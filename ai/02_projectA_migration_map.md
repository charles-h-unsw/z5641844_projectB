# Project A migration map

> Recovery note: this workflow record was reconstructed from the conversation record and surviving project artifacts after an accidental release-cleanup deletion. It is an accurate stage summary, but the exact original prompt text was not recoverable.

## Purpose and scope

Read-only mapping of reusable Project A ETL, returns, headline alignment, Coverage Lens and tests into Project B.

## Main human decisions

- Work was restricted to `z5641844_projectB` except for specifically authorised, read-only Project A comparison tasks.
- Raw course data, secrets and local absolute paths were excluded from the submission.
- Look-ahead controls, missing-news treatment and calendar conventions were treated as hard constraints.
- Numerical results were not retuned or rewritten after they were observed.

## Outcome

Project A remained read-only. Code was classified as reuse/refactor/regenerate/exclude; Project B kept the official data_access helper.

## Verification and corrections

The stage used targeted tests, the full pytest suite where applicable, `scripts/check_handin.py`, and explicit comparison of generated artifacts. Human corrections included rejecting unsupported claims, preserving plain VADER as a transparent baseline, removing the Project A runtime dependency, and keeping the negative fusion result unchanged.
