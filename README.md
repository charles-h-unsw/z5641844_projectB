# Signal Mosaic

Signal Mosaic is a Project B investment-product prototype for FINS3645. It combines walk-forward systematic funds with a sector sentiment index and a Coverage Lens that shows how broad or concentrated the underlying equity-news evidence is.

Target user: a financially literate individual investor who wants to compare transparent, rules-based multi-asset funds and understand whether a news signal is supported by broad coverage.

This is an educational analysis prototype, not personal financial advice.

## Principal Features

- 11 walk-forward out-of-sample funds covering equity, crypto, combined, and two equity sentiment overlays.
- Daily equity-sector sentiment index built from individual plain-VADER headline scores.
- Coverage Lens that reports article count, covered tickers, coverage share, and breadth.
- Signal Mosaic Coverage-Gated Sentiment Tilt, where coverage quality scales the size of an equity-sector sentiment view.
- Streamlit app that reads precomputed CSV artifacts from `results/` and does not rebuild analytics.

## Fund Set

Base funds:

- Equity Equal Weight
- Equity Minimum Variance
- Equity Risk Parity
- Crypto Equal Weight
- Crypto Minimum Variance
- Crypto Risk Parity
- Combined Equal Weight
- Combined Minimum Variance
- Combined Risk Parity

Sentiment-overlay funds:

- Equity Naive Sentiment Tilt
- Equity Coverage-Gated Sentiment Tilt

## Key Empirical Finding

In the current validated sample, Equity Equal Weight remained the strongest of the three equity comparison funds. Both sentiment tilts reduced net return and net Sharpe versus Equity Equal Weight. The Coverage-Gated Sentiment Tilt performed better than the Naive Sentiment Tilt, indicating that coverage attenuation reduced some signal damage but did not create positive predictive value.

No sentiment parameter was retuned after seeing these results.

## Project Structure

- `src/`: reusable Project B analytical and app-support code.
- `scripts/`: deterministic build and validation commands.
- `results/data/`: app-readable analytical data artifacts.
- `results/tables/`: validation, metric, diagnostic, and fact-sheet tables.
- `results/figures/`: generated analytical figures.
- `streamlit_app.py`: root Streamlit entrypoint.
- `.streamlit/config.toml`: app theme settings.
- `tests/`: deterministic tests for the analytical pipeline and app.
- `ai/`: curated AI workflow records.
- `context/`: course-provided context, kept unchanged.

## Reproduce the Analytical Pipeline

From the Project B root:

```powershell
python scripts/run_part_b.py
```

The pipeline rebuilds the foundation, base funds, standalone sentiment index, fusion funds, and app-readiness validation tables. It is intended to run before the app is launched.

## Run the App Locally

From the Project B root:

```powershell
streamlit run streamlit_app.py
```

With the repo virtual environment on Windows:

```powershell
& "..\..\.venv\Scripts\python.exe" -m streamlit run streamlit_app.py
```

## Tests

```powershell
python -m pytest tests/test_app.py -q
python scripts/smoke_test_app.py
python -m pytest -q
python scripts/check_handin.py
```

## Deployment Architecture

The deployed app is a lightweight presentation layer. It reads committed, precomputed CSV artifacts from `results/` using project-relative paths. It does not load raw market data or raw headline data, does not call build scripts, does not import NLTK, does not run VADER, and does not optimise portfolios.

Deployment requirements are kept separate from local development dependencies. The app uses precomputed sentiment results so the deployed environment does not require NLTK.

## Limitations

- Historical results cover a short 2021-2023 out-of-sample window.
- The equity universe contains 50 large US equities across ten sectors.
- Crypto funds have no matching sentiment data.
- Plain VADER produces many neutral finance headlines.
- The 10 basis-point transaction-cost assumption is simplified.
- Taxes, market impact, custody, and management fees are not modelled.
- Combined funds exclude weekend-only crypto returns.
- The Allocation Studio uses common monthly returns.
- Coverage Lens measures evidence breadth, not truth or predictability.

## Submission Placeholders

- Live Streamlit URL: https://z5641844projectb-27zghttja2ajpyztryvvm3.streamlit.app/
- Public GitHub repository URL: https://github.com/charles-h-unsw/z5641844_projectB
