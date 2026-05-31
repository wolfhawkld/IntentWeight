# Task36.9 Full-Draft Consistency Audit

Updated: 2026-05-31

## Purpose

This task performs a paper-facing consistency audit after the appendix,
provisional bibliography, and draft figure assets have been added. It does not
add new experiments or new claims. Its purpose is to prevent internal labels,
unfinished markers, overstrong manifold wording, unpaired math delimiters, or
unresolved citation keys from leaking into the formal paper.

## Files Added

- `paper/experiments/scripts/task36_9_validate_full_draft.py`
- `paper/experiments/task36_9_full_draft_consistency_audit.md`

## Files Updated

- `paper/full_draft/00_title.md`
- `paper/full_draft/01_abstract.md`
- `paper/full_draft/02_introduction.md`
- `paper/full_draft/04_method.md`
- `paper/full_draft/07_discussion.md`
- `paper/full_draft/09_conclusion.md`
- `paper/full_draft/README.md`
- `paper/experiments/task_paper_use_status.md`

## Claim-Boundary Revisions

- Replaced the assertive phrase `manifold-structured domain data` with wording
  based on a `piecewise relevance-manifold assumption`.
- Changed `manifold-aware` to `manifold-inspired` in an alternative title.
- Broadened the conceptual framing from a RAG-only controller to an adaptive
  evidence-selection controller, while keeping the evaluated implementation
  explicitly retrieval-backed and QA-specific.
- Renamed the discussion heading from `What IntentWeight Proves` to
  `Supported Claim`.

## Automated Validation

Run from the repository root:

```bash
.venv/bin/python paper/experiments/scripts/task36_9_validate_full_draft.py
```

The script checks:

- internal task labels in manuscript files;
- `TODO`, `FIXME`, and `TBD` markers;
- overstrong `manifold-structured` wording;
- paired Markdown-compatible LaTeX delimiters;
- duplicate BibTeX keys;
- cited keys missing from `references.bib`.

## Result

The full draft passes the automated consistency audit after the wording
revisions. The remaining work is venue-specific editing: bibliography style,
table conversion, figure styling, and prose compression for the selected
submission template.
