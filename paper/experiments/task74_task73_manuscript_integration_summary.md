# Task74 Task73 Manuscript Integration Summary

Status: completed 2026-07-16

## What Changed

Task74 integrates the preregistered Task73 recreation/search and writing/search
100k results into the canonical manuscript and generated review/submission
packages. It changes no experiment, ranking, budget selection, or method
implementation.

- The manuscript scope is now nine dataset settings across eight domain areas.
- Experimental Setup records the matched 100k protocol and non-pooling rule.
- Results, Discussion, Limitations, and Conclusion report both the writing
  useful frontier and the recreation strict-NI boundary.
- Supplementary Table S30 reports source-derived lexical, dense, full-route,
  geometry, calibration, saving, and seed-level NI values.
- The protocol registry and paper-use ledger now include Task73.

## Preserved Claim Boundary

- Writing/no-feedback: `+0.12pp` mean Hit@10 change, `10.09%` saving, `2/3`
  strict NI seeds.
- Recreation/no-feedback: `-0.76pp`, `5.42%`, `0/3` strict NI seeds.
- Trust-weighted calibration: Dense fallback in all folds in both domains.
- Nearest-cluster Hit@3: `0.8366` and `0.8655`, supporting route signal but not
  a direct geometry-to-compression guarantee.
- The preregistered lexicality ordering was reversed and is not used as a
  post-hoc explanation.
- Post-failure retry remains same-query simulated-feedback evidence, not
  first-pass unseen-query generalization.

## Validation

- Task73 source audit: 104/104 PASS.
- Task74 source-derived integration audit: PASS.
- Task51 experiment artifacts: 921 PASS.
- Task43 table/figure checks: 139/139 PASS.
- Task67 five main tables, two plotted-data files, and 482 supplementary values
  across 18 source-checked tables: PASS.
- Full-draft, review-packet, ACL LaTeX, evidence, cross-reference, and IP&M
  journal validators: PASS.
- ACL working PDF: 37 pages, zero critical LaTeX warnings.
- CAS package: 28-page anonymous manuscript, 15-page supplement, one-page
  title page; abstract within the 250-word limit.
- Visual inspection: CAS abstract and Supplementary Table S30 are readable and
  unclipped.

## Remaining Author-Owned Items

The repository-controlled Task74 gate is closed. Formal submission still needs
the final author-produced Figure 1, author/affiliation and CRediT metadata,
funding/conflict/acknowledgement fields, public data/code URLs, the final AI-use
disclosure, and preprint/submission-system decisions.
