# Task80 Remaining Work Checklist

Status: authoritative open-work list after Task80

Date: 2026-07-21

No additional ordinary dataset, seed, encoder, route, or compressor experiment
is required by default. New experiments should be added only for a concrete
reviewer request or a newly discovered evidence gap.

## Task81: Artwork, Metadata, and Declarations

- [ ] Replace the Figure 1 placeholder with author-produced editable vector
  artwork following `../full_draft/figures/figure1_author_spec.md`.
- [ ] Pass the 190 mm artwork audit: at least 7 pt finished lettering, embedded
  non-Type-3 fonts, no raster objects, clipping, or overlap.
- [ ] Confirm author order, affiliations, ORCIDs, corresponding-author details,
  and CRediT roles in the non-anonymized workflow.
- [ ] Finalize funding, competing interests, acknowledgements, data/code
  availability, and generative-AI disclosure.
- [ ] Keep all identity-bearing fields out of the anonymous manuscript and
  supplement.

## Task82: Reproducibility and Licenses

- [ ] Build a clean release payload from tracked source, scripts, selected
  result artifacts, figure data, environment specifications, and checksums.
- [ ] Exclude credentials, `.env`, `.venv*`, caches, raw restricted data,
  machine-specific state, and absolute local paths.
- [ ] Audit dataset, embedding/compression model, generated-answer, judge-output,
  and redistributed-text licenses.
- [ ] Publish download scripts and pinned source revisions where raw data cannot
  be redistributed.
- [ ] Decide blinded artifact and preprint timing before publishing an
  identity-bearing repository or archive link.
- [ ] Create the immutable archive/DOI only after the payload and anonymity
  strategy are approved.

## Task83: Independent Review and Freeze

- [ ] Obtain independent scientific review and resolve findings in a response
  ledger.
- [ ] Obtain native-level English and final-layout review.
- [ ] Run a cold final build and inspect every main and supplementary page at
  100% zoom.
- [ ] Verify anonymity, PDF metadata, archive links, declarations,
  submission-system fields, and file naming.
- [ ] Freeze checksums, tag the release, and record the exact submitted commit
  and artifact versions.

## Deferred Extensions

More domains, encoders, real-user feedback, hardware profiling, HDBSCAN arms,
new rerankers, and new route algorithms remain follow-up work. They do not block
the current bounded claim or submission package.

A small stratified human correctness, faithfulness, and citation audit is also
deferred. It will be activated only if a reviewer or editor explicitly requires
human evaluation; it is not part of the planned pre-submission work.
