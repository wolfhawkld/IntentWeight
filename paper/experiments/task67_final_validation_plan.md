# Task67 Final Validation and Submission Reduction Plan

Updated: 2026-07-05

## Objective

Produce a shorter IP&M first-submission manuscript without weakening the
IntentRoute thesis, dropping experiment evidence, or hiding boundary and
negative results. Task67 is a presentation, traceability, and final-validation
task. It must not silently change metrics, experiment outputs, claim scope, or
the method definition.

## Non-Negotiable Guardrails

1. Preserve the complete experiment evidence chain. Consolidation may remove
   repetition from the main narrative, but every paper-facing number must
   remain traceable to a tracked result artifact.
2. Preserve the central thesis: manifold-inspired local relevance structure,
   geometry-guided route construction, feedback-adaptive LinUCB confidence,
   dense/BM25 rescue, and separately calibrated final-context budgeting.
3. Keep defensive boundaries explicit without replacing the thesis with a
   weaker dense-budget-only account.
4. Stop for user review before any major section restructure, evidence move,
   figure redesign, or change to the five-table/three-figure main display set.
5. Do not lower experiment or publication standards to simplify validation.

## Current Baseline

The current `cas-sc` double-blind package compiles and passes the Task66
validator after restoring the declared TinyTeX packages.

- anonymous manuscript: 36 pages;
- main text reaches page 24 and references continue through page 25;
- embedded appendix tables occupy pages 26-36;
- main displays: five editable tables and three vector PDF figures;
- appendix displays: 28 editable tables in 12 appendix sections;
- review-packet manuscript count: 16,255 words;
- Task51 audit: 763/763 checks pass, but its manifest currently stops at
  Task62 and therefore is not a complete Task67 audit.

The page count is driven primarily by the embedded evidence appendix. The main
text itself is not 36 pages long.

## Approved Submission Structure

Approved by the author on 2026-07-05:

1. Keep the anonymous main manuscript at approximately 22-24 CAS pages,
   including references.
2. Keep the existing five main tables and three main figures unless a later
   evidence audit finds a direct traceability problem.
3. Move the complete 12-section appendix into a separately submitted,
   double-blind supplementary-material PDF.
4. Preserve all 28 appendix tables in the supplement; consolidate only
   duplicated framing prose and table introductions.
5. Replace main-text appendix references with stable supplementary section and
   table references, and validate every reference in both PDFs.

This is a packaging change, not evidence deletion. The rejected fallback was to
keep the calibration and multi-judge appendices embedded, which would likely
leave a roughly 28-30 page main manuscript.

## Main-Text Consolidation Candidate Areas

These are candidates for paragraph-level consolidation, not thesis removal:

- Introduction: retain the full thesis and five contributions, but remove
  repeated explanations of dense rescue, cost-layer separation, and bounded
  claims when the same point is immediately restated later.
- Method: retain all controller components and equations; combine short
  implementation/rationale subsections where their boundaries add headings but
  not technical content.
- Experimental Setup: keep metric definitions and protocols in the main text;
  move exhaustive metric implementation detail to the supplement only when the
  main definition remains independently reproducible.
- Discussion and Limitations: keep all adverse findings and claim boundaries;
  merge duplicate caveats so each boundary is explained once in depth rather
  than repeatedly in both sections.

No candidate consolidation will be applied until the submission-structure
decision is approved.

## Figure Audit

Current figure files are vector PDFs, but they do not yet meet the desired
final-artwork standard:

| Figure | Current PDF width | Current issue |
| --- | ---: | --- |
| System diagram | 221.62 mm | Oversized source; Type 3 fonts; subtitle overlaps the dense-route box; crowded connectors. |
| Token-quality frontier | 256.14 mm | Oversized source; Type 3 fonts; final lettering depends on LaTeX downscaling. |
| Geometry-to-control | 256.45 mm | Oversized source; Type 3 fonts; final lettering depends on LaTeX downscaling. |

Elsevier's general artwork targets are 90 mm single-column, 140 mm 1.5-column,
and 190 mm full-width, with normal lettering at approximately 7 pt at final
printed size. Fonts should be embedded and use a standard family where
possible.

The existing Matplotlib generator can be corrected without rasterization:

- generate at an exact 190 mm physical width;
- remove `bbox_inches="tight"` physical-size drift;
- use embedded TrueType/Type 42 fonts instead of Type 3;
- enforce at least 7 pt normal text at final size;
- add automated width, font, and clipping checks;
- retain editable CSV data and deterministic generation.

The system diagram needs a layout redesign while preserving the same method
semantics. The author will create the final Figure 1 manually. The current
Figure 1 remains a non-final structural placeholder; Task67 may document its
required content and audit the author-supplied vector file, but must not replace
it with generative-AI-created artwork. The data figures need specification
repair rather than conceptual redesign.

The compiled manuscript also contains Type 3 fonts outside the figures because
the local CAS build falls back to bitmap EC fonts when STIX/Charis is absent.
Task67 must restore the CAS font dependencies (or an equivalent embedded
publication font configuration) and reject Type 3 fonts across the complete
main and supplementary PDFs, not only in separately uploaded figure files.

## Tooling and Quality Boundaries

The current code workflow can produce deterministic publication-grade vector
plots and a clean technical architecture diagram. It should not use generative
image tools for manuscript figures: Elsevier's current policy prohibits
generative-AI-created or altered submission artwork unless it is itself part of
the research method.

A designer-style graphical abstract is not currently part of the validated
submission package. If IP&M's submission system later requires one, it will be
an author-created manual vector-design task; it must not be silently generated
as raster or generative-AI artwork.

## Required Task67 Validation Expansion

1. Extend the experiment manifest/audit through Task63 and Task65.1-65.7.
2. Add a claim-to-artifact ledger for every main-text quantitative statement.
3. Validate that main and supplementary tables agree with their source CSV/JSON
   artifacts.
4. Validate figure physical dimensions, font embedding/type, minimum finished
   lettering, data-source hashes, and rendered clipping.
5. Reject Type 3 fonts and validate font embedding across the complete main
   manuscript and supplement.
6. Compile and visually inspect the main manuscript and supplement separately.
7. Re-run manuscript consistency, citation/BibTeX, anonymity, cross-reference,
   and review-packet validation.
8. Produce a final response-to-review map and submission-readiness report.

## Completed Approval Gate

Confirmed on 2026-07-05:

1. all 12 appendix sections will move to a separate supplement; and
2. Figure 1 will be author-created. Task67 will provide specifications and
   validate dimensions, font embedding, text size, semantics, and clipping.

## Execution Status

Completed on 2026-07-05:

- separated the 24-page main manuscript from the 12-page supplement;
- preserved all five main tables, three figures, and 28 supplementary tables;
- expanded the artifact audit through Task65.7: 921 checks, zero warnings and
  zero errors;
- updated the Task43 display audit for the current manuscript: 139/139 checks;
- added source-derived validation for all five main tables, both data-figure
  CSVs, and 446 numeric values across the remaining 17 supplementary tables;
- regenerated Figures 2 and 3 at 190 x 76 mm with embedded Type 42 fonts and
  7 pt minimum lettering;
- restored embedded publication fonts in the CAS manuscript and supplement;
- split the review packet into main-manuscript and supplementary files;
- documented the author-owned Figure 1 production and acceptance requirements.

The strict submission validator intentionally remains red only for the current
Figure 1 placeholder: it is 221.62 mm wide and contains Type 3 fonts, which also
propagate into the compiled main PDF. Replacing it with the specified 190 mm
author vector PDF should clear all three remaining technical errors.
