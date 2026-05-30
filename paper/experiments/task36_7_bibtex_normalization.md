# Task36.7 BibTeX Normalization

Updated: 2026-05-31

## Purpose

This task converts the reference seed list into a provisional BibTeX file for
the full draft. It does not add new experiments or new claims. Its purpose is
to make the Markdown draft easier to migrate into a LaTeX venue template.

## Files Added

- `paper/full_draft/references.bib`

## Files Updated

- `paper/full_draft/10_reference_seed.md`
- `paper/full_draft/README.md`
- `paper/experiments/task_paper_use_status.md`

## Coverage

The generated bibliography includes the citation keys currently used by the
related-work section:

- retrieval-augmented generation and dense retrieval;
- BM25, BEIR, and reciprocal-rank fusion;
- LinUCB and contextual-bandit foundations;
- manifold-learning diagnostics and structured retrieval;
- implicit feedback, preference learning, and RLHF-style optimization.

## Validation

The related-work citation keys are checked against `references.bib`. At the
time of this task, all cited keys in `paper/full_draft/03_related_work.md` have
matching BibTeX entries.

## Remaining Work

The file is venue-ready enough for drafting, but not camera-ready. Before
submission, verify author metadata, capitalization, venue names, and DOI fields
against the target bibliography style.
