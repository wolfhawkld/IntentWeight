# Task 42: Manuscript Review Alignment

Date: 2026-06-12

## Goal

Align the manuscript with the latest academic-audit feedback before the next
writing pass. The main correction is to make the calibrated context-budget
frontier the headline cost-quality result, while keeping the conservative
confidence-only policy as a stable baseline.

## Completed Changes

- Slimmed the abstract and removed over-specific RAG wording from the headline
  claim.
- Reordered the evidence chain so the frozen calibration/test budget result is
  primary: 6-18% final LLM evidence-context input-token saving while avoiding
  the Hit@10 loss of dense-only adaptive truncation.
- Moved the 4.7-5.3% confidence-only result to a conservative baseline and seed
  stability role.
- Restructured the Results section into six paper-facing sections:
  calibrated token-quality frontier, cross-domain validation, component
  ablation, feedback adaptation and recovery, geometry diagnostics, and
  boundary/robustness checks.
- Clarified that no-feedback gated performance comes from full dense fallback,
  not learned route efficiency.
- Added justification for 32 fixed KMeans routing arms and noted that the
  LoTTE drift fallback is mostly inactive under current thresholds.
- Regenerated Figure 2 as a calibrated token-quality frontier comparing
  IntentWeight budget policies against dense-only adaptive truncation.
- Renamed the LLM generation smoke wording to a downstream answer-quality
  check.
- Synchronized `paper/full_draft`, generated LaTeX sections, LaTeX figures, and
  `paper/latex/main.pdf`.

## Validation

- `.venv/bin/python paper/experiments/scripts/task36_9_validate_full_draft.py`
  passed.
- `make -C paper/latex audit` passed, including PDF compile and PDF audit.
- `git diff --check` passed.

## Paper Claim Boundary

The paper should now claim a bounded quality-cost frontier rather than dense
replacement. The supported main claim is:

> IntentWeight can use route confidence and feedback-updated local routing to
> reduce final LLM evidence-context input tokens under calibrated operating
> points, while preserving query-level usable-evidence retrieval better than
> dense-only adaptive truncation.

Do not claim theorem-level manifold proof, universal superiority over dense
retrieval, real-human-feedback validation, or complete-evidence collection.
