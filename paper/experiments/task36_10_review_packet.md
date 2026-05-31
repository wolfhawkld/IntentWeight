# Task36.10 Review Packet

Updated: 2026-05-31

## Purpose

This task assembles a venue-neutral review packet for independent academic
review before LaTeX template migration. It does not add new experiments or new
claims. Its purpose is to give reviewers one stable entry point instead of a
directory of separate draft chapters and evidence notes.

## Files Added

- `paper/experiments/scripts/task36_10_build_review_packet.py`
- `paper/experiments/task36_10_review_packet.md`
- `paper/review_packet/README.md`
- `paper/review_packet/manuscript.md`
- `paper/review_packet/references.bib`
- `paper/review_packet/figure_index.md`
- `paper/review_packet/submission_checklist.md`
- `paper/review_packet/validation_report.md`
- `paper/review_packet/manifest.sha256`

## Review Packet Contents

- assembled title, abstract, main manuscript, and appendix;
- provisional BibTeX bibliography;
- draft figure index and regeneration sources;
- submission checklist covering claim boundaries, simulated feedback,
  multi-epoch disclosure, seed limitations, 400k variance, encoder robustness,
  and LLM-smoke limitations;
- automated validation report;
- SHA-256 manifest for packet files.

## Regeneration Command

Run from the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_10_build_review_packet.py
```

The script runs the full-draft validator before assembling the packet and then
checks the assembled packet again.

## Validation Result

```text
packet_validation=passed
chapters=10
manuscript_words=8771
citation_keys=16
bib_entries=16
figure_assets=3
```

The SHA-256 manifest verifies cleanly, and the packet bibliography is
byte-identical to `paper/full_draft/references.bib`.

## Paper-Facing Decision

Use `paper/review_packet/` as the independent-review handoff. Continue editing
source chapters under `paper/full_draft/`; regenerate the packet after any
paper-facing source change.
