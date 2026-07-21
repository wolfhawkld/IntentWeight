# Journal Submission Checklist

Updated: 2026-07-21 (Task80 reconciliation)

This checklist contains only current submission actions. Historical completion
details are recorded in the Task reports; authoritative counts are generated in
`paper/experiments/task80_authoritative_submission_state.md`.

## Venue Decision

- [x] Primary target selected: IP&M.
- [x] Fallback target identified: ESWA.
- [x] Complete expanded answer-level evaluation before first submission:
  300 queries, 2,100 answers, and three LLM judges.
- [ ] Decide whether to post a preprint before or after journal decision,
  considering double-anonymous review constraints.

## Manuscript Format

- [x] Full draft exists under `paper/full_draft/`.
- [x] Abstract shortened to 250 words or fewer.
- [x] Complete the evidence-preserving main-text compression pass and retain a
  validated 26-page CAS main manuscript.
- [x] Candidate keywords prepared.
- [x] Candidate highlights prepared.
- [x] Convert the manuscript to the current Elsevier CAS single-column format.
- [x] Build a clean CAS `doubleblind` anonymized manuscript file.
- [x] Build a separate one-page title-page file.
- [x] Export all three cited figures as separate vector PDF files.
- [x] Regenerate Figures 2 and 3 at 190 mm with embedded Type 42 fonts and at
  least 7 pt finished lettering.
- [ ] Replace the non-final Figure 1 placeholder with the author-produced
  190 mm vector PDF and pass the strict artwork audit.
- [x] Verify every table is editable LaTeX text, not an image.
- [x] Verify all five main tables, 23 supplementary tables, and three figures
  are cited in their respective documents.

## Double-Anonymized Review

- [x] Remove author names and affiliations from the manuscript body.
- [x] Remove acknowledgements from the anonymized manuscript.
- [x] Check repository links, local paths, and artifact references for identity
  leakage.
- [x] Move acknowledgements, competing-interest text, and corresponding-author
  details to the title page or submission metadata.

## Scientific Positioning

- [x] Keep dense retrieval visible as the quality floor and fallback.
- [x] Keep SentMMR as a shared final-context compressor.
- [x] Keep cross-encoder reranking as a late ranking layer.
- [x] Keep the 400k point marked as diagnostic, not calibration-eligible.
- [x] Keep feedback framed as simulated and ground-truth-derived.
- [x] Keep answer-generation evaluation framed as a formal, automated
  three-judge study rather than human evaluation.
- [x] Include journal-style production implications and deployment boundaries
  in the discussion.
- [x] Add multi-judge answer-level evaluation for the current IP&M route.

## Declarations and Metadata

- [ ] Fill real author order and affiliations.
- [ ] Fill corresponding-author address and email.
- [ ] Confirm funding statement.
- [ ] Confirm competing-interest statement.
- [ ] Confirm data/code availability statement and release link.
- [ ] Confirm generative AI declaration.
- [ ] Confirm any acknowledgements.

## Reproducibility Package

- [x] Experiment scripts and result artifacts are tracked in the repository.
- [x] Local ROCm environment is kept local and should not be submitted as a
  repository artifact.
- [ ] Prepare public artifact release with machine-specific paths removed.
- [x] Re-run manuscript and submission-package validation after CAS migration.
- [x] Rebuild and visually inspect the 26-page main PDF, 13-page supplement,
  and one-page title page.
- [x] Pass 921 experiment-artifact checks with zero warnings and errors.
- [x] Recompute and verify all five main tables and both plotted-data files.
