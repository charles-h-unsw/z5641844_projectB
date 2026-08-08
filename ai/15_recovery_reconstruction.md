# Recovery reconstruction after accidental cleanup

## Incident

A release-preparation PowerShell cleanup command deleted ordinary Project B files more broadly than intended. A subsequent Local History attempt restored many paths as zero-byte files. The final report survived in the conversation, while several analytical modules and report sources survived in the damaged archive.

## Reconstruction method

- Re-extracted the official `projectB_starter.zip`.
- Restored official non-editable infrastructure such as `src/data_access.py`, requirements, course context and starter checks.
- Overlaid every non-empty surviving Project B file.
- Restored the approved final report PDF and editable DOCX copy.
- Reconstructed the missing fund, sentiment, fusion, app-chart and smoke-test entrypoints from the surviving analytical modules, final artifact contracts and recorded methodology.
- Reconstructed missing AI workflow summaries honestly; exact prompt text is labelled unavailable rather than invented.
- Added synthetic tests for sentiment, fusion and orchestration.

## Required local finalisation

The rebuilt archive intentionally does not contain fabricated result CSVs. On the student's machine, install the declared requirements and run `python scripts/run_part_b.py`. This downloads the official course bundle through the provided loader and regenerates the final CSVs, tables and figures. Then run the full tests, app smoke test and hand-in checker.

## Safety rule

Do not run broad recursive cleanup commands again. Cache files should be ignored through `.gitignore`; physical cleanup is optional and must be narrowly targeted.
