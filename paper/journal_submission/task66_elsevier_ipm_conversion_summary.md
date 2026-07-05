# Task66 Elsevier/IP&M Conversion Summary

Updated: 2026-07-01

## Objective

Convert the stabilized venue-neutral IntentRoute manuscript into a
self-contained, technically validated journal-submission package, with
Information Processing & Management as the primary target.

## Format Decision

The current IP&M Guide for Authors links to Elsevier's CAS single-column LaTeX
template. Task66 therefore uses `cas-sc` rather than the older project plan for
`elsarticle`.

IP&M uses double-anonymized review. The package separates:

- `latex/anonymous_manuscript.tex`: CAS `doubleblind` manuscript;
- `latex/title_page.tex`: non-anonymous title-page template containing the
  author-controlled declarations and placeholders.

## Completed Work

- shortened the current abstract to 240 words while retaining the main claim,
  multi-scale result, multi-judge result, and BGE faithfulness boundary;
- created a reproducible builder that synchronizes canonical LaTeX sections,
  the three cited vector figures, bibliography, highlights, and keywords;
- converted wide ACL `table*` environments to CAS single-column editable
  tables and translated float positions to CAS `pos=` syntax;
- added a source SHA-256 manifest and drift checks for the inline CAS abstract;
- added explicit cross-references for all 33 tables and three figures;
- created a one-page title-page template with author, affiliation,
  corresponding-author, acknowledgement, funding, competing-interest, CRediT,
  data/code, and AI-use fields;
- added an automated audit target covering format, anonymity, abstract length,
  keywords, highlights, manifest hashes, cross-references, PDF generation, and
  compile warnings.

## Generated Artifacts

- `paper/journal_submission/latex/anonymous_manuscript.tex` and compiled PDF;
- `paper/journal_submission/latex/title_page.tex` and compiled one-page PDF;
- synchronized manuscript sections, bibliography, and three cited vector
  figures;
- `highlights.txt`, `keywords.txt`, and `source_manifest.json`;
- reproducible `Makefile` targets for synchronization, compilation,
  validation, and full audit.

## Validation Result

- anonymous manuscript: 36 pages;
- title page: 1 page;
- abstract: 240 words;
- keywords: 7;
- highlights: 5, each within 85 characters;
- display cross-references: 36/36 resolved;
- cited manuscript figures: 3 vector PDFs;
- visible clipping, overlap, or abnormal float placement: none in the full
  contact-sheet review;
- automated submission validation: passed.

CAS 2.4 emits one fixed internal `117.0831pt` overfull notice while constructing
the empty-author double-blind frontmatter box. The first page was inspected at
full resolution and has no visible overflow. The validator allows only that
exact template-internal notice and still fails on any other overfull box or
LaTeX/package warning.

The CAS bibliography style also reports empty page ranges for the ICLR
Self-RAG paper and the official NeurIPS record for the human-preference paper.
Their source proceedings metadata do not provide conventional page ranges.
The validator allows only these two entry-specific notices and fails on any
other BibTeX warning or error.

Task67 subsequently separated the 12-section evidence appendix into a
12-page supplementary-material PDF. The main manuscript is now 24 CAS pages,
including references. Task67 also regenerated Figures 2 and 3 at a final
190 x 76 mm vector size with embedded Type 42 fonts. Figure 1 remains an
explicitly non-final author-owned placeholder.

## Claim Boundary

Task66 changes submission format and traceability, not experimental claims. The
paper continues to support the bounded chain:

`local geometric structure -> adaptive route selection -> feedback correction -> quality-efficiency trade-off`

It does not claim universal superiority over dense retrieval, strict
answer-level non-inferiority, uniform faithfulness preservation, production
RLHF validation, or complete evidence collection from query-level Hit@10.

## Remaining Human Submission Fields

Before formal submission, the authors must provide and approve:

- author order, affiliations, ORCIDs, and corresponding-author contact;
- CRediT roles and acknowledgements;
- funding and competing-interest declarations;
- final public data/code archive URLs;
- final generative-AI disclosure wording;
- preprint timing and final submission-system metadata.
