# Journal Submission Checklist

Updated: 2026-06-21

## Venue Decision

- [x] Primary target selected: IP&M.
- [x] Fallback target identified: ESWA.
- [ ] Decide whether to add a larger answer-level evaluation before first
  submission.
- [ ] Decide whether to post a preprint before or after journal decision,
  considering double-anonymous review constraints.

## Manuscript Format

- [x] Full draft exists under `paper/full_draft/`.
- [x] Abstract shortened to 250 words or fewer.
- [x] Candidate keywords prepared.
- [x] Candidate highlights prepared.
- [ ] Convert ACL-style LaTeX to Elsevier `elsarticle`.
- [ ] Build a clean anonymized manuscript file.
- [ ] Build a separate title page file.
- [ ] Export separate figure files with journal-friendly names.
- [ ] Verify every table is editable text, not an image.
- [ ] Verify every figure and table is cited in the manuscript.

## Double-Anonymized Review

- [ ] Remove author names and affiliations from the manuscript body.
- [ ] Remove acknowledgements from the anonymized manuscript.
- [ ] Check repository links, local paths, and artifact references for identity
  leakage.
- [ ] Move acknowledgements, competing-interest text, and corresponding-author
  details to the title page or submission metadata.

## Scientific Positioning

- [x] Keep dense retrieval visible as the quality floor and fallback.
- [x] Keep SentMMR as a shared final-context compressor.
- [x] Keep cross-encoder reranking as a late ranking layer.
- [x] Keep the 400k point marked as diagnostic, not calibration-eligible.
- [x] Keep feedback framed as simulated and ground-truth-derived.
- [x] Keep answer-generation evaluation framed as a smoke test.
- [ ] Strengthen journal-style practical implications in the discussion.
- [ ] Consider adding more answer-level evaluation if targeting TOIS.

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
- [ ] Re-run manuscript validation after Elsevier migration.
- [ ] Rebuild and inspect final PDF before submission.
