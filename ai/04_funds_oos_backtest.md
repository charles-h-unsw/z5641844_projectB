# Out-of-sample fund engine

> Recovery note: this workflow record was reconstructed from the conversation record and surviving project artifacts after an accidental release-cleanup deletion. It is an accurate stage summary, but the exact original prompt text was not recoverable.

## Purpose and scope

Implemented nine walk-forward funds: Equal Weight, long-only Minimum Variance and long-only Risk Parity across equity, crypto and combined universes.

## Main human decisions

- Work was restricted to `z5641844_projectB` except for specifically authorised, read-only Project A comparison tasks.
- Raw course data, secrets and local absolute paths were excluded from the submission.
- Look-ahead controls, missing-news treatment and calendar conventions were treated as hard constraints.
- Numerical results were not retuned or rewritten after they were observed.

## Outcome

Monthly expanding-window backtests used prior information only, 10 bps one-way turnover cost, 252/365 annualisation and no optimiser failures.

## Verification and corrections

The stage used targeted tests, the full pytest suite where applicable, `scripts/check_handin.py`, and explicit comparison of generated artifacts. Human corrections included rejecting unsupported claims, preserving plain VADER as a transparent baseline, removing the Project A runtime dependency, and keeping the negative fusion result unchanged.
