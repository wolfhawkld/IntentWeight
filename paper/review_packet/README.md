# IntentRoute Review Packet

Updated: 2026-07-21

This directory is the venue-neutral review handoff for the IntentRoute paper.
It is generated from `paper/full_draft/` and should be used for independent
academic review before LaTeX venue migration.

This packet is a generated review surface, not the authoritative project-status
record. Use `../experiments/task80_authoritative_submission_state.md` and
`../experiments/task80_remaining_work_checklist.md` for current counts and
remaining work.

## Review Entry Points

- `manuscript.md`: assembled paper-facing main manuscript.
- `supplementary_material.md`: complete supporting evidence separated under
  approved Task67 scheme A.
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
