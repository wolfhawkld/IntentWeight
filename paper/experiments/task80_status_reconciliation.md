# Task80 Status Reconciliation

Status: complete

Date: 2026-07-21

## Purpose

This document separates live submission state from historical task records and
generated manuscript mirrors. It prevents stale page counts, judgment counts,
or planned work from being treated as current facts.

## Current Authority

Use these files for current decisions:

- `task80_authoritative_submission_state.md`: generated evidence, validation,
  and compiled-package snapshot;
- `task80_remaining_work_checklist.md`: the sole open-work list;
- `task_paper_use_status.md`: evidence-use and supersession registry;
- `../journal_submission/README.md`: current journal-package entry point;
- `../journal_submission/submission_checklist.md`: current submission checklist.

Scientific prose remains authoritative in `../full_draft/`, while numerical
claims remain authoritative only when traceable to source CSV/JSON artifacts.

## Generated Mirrors

The following files are regenerated and must not be edited directly:

- `../review_packet/manuscript.md` and `supplementary_material.md`;
- `../latex/sections/` and the ACL-style PDF;
- `../journal_submission/latex/sections/` and the CAS PDFs;
- review-packet and LaTeX manifests.

Edit canonical chapters under `../full_draft/`, then run the corresponding
generators and validators.

## Historical Records

Earlier task plans, review-response maps, audits, and readiness reports retain
their original measurements for provenance. They are not silently rewritten
to match later builds. High-risk status documents now carry a historical-record
banner pointing to Task80.

Examples include the Task57 and Task67 response maps, pre-submission audits,
post-Task69 plans, and Task67 readiness report. Their old page or word counts are
correct for their recorded checkpoint, not for the current package.

## Reporting Rules

- Do not use internal `TaskXX` labels in manuscript prose.
- Do not pool heterogeneous dataset/domain rows into one effect estimate.
- Treat geometry as diagnostic support, feedback as controlled simulation, and
  Dense as a strong baseline and fallback.
- Report final evidence-context tokens as the efficiency endpoint; do not call
  them end-to-end serving cost.
- Preserve negative and boundary results, including 400k instability and mixed
  answer-level faithfulness.
