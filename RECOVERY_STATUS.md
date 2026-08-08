# Project B Recovery Status

This folder has been reconstructed from:

1. the official Project B starter;
2. non-empty surviving Project B source files;
3. the approved final report saved in the conversation; and
4. the documented final data contracts and methodology.

## What is already restored

- Official starter infrastructure and course context
- ETL, features, portfolio, sentiment and fusion analytical modules
- Streamlit app and app data/logic/copy/chart helpers
- Fund, sentiment and fusion build entrypoints
- Orchestration, report build/validation and smoke-test scripts
- Foundation, fund, sentiment, fusion, orchestration and app tests
- Final report DOCX and approved 18-page PDF
- AI workflow records, including clearly labelled reconstructed summaries

## What must be regenerated locally

The `results/` directory contains only `.gitkeep` files until the official course data is downloaded. From the Project B root:

```powershell
& "C:\Users\19476\Documents\GitHub\fins-agent\.venv\Scripts\python.exe" -m pip install -r requirements.txt -r requirements-dev.txt
& "C:\Users\19476\Documents\GitHub\fins-agent\.venv\Scripts\python.exe" scripts\run_part_b.py
& "C:\Users\19476\Documents\GitHub\fins-agent\.venv\Scripts\python.exe" -m pytest -q
& "C:\Users\19476\Documents\GitHub\fins-agent\.venv\Scripts\python.exe" scripts\smoke_test_app.py
& "C:\Users\19476\Documents\GitHub\fins-agent\.venv\Scripts\python.exe" scripts\check_handin.py
```

Expected final headline checks:

- 11 unique funds
- 11 performance metric rows
- 10,060 sector sentiment rows
- 360 fusion rebalance-signal rows
- 81 pipeline validation PASS rows
- 57 pytest tests passed
- 22 hand-in checks passed

Do not regenerate the report unless necessary. The approved `report/report.pdf` is already included.
