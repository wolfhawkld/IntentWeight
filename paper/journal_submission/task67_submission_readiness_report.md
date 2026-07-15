# Task67 Submission Readiness Report

Updated: 2026-07-16 (Task74 refresh)

## Status

The repository-controlled submission work through Task74 is complete. The
Task73 recreation/search and writing/search evidence is integrated, and the
IP&M package is scientifically, structurally, and technically validated. Final
author work remains for Figure 1 and submission metadata.

## Package

- anonymous CAS main manuscript: 28 pages, including references;
- double-blind supplementary material: 15 pages and 30 tables;
- separate title page: 1 page;
- abstract: within the 250-word IP&M limit; keywords: 7; highlights: 5;
- main displays: five editable tables and three vector PDF figures.

Moving the complete evidence appendix to a separate supplement reduces the
complete 37-page ACL-style working draft to a 28-page CAS main manuscript
without deleting experimental evidence. The central geometry-guided,
feedback-adaptive route-control thesis and all negative/boundary results remain
present.

## Evidence Validation

- Task51 artifact audit: 921 PASS, 0 WARN, 0 ERROR;
- current Task43 source/display audit: 139/139 PASS;
- Task67 main tables: 5/5 source-derived tables PASS;
- Task67 plotted data: 2/2 files PASS;
- supplementary display provenance: 482 numeric values across 18
  tables PASS;
- Task74 Task73 integration: S30, canonical source files, review packet, ACL
  LaTeX, and CAS package PASS;
- full-draft, LaTeX migration, citation/BibTeX, cross-reference, anonymity,
  and review-packet validation: PASS.

The audit identified and corrected one real presentation drift: the GLM-5.2
correctness mean in Supplementary Table S10 is `4.550` when rounded from the
tracked source value, not `4.551`.

## Artwork

Figures 2 and 3 are deterministic vector plots at 190 x 76 mm, contain no
raster objects or Type 3 fonts, and use 7 pt minimum finished lettering. The
current Figure 1 placeholder also passes the repository's physical-size and
font checks, but it is not the final author-produced architecture artwork.
Replace it according to `paper/full_draft/figures/figure1_author_spec.md`, then
rerun `make audit` from `paper/journal_submission/latex/`.

## Human Submission Fields

These items cannot be finalized from repository evidence alone:

- author order, affiliations, ORCIDs, and corresponding-author contact;
- CRediT roles and acknowledgements;
- funding and competing-interest declarations;
- public data/code archive URLs;
- exact generative-AI disclosure wording and tool-use confirmation;
- preprint timing and final submission-system metadata.
