# IntentRoute Review Packet

Updated: 2026-05-31

This directory is the venue-neutral review handoff for the IntentRoute paper.
It is generated from `paper/full_draft/` and should be used for independent
academic review before LaTeX venue migration.

## Review Entry Points

- `manuscript.md`: assembled paper-facing manuscript and appendix.
- `references.bib`: provisional BibTeX bibliography.
- `figure_index.md`: draft figure assets and regeneration sources.
- `submission_checklist.md`: claim-boundary and migration checklist.
- `validation_report.md`: automated draft and packet validation output.
- `manifest.sha256`: content hashes for packet files.

## Regeneration

Run from the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_10_build_review_packet.py
```

Edit source chapters under `paper/full_draft/`, then regenerate this packet.
Do not manually edit generated packet files.
