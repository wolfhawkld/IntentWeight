# Task67 Submission Readiness Report

Updated: 2026-07-05

## Status

The repository-controlled Task67 work and Task68 multi-dataset narrative
alignment are complete. The IP&M package is scientifically and structurally
validated. Final artwork still requires replacement of the non-final Figure 1
placeholder and installation of vector text fonts in the current WSL build
environment.

## Package

- anonymous CAS main manuscript: 25 pages, including references;
- double-blind supplementary material: 13 pages and 28 tables in the current
  WSL font-fallback build;
- separate title page: 1 page;
- abstract: 218 words; keywords: 7; highlights: 5;
- main displays: five editable tables and three vector PDF figures.

Moving the complete evidence appendix to a separate supplement reduces the
review manuscript from 36 to 25 pages without deleting experimental evidence.
The central geometry-guided, feedback-adaptive route-control thesis and all
negative/boundary results remain present.

## Evidence Validation

- Task51 artifact audit: 921 PASS, 0 WARN, 0 ERROR;
- current Task43 source/display audit: 139/139 PASS;
- Task67 main tables: 5/5 source-derived tables PASS;
- Task67 plotted data: 2/2 files PASS;
- remaining supplementary display provenance: 446 numeric values across 17
  tables PASS;
- full-draft, LaTeX migration, citation/BibTeX, cross-reference, anonymity,
  and review-packet validation: PASS.

The audit identified and corrected one real presentation drift: the GLM-5.2
correctness mean in Supplementary Table S10 is `4.550` when rounded from the
tracked source value, not `4.551`.

## Artwork

Figures 2 and 3 are deterministic vector plots at 190 x 76 mm, contain no
raster objects or Type 3 fonts, and use 7 pt minimum finished lettering.

The strict validator currently reports four artwork/font errors:

1. the current WSL main PDF contains Type 3 fonts from Figure 1 and the local
   CMR fallback;
2. the supplementary PDF contains Type 3 fonts from the same missing vector
   text-font environment;
3. Figure 1 contains Type 3 fonts;
4. Figure 1 is 221.62 mm wide instead of 190 mm.

Replace `paper/latex/figures/figure1_system_diagram.pdf` according to
`paper/full_draft/figures/figure1_author_spec.md`, install the CAS-compatible
vector text fonts, then run `make audit` from
`paper/journal_submission/latex/`.

## Human Submission Fields

These items cannot be finalized from repository evidence alone:

- author order, affiliations, ORCIDs, and corresponding-author contact;
- CRediT roles and acknowledgements;
- funding and competing-interest declarations;
- public data/code archive URLs;
- exact generative-AI disclosure wording and tool-use confirmation;
- preprint timing and final submission-system metadata.
