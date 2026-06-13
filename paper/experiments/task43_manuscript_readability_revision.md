# Task 43: Manuscript Readability and Structure Revision

Date: 2026-06-13

## Goal

Address manuscript-level readability feedback after the first full read of the
draft PDF. This task does not add new experiments. It improves paper-facing
structure, figure semantics, dataset-role presentation, and appendix layout.

## Completed Changes

- Strengthened the abstract's cost wording from generic context saving to the
  LLM input tokens consumed by retrieved evidence context.
- Simplified the Introduction boundary paragraph and reordered contributions so
  the piecewise relevance-manifold hypothesis and geometry diagnostics appear
  before the optimization result.
- Replaced the Experimental Setup dataset-role table with compact role bullets.
  This avoids making dataset guardrails the first main table.
- Renumbered main Results tables so the calibrated token-quality frontier is
  Table 1.
- Updated Figure 1 in both SVG and LaTeX/PDF generation paths:
  dense and BM25 are shown as global recall routes, while LinUCB selects
  cluster-local arms and supplies route confidence for final context-budget
  control.
- Updated the Figure 1 caption and table/figure placement plan to match the
  actual experimental design.
- Converted the wide secondary-dataset appendix table into prose bullets while
  preserving all key numbers. The structured eManual diagnostic remains as
  Appendix Table D1.
- Reworked the final recovery-generalization table as a full-width appendix
  table and adjusted float-page placement so the final-page table starts at the
  top with normal appendix table sizing.
- Kept appendix tables under normal two-column LaTeX float semantics after a
  layout audit: wide appendix tables are emitted as cross-column `table*`
  floats, while narrower tables remain single-column `table` floats. We avoid
  forced appendix section page breaks because they create sparse pages in the
  ACL two-column template.
- Tuned LaTeX float parameters in `paper/latex/main.tex` to allow more
  cross-column appendix floats to appear on text pages instead of being pushed
  into a long terminal float block.
- Installed TinyTeX `sttools` and used its `stfloats` package for safer
  two-column wide-table placement. A `cuted/strip` attempt placed wide appendix
  tables closer to their source positions, but it caused overlapping text under
  the ACL review template, so it was reverted. The retained layout uses standard
  `table*` for wide appendix tables and ordinary single-column `table` for
  narrow appendix tables.
- Switched the local reading build from ACL `review` mode to `preprint` mode to
  remove line numbers while retaining page numbers. Restore
  `\usepackage[review]{acl}` before formal anonymous review submission if the
  target venue requires ACL review formatting.

## Validation

- `.venv/bin/python paper/experiments/scripts/task36_9_validate_full_draft.py`
  passed.
- `make -C paper/latex audit` passed, including LaTeX migration, figure
  generation, PDF compile, and PDF audit.
- `git diff --check` passed.

## Remaining Manual Review

The generated Figure 1 now reflects the correct method semantics. It should
still be visually reviewed in the PDF for arrow density and spacing before a
camera-ready pass.
